"""Survey estimates and contrasts: full strata/PSUs, domains and shared replicates."""
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import t


def interval(point, se, df, **extra):
    margin = t.ppf(.975, df) * se
    return dict(estimacion=float(point), error_estandar=float(se),
                ic95_inferior=float(point-margin), ic95_superior=float(point+margin),
                gl_diseno=float(df), **extra)


class Design:
    def __init__(self, frame, weight, strata, psu, *, replicates=999, seed=20261025):
        self.w = frame[weight].to_numpy(dtype=float)
        keys = frame[[strata, psu]].astype(str)
        if keys.isin(['', 'nan', '<NA>', 'None']).any().any():
            raise ValueError('Missing survey design identifiers')
        units = frame.attrs.get('design_units', list(keys.itertuples(index=False, name=None)))
        units = pd.MultiIndex.from_tuples(sorted(set(units)))
        self.ids = units.get_indexer(pd.MultiIndex.from_frame(keys))
        if (self.ids < 0).any() or not (np.isfinite(self.w) & (self.w > 0)).all():
            raise ValueError('Invalid survey weights or PSU inventory')
        self.strata_ids, strata_names = pd.factorize(units.get_level_values(0), sort=True)
        self.sizes = np.bincount(self.strata_ids)
        if (self.sizes < 2).any():
            raise ValueError('Singleton stratum requires an explicit design decision')
        self.nunits = len(units)
        self.df = self.nunits-len(strata_names)
        self.replicates, self.seed = replicates, seed
        self._multipliers = None

    def linear(self, point, influence, valid):
        totals = np.bincount(self.ids, weights=influence, minlength=self.nunits)
        means = np.bincount(self.strata_ids, weights=totals)/self.sizes
        centered = (totals-means[self.strata_ids])*np.sqrt(self.sizes[self.strata_ids]/(self.sizes[self.strata_ids]-1))
        return interval(point, np.linalg.norm(centered), self.df,
                        n=int(valid.sum()), hogares_expandidos=float(self.w[valid].sum()),
                        metodo='Taylor_UPM', _linear=centered)

    def ratio(self, numerator, denominator, domain=None):
        a = np.asarray(numerator, dtype=float)
        b = np.broadcast_to(np.asarray(denominator, dtype=float), a.shape)
        valid = np.isfinite(a) & np.isfinite(b)
        if domain is not None:
            valid &= np.asarray(domain, dtype=bool)
        den = np.dot(self.w[valid], b[valid])
        if not valid.any() or den <= 0:
            raise ValueError('Empty estimate domain or nonpositive denominator')
        point = np.dot(self.w[valid], a[valid])/den
        influence = np.zeros(len(self.w))
        influence[valid] = self.w[valid]*(a[valid]-point*b[valid])/den
        return self.linear(point, influence, valid)

    def mean(self, values, domain=None):
        values = pd.Series(values).to_numpy(dtype=float, na_value=np.nan)
        return self.ratio(values, 1., domain)

    def multipliers(self):
        if self._multipliers is None:
            rng = np.random.default_rng(self.seed)
            self._multipliers = np.concatenate([
                rng.multinomial(int(m-1), np.full(m, 1/m), size=self.replicates)*m/(m-1)
                for m in self.sizes], axis=1).astype(np.float32)
        return self._multipliers

    def distribution(self, values, domain=None, *, concentration=False, curve=False):
        values = pd.Series(values).to_numpy(dtype=float, na_value=np.nan)
        valid = np.isfinite(values)
        if domain is not None:
            valid &= np.asarray(domain, dtype=bool)
        pos = np.flatnonzero(valid)
        pos = pos[np.argsort(values[pos], kind='stable')]
        v, w, ids = values[pos], self.w[pos], self.ids[pos]
        if not len(pos):
            raise ValueError('Empty distribution domain')
        if concentration and ((v < 0).any() or np.dot(v,w) <= 0):
            raise ValueError('Concentration requires nonnegative values and a positive total')
        grid = np.linspace(0, 1, 101)

        def calculate(weights):
            keep = weights > 0
            vv, ww = v[keep], weights[keep]
            cw = np.cumsum(ww)
            if not len(cw):
                raise ValueError('Empty domain in a bootstrap replicate')
            if not concentration:
                return np.array([vv[min(np.searchsorted(cw, .5*cw[-1]),len(vv)-1)]])
            cv = np.cumsum(vv*ww)
            x, y = np.r_[0,cw/cw[-1]], np.r_[0,cv/cv[-1]]
            stats = [1-2*np.trapezoid(y,x),1-np.interp(.9,x,y),1-np.interp(.8,x,y)]
            return np.r_[stats,np.interp(grid,x,y)] if curve else np.array(stats)

        point = calculate(w)
        draws = np.array([calculate(w*mult[ids]) for mult in self.multipliers()])
        names = ['gini','top10','top20'] if concentration else ['mediana']
        if curve:
            names += [f'lorenz_{i}' for i in range(101)]
        df = min(self.df, self.replicates-1)
        return {name:interval(point[j],draws[:,j].std(ddof=1),df,
                             n=len(pos),hogares_expandidos=float(w.sum()),
                             metodo='bootstrap_UPM',bootstrap_replicas=self.replicates,
                             _replicates=draws[:,j]) for j,name in enumerate(names)}


def public(estimate):
    return {k:v for k,v in estimate.items() if not k.startswith('_')}


def difference(a, b, *, independent=False):
    point = a['estimacion']-b['estimacion']
    if independent:
        se = np.hypot(a['error_estandar'], b['error_estandar'])
    elif '_linear' in a and '_linear' in b:
        se = np.linalg.norm(a['_linear']-b['_linear'])
    elif '_replicates' in a and '_replicates' in b:
        se = np.std(a['_replicates']-b['_replicates'],ddof=1)
    else:
        raise ValueError('Paired differences require shared linearization or replicates')
    df = min(a['gl_diseno'], b['gl_diseno'])
    p = 2*t.sf(abs(point/se),df) if se > 0 else (1. if point == 0 else 0.)
    return interval(point,se,df,p_valor=float(p),
                    n_a=a.get('n'),n_b=b.get('n'),
                    metodo='olas_independientes' if independent else a['metodo'])


def adjust_holm(table):
    """Holm family-wise adjustment; families are explicit, never chosen by significance."""
    table = table.copy()
    table['p_ajustada_holm'] = np.nan
    table['comparaciones_familia'] = 0
    for _, ids in table.groupby('familia',sort=False).groups.items():
        p = table.loc[ids,'p_valor'].to_numpy(float)
        if not np.isfinite(p).all():
            raise ValueError('Nonfinite p-value in a comparison family')
        order = np.argsort(p,kind='stable')
        adjusted = np.minimum(1,np.maximum.accumulate(p[order]*np.arange(len(p),0,-1)))
        table.loc[np.asarray(list(ids))[order],'p_ajustada_holm'] = adjusted
        table.loc[ids,'comparaciones_familia'] = len(p)
    table['significativa_holm_005'] = table.p_ajustada_holm.lt(.05)
    table['decision'] = np.where(table.significativa_holm_005,'Diferencia detectada','Evidencia insuficiente')
    return table


def pairs(estimates, *, family, **context):
    return [{**context,'familia':family,'categoria_a':a,'categoria_b':b,
             **difference(estimates[a],estimates[b])} for a,b in combinations(estimates,2)]
