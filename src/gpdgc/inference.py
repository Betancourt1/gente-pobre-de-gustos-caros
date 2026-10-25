"""Uncertainty and all age-pair comparisons for the original ENIGH/ENSAFI outputs."""
import numpy as np
import pandas as pd

from . import config
from .survey import Design, public, pairs, adjust_holm


def scaled_rows(rows, scale):
    for row in rows:
        for key in ['estimacion','error_estandar','ic95_inferior','ic95_superior']:
            row[key] *= scale
        row['unidad'] = 'p.p.' if scale == 100 else ('índice' if row.get('indicador','').startswith('gini') else 'MXN')
    return rows


def original(tables, enigh, ensafi, viv, *, replicates=999):
    designs = {
        'ENIGH': Design(enigh,'factor','est_dis','upm',replicates=replicates),
        'ENSAFI': Design(ensafi,'FAC_ELE','EST_DIS','UPM_DIS',replicates=replicates,seed=20261026),
    }
    contrasts, precision = [], []
    assets = ensafi.merge(viv,on='LLAVEVIV',how='left',validate='many_to_one')
    assert assets.LLAVEMOD.tolist() == ensafi.LLAVEMOD.tolist()

    def add(table_name, source, metrics, *, deciles=False):
        table = tables[table_name]
        columns = [metric+"_"+field for metric in metrics for field in ["error_estandar","ic95_inferior","ic95_superior","gl_diseno","n"]]
        table = pd.concat([table,pd.DataFrame(np.nan,index=table.index,columns=columns)],axis=1)
        tables[table_name] = table
        frame = enigh if source == 'ENIGH' else ensafi
        design = designs[source]
        for metric, (values, kind, scale) in metrics.items():
            for decile in (range(1,11) if deciles else [None]):
                estimates = {}
                for age in config.AGE_LABELS:
                    domain = frame.grupo_edad.astype('string').eq(age).to_numpy(bool)
                    rowmask = table.grupo_edad.eq(age)
                    if decile is not None:
                        domain &= frame.decil_ing.eq(decile).fillna(False).to_numpy(bool)
                        rowmask &= table.decil_ing.eq(decile)
                    estimate = (design.distribution(values,domain)['mediana'] if kind=='median'
                                else design.mean(values,domain))
                    idx = table.index[rowmask]
                    assert len(idx)==1
                    old = table.loc[idx[0],metric]
                    assert np.isclose(old,estimate['estimacion'],atol=1e-10,equal_nan=True),(table_name,metric,age,old,estimate['estimacion'])
                    estimates[age] = estimate
                    for field in ['error_estandar','ic95_inferior','ic95_superior','gl_diseno','n']:
                        table.loc[idx,metric+'_'+field] = estimate[field]
                    details=public(estimate)
                    details["poblacion_expandida"]=details.pop("hogares_expandidos")
                    precision.append(dict(tabla=table_name,fuente=source,indicador=metric,grupo_edad=age,
                                          decil_ingreso=decile,**details))
                family = f'{source}|{table_name}|{metric}'
                contrasts.extend(scaled_rows(pairs(estimates,family=family,fuente=source,
                    anio=2024 if source=='ENIGH' else 2023,indicador=metric,tabla=table_name,
                    decil_ingreso=decile,tipo='edad'),scale))

        if 'peso_pct' in table:
            for age in config.AGE_LABELS:
                est=design.mean(frame.grupo_edad.astype('string').eq(age),frame.grupo_edad.notna())
                idx=table.index[table.grupo_edad.eq(age)]
                for field in ['error_estandar','ic95_inferior','ic95_superior']:
                    table.loc[idx,'peso_pct_'+field]=100*est[field]

    profile = {key:(enigh[key], 'mean',100) for key in tables['h1_perfil_hogares.csv'] if key.startswith('share_') and not key.startswith('share_d2_')}
    for key in ['alcohol','restaurantes','recreacion','personal','streaming','auto']:
        profile['share_d2_'+key] = (enigh['gasto_d2_'+key]/enigh.gasto_total_g1.where(enigh.gasto_total_g1.gt(0)),'mean',100)
    profile.update({
        'ing_eq_medio':(enigh.ing_eq,'mean',1),'ing_eq_mediano':(enigh.ing_eq,'median',1),
        'gasto_eq_medio':(enigh.gasto_eq,'mean',1),'gasto_eq_mediano':(enigh.gasto_eq,'median',1),
        'gasto_d2_eq':(enigh.gasto_d2_eq,'mean',1)})
    add('h1_perfil_hogares.csv','ENIGH',profile)
    for name,metric in [('h2_share_d2_por_decil.csv','share_d2'),('h2_nivel_d2_por_decil.csv','gasto_d2_eq')]:
        add(name,'ENIGH',{metric:(enigh[metric],'mean',100 if metric.startswith('share') else 1)},deciles=True)
    add('h2_sensibilidad_canastas_por_decil.csv','ENIGH',{
        key:(enigh[key],'mean',100) for key in ['share_d1','share_d2','share_d3']},deciles=True)
    add('h4_vivienda_por_edad.csv','ENIGH',{
        'pct_rentados':(enigh.es_rentado,'mean',100),
        'carga_renta_mediana':(enigh.carga_renta,'median',100),
        'share_vivienda':(enigh.share_vivienda,'mean',100)})
    financial={
        'pct_afore':'tiene_afore','pct_reporta_ahorro_cuentas':'reporta_ahorro_cuentas',
        'pct_deuda_credito':'tiene_deuda_credito','pct_reporta_atraso':'reporta_atraso_pago',
        'pct_ingreso_insuficiente':'ingreso_insuficiente','pct_alto_estres':'alto_estres',
        'pct_gasto_supera_ingreso_laboral':'gasto_supera_ingreso_laboral',
        'pct_comparables_ingreso_gasto':'comparable_ingreso_gasto'}
    metrics={name:(ensafi[col],'mean',100) for name,col in financial.items()}
    metrics.update({name:(ensafi[col],'median',1) for name,col in {
        'ingreso_laboral_mensual_mediano':'ingreso_laboral_mensual','gasto_mensual_mediano':'gasto_mensual'}.items()})
    add('h3_finanzas_ensafi.csv','ENSAFI',metrics)
    from .analysis import _EXPECT_COLS
    metrics={name:(ensafi[col].eq(1),'mean',100) for col,name in _EXPECT_COLS.items()}
    metrics['Meta: vivienda']=(ensafi.P9_1.isin([1,2]),'mean',100)
    add('h4_expectativas_ensafi.csv','ENSAFI',metrics)
    add('h1b_bienes_ensafi.csv','ENSAFI',{
        name:(assets[col],'mean',100) for name,col in {
            'Auto':'tiene_auto','Celular':'tiene_celular','Internet':'tiene_internet',
            'TV de paga':'tiene_tv_paga','Streaming':'tiene_streaming'}.items()})

    design=designs['ENIGH']
    national=design.distribution(enigh.gasto_d2,concentration=True,curve=True)
    wide=design.distribution(enigh.gasto_d1,concentration=True)
    table=tables['h5_concentracion_nacional.csv']
    for idx,row in table.iterrows():
        metric,basket=row.indicador.rsplit('_',1)
        est=(national if basket=='d2' else wide)[metric]
        assert np.isclose(row.valor,est['estimacion'],atol=1e-10)
        for key,value in public(est).items():
            if key!='estimacion':table.loc[idx,key]=value
    # A fixed probability grid makes pointwise Lorenz bands reproducible and readable.
    curve=pd.DataFrame([dict(proporcion_acumulada_hogares=i/100,
        proporcion_acumulada_gasto_d2=national[f'lorenz_{i}']['estimacion'],
        **{k:v for k,v in public(national[f'lorenz_{i}']).items() if k!='estimacion'}) for i in range(101)])
    tables['h5_curva_lorenz_d2.csv']=curve
    by_age=tables['h5_concentracion_por_edad.csv']
    stats={name:{} for name in ['gini_d2','top10_d2','top20_d2','share_gasto_d2_total']}
    for age in config.AGE_LABELS:
        domain=enigh.grupo_edad.astype('string').eq(age).to_numpy(bool)
        dist=design.distribution(enigh.gasto_d2,domain,concentration=True)
        estimates={key+'_d2':dist[key] for key in ['gini','top10','top20']}
        estimates['share_gasto_d2_total']=design.ratio(enigh.gasto_d2*domain,enigh.gasto_d2)
        idx=by_age.index[by_age.grupo_edad.eq(age)][0]
        for metric,est in estimates.items():
            if metric in by_age and pd.notna(by_age.loc[idx,metric]):
                assert np.isclose(by_age.loc[idx,metric],est['estimacion'],atol=1e-10)
            by_age.loc[idx,metric]=est['estimacion']
            for key in ['error_estandar','ic95_inferior','ic95_superior','gl_diseno']:
                by_age.loc[idx,metric+'_'+key]=est[key]
            stats[metric][age]=est
    for metric,estimates in stats.items():
        contrasts.extend(scaled_rows(pairs(estimates,family='ENIGH|H5|'+metric,
            fuente='ENIGH',anio=2024,indicador=metric,tabla='h5_concentracion_por_edad.csv',tipo='edad'),
            1 if metric=='gini_d2' else 100))
    contrasts=adjust_holm(pd.DataFrame(contrasts))
    tables['contrastes_categorias.csv']=contrasts
    tables['precision_original.csv']=pd.DataFrame(precision)
    # Every headline value gets its corresponding uncertainty, including the D2 difference.
    findings=tables['hallazgos_clave.csv']
    lookup=[('h1_perfil_hogares.csv','share_d2','18-29'),('h1_perfil_hogares.csv','share_d2','60+'),None,
        ('h1_perfil_hogares.csv','share_d1','18-29'),('h1_perfil_hogares.csv','share_d1','60+'),
        ('h3_finanzas_ensafi.csv','pct_afore','18-29'),('h3_finanzas_ensafi.csv','pct_afore','60+'),
        ('h3_finanzas_ensafi.csv','pct_deuda_credito','18-29'),('h3_finanzas_ensafi.csv','pct_alto_estres','18-29'),
        ('h4_expectativas_ensafi.csv','Pensión, jubilación o AFORE','18-29'),
        ('h4_expectativas_ensafi.csv','Pensión, jubilación o AFORE','60+'),
        ('h4_expectativas_ensafi.csv','Apoyo de gobierno','18-29')]
    for idx,item in enumerate(lookup):
        if item is None:
            row=contrasts.loc[contrasts.tabla.eq('h1_perfil_hogares.csv')&contrasts.indicador.eq('share_d2')&contrasts.categoria_a.eq('18-29')&contrasts.categoria_b.eq('60+')].iloc[0]
            for key in ['error_estandar','ic95_inferior','ic95_superior','p_valor','p_ajustada_holm']:
                findings.loc[idx,key]=row[key]
        else:
            name,metric,age=item; row=tables[name].loc[tables[name].grupo_edad.eq(age)].iloc[0]
            for key in ['error_estandar','ic95_inferior','ic95_superior']:
                findings.loc[idx,key]=row[metric+'_'+key]
    return national
