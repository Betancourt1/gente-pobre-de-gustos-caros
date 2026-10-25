"""Comparación histórica H1–H5; publica agregados y figuras, sin microdatos."""
from pathlib import Path
import json
import sys
import hashlib
import argparse
import tempfile
import os
import numpy as np
import pandas as pd
from dbfread import DBF
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports'
sys.path.insert(0, str(ROOT / 'src'))
from gpdgc.historical import load_wave, survey_mean, survey_variance, YEARS
from gpdgc.weights import weighted_quantile, gini, top_share

RAW = ROOT / 'data/raw/enigh'
GROUPS = {'18–29': (18,29), '30–44': (30,44), '45–59': (45,59), '60+': (60,120)}
INCOME_CODES = {
    1994: {'prestamo_recibido': ['P033'], 'retiro_ahorro': ['P031'], 'pension': ['P023']},
    2004: {'prestamo_recibido': ['P064'], 'retiro_ahorro': ['P062'], 'pension': ['P048','P049']},
    2014: {'prestamo_recibido': ['P053'], 'retiro_ahorro': ['P051'], 'pension': ['P032','P033']},
    2024: {'prestamo_recibido': ['P053'], 'retiro_ahorro': ['P051'], 'pension': ['P032','P033']},
}
files_read = set()
validation = []

def read_table(year, kind):
    folder = RAW / str(year) / 'microdata'
    if year < 2014:
        p = folder / f'{kind}_dbf/{kind}.dbf'
        d = pd.DataFrame(iter(DBF(str(p), encoding='latin1')))
        d.columns = d.columns.str.lower()
        d['id'] = d.folio.str.strip()
    else:
        matches = [p for p in folder.rglob('*.csv') if
                   ((kind == 'viviendas' and ('vivi' in p.name)) or
                    (kind != 'viviendas' and kind in p.name and 'jcf' not in p.name))]
        assert len(matches) == 1, (year,kind,matches)
        p = matches[0]
        d = pd.read_csv(p, dtype=str)
        if kind != 'viviendas':
            d['id'] = d.folioviv.str.strip() + d.foliohog.str.strip()
    files_read.add(p)
    return d

def mean_row(df, year, hyp, metric, group, domain, values, **extra):
    return {'anio':year, 'hipotesis':hyp, 'indicador':metric, 'grupo_edad':group,
            **extra, **survey_mean(df, values, domain)}

def gap(df, values, a, b):
    v=np.asarray(values,float); w=df.peso.to_numpy(float)
    a=np.asarray(a)&np.isfinite(v); b=np.asarray(b)&np.isfinite(v)
    ma=np.average(v[a],weights=w[a]); mb=np.average(v[b],weights=w[b])
    influence=np.zeros(len(df))
    influence[a]=w[a]*(v[a]-ma)/w[a].sum()
    influence[b]-=w[b]*(v[b]-mb)/w[b].sum()
    variance, degrees=survey_variance(df,influence)
    se=np.sqrt(variance); margin=t.ppf(.975,degrees)*se
    return dict(estimacion=ma-mb,error_estandar=se,ic95_inferior=ma-mb-margin,
                ic95_superior=ma-mb+margin,n_joven=int(a.sum()),n_mayor=int(b.sum()),gl_diseno=degrees)

def augment(year, df):
    inc=read_table(year,'ingresos')
    assert not set(inc.id)-set(df.index), (year,'income orphan keys')
    for name,codes in INCOME_CODES[year].items():
        part=inc.loc[inc.clave.str.strip().isin(codes)].copy()
        part['amount']=pd.to_numeric(part.ing_tri,errors='raise')
        assert part.amount.notna().all() and part.amount.ge(0).all()
        df[name]=part.groupby('id').amount.sum().reindex(df.index,fill_value=0)
    # Reconcile raw financial flows with the official aggregates where available.
    if year >= 2004:
        for name,col in [('prestamo_recibido','prestamo' if year==2004 else 'prestamos'),
                         ('retiro_ahorro','retiro' if year==2004 else 'retiro_inv'),
                         ('pension','jubila' if year==2004 else 'jubilacion')]:
            compare=df[name]
            # JUBILA 2004 includes insurance/work/severance compensation, unlike 2014/2024.
            # Preserve pure pension income for analysis, reconcile the wider aggregate separately.
            if year==2004 and name=='pension':
                extras=inc.loc[inc.clave.isin(['P050','P051','P052'])].copy()
                extras['amount']=pd.to_numeric(extras.ing_tri,errors='raise')
                compare=compare+extras.groupby('id').amount.sum().reindex(df.index,fill_value=0)
            error=(compare-pd.to_numeric(df[col])).abs().max()
            validation.append({'anio':year,'control':f'conciliacion_{name}','valor':error})
            if year==2004 and name=='pension':
                # One source household remains inconsistent (10,500 vs 21,000).
                # Use explicit raw pension codes; preserve the discrepancy in validation.
                mismatches=(compare-pd.to_numeric(df[col])).abs().gt(.10).sum()
                validation.append({'anio':year,'control':'n_discrepancias_jubila_ampliada','valor':int(mismatches)})
                assert mismatches==1 and abs(error-10500)<.1
            else:
                assert error <= .10, (year,name,error)
    df['flujo_financiero']=(df.prestamo_recibido.gt(0)|df.retiro_ahorro.gt(0)).astype(float)
    if year>=2014:
        code='P044' if year==2014 else 'P104'
        support=inc.loc[inc.clave.eq(code)].copy()
        support['amount']=pd.to_numeric(support.ing_tri,errors='raise')
        df['apoyo_mayores']=support.groupby('id').amount.sum().reindex(df.index,fill_value=0)
    hh=read_table(year,'hogares').set_index('id',verify_integrity=True).reindex(df.index)
    assert hh.index.equals(df.index)
    if year < 2014:
        ten=pd.to_numeric(hh['tenencia' if year==1994 else 'tenencia12'],errors='coerce')
        df['principal']=df.index.str.endswith('0')
        rent=5 if year==1994 else 1
        own=[1,2,3,4] if year==1994 else [4,5]
        paid=[1,2,3] if year==1994 else [5]
        borrowed=[6,7] if year==1994 else [2,3]
        valid=ten.isin(range(1,9) if year==1994 else range(1,7))
    else:
        viv=read_table(year,'viviendas').set_index('folioviv',verify_integrity=True)
        assert set(df.folioviv) <= set(viv.index)
        ten=pd.to_numeric(df.folioviv.map(viv.tenencia),errors='raise')
        df['principal']=df.foliohog.eq('1')
        rent=1; own=[3,4]; paid=[4]; borrowed=[2]; valid=ten.isin(range(1,7))
        df['renta_mensual']=pd.to_numeric(df.folioviv.map(viv.renta),errors='coerce')
        df['unico_hogar']=pd.to_numeric(df.folioviv.map(viv.tot_hog)).eq(1)
    assert valid[df.principal].all(), (year,'missing tenure primary household')
    for name,mask in [('rentada',ten.eq(rent)),('propia',ten.isin(own)),
                      ('propia_pagada',ten.isin(paid)),('prestada',ten.isin(borrowed))]:
        df[name]=mask.astype(float).where(valid)
    if year >= 2004:
        for metric,old,new in [('celular','serv01_2','celular'),('internet','serv01_4','conex_inte'),('tv_paga','serv01_3','tv_paga')]:
            v=pd.to_numeric(hh[old if year==2004 else new],errors='raise')
            assert v.isin([1,2]).all()
            df[f'bien_{metric}']=v.eq(1).astype(float)
        v=pd.to_numeric(hh['vehi06_1' if year==2004 else 'num_auto'],errors='raise')
        assert v.notna().all() and v.ge(0).all()
        df['bien_auto']=v.gt(0).astype(float)
    adult=df.edad_jefe.ge(18)
    income=df.ing_cor/df.tot_integ
    cuts=[weighted_quantile(income[adult],df.peso[adult],q/10) for q in range(1,10)]
    df['decil_pc']=np.searchsorted(cuts,income,side='left')+1
    validation.append({'anio':year,'control':'n_hogares_principales_adultos','valor':int((adult&df.principal).sum())})
    return df

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'tables').mkdir(exist_ok=True)
    (OUT/'figures').mkdir(exist_ok=True)
    waves={}
    for year in YEARS:
        print(f'{year}: lectura y validación',flush=True)
        df, audit=load_wave(RAW,year)
        waves[year]=augment(year,df)
        validation.append({'anio':year,'control':'n_hogares_fuente','valor':len(df)})
    rows=[]; h2=[]; h3joint=[]; concentration=[]; rents=[]; adjusted=[]
    ref=waves[2024]; refyoung=ref.edad_jefe.between(18,29)
    refweights=ref.loc[refyoung].groupby('edad_jefe').peso.sum()
    refweights=(refweights/refweights.sum()).to_dict()
    refhousing=ref.loc[refyoung&ref.principal].groupby('edad_jefe').peso.sum()
    refhousing=(refhousing/refhousing.sum()).to_dict()
    for year,df in waves.items():
        adult=df.edad_jefe.ge(18); young=df.edad_jefe.between(18,29); old=df.edad_jefe.ge(60)
        print(f'{year}: estadísticas H1–H5',flush=True)
        for group,(lo,hi) in GROUPS.items():
            domain=df.edad_jefe.between(lo,hi)
            for metric in ['alimentos_fuera','recreacion_hospedaje','h1c']:
                rows.append(mean_row(df,year,'H1',metric,group,domain,df['share_'+metric]))
            for metric in ['prestamo_recibido','retiro_ahorro']:
                rows.append(mean_row(df,year,'H3',metric,group,domain,df[metric].gt(0).astype(float)))
            rows.append(mean_row(df,year,'H3','prestamo_o_retiro',group,domain,df.flujo_financiero))
            for metric in ['rentada','propia','propia_pagada','prestada']:
                rows.append(mean_row(df,year,'H4_vivienda',metric,group,domain&df.principal,df[metric]))
            rows.append(mean_row(df,year,'H4_pension','pension_en_hogar',group,domain,df.pension.gt(0).astype(float)))
            if year>=2014:
                rows.append(mean_row(df,year,'H4_pension','programa_adultos_mayores',group,domain,df.apoyo_mayores.gt(0).astype(float)))
            if year>=2004:
                for metric in ['celular','internet','tv_paga','auto']:
                    rows.append(mean_row(df,year,'H1b',metric,group,domain,df['bien_'+metric]))
            if year>=2014:
                # One-household dwellings avoid charging a dwelling's full rent to one of several households.
                valid=domain&df.principal&df.unico_hogar&df.rentada.eq(1)&df.ing_cor.gt(0)&df.renta_mensual.ge(0)
                ratio=3*df.renta_mensual/df.ing_cor.where(df.ing_cor.gt(0))
                rents.append({'anio':year,'grupo_edad':group,'mediana_renta_ingreso':weighted_quantile(ratio[valid],df.peso[valid],.5),
                              'n':int(valid.sum()),'hogares_expandidos':df.peso[valid].sum()})
        for decile in range(1,11):
            domain=df.decil_pc.eq(decile)
            h2.append({'anio':year,'decil_ingreso_pc':decile,
                       **gap(df,df.share_h1c,domain&young,domain&old)})
            for name,dom in [('18–29',domain&young),('60+',domain&old)]:
                rows.append(mean_row(df,year,'H2','h1c',name,dom,df.share_h1c,decil_ingreso_pc=decile))
        for flag,label in [(0,'sin_prestamo_ni_retiro'),(1,'con_prestamo_o_retiro')]:
            dom=young&df.flujo_financiero.eq(flag)
            h3joint.append(mean_row(df,year,'H3','h1c_segun_flujo',label,dom,df.share_h1c))
        h3joint.append({'anio':year,'hipotesis':'H3','indicador':'brecha_h1c_con_menos_sin_flujo','grupo_edad':'18–29',
                        **gap(df,df.share_h1c,young&df.flujo_financiero.eq(1),young&df.flujo_financiero.eq(0))})
        for label,dom in [('Total adulto',adult),('18–29',young),('60+',old)]:
            v=df.loc[dom,'h1c']; w=df.loc[dom,'peso']
            concentration.append({'anio':year,'grupo_edad':label,'gini':gini(v,w),
                                  'top10':top_share(v,w,.1),'top20':top_share(v,w,.2),'n':len(v),
                                  'fraccion_hogares':w.sum()/df.loc[adult,'peso'].sum(),
                                  'fraccion_gasto':(v*w).sum()/(df.loc[adult,'h1c']*df.loc[adult,'peso']).sum()})
        for hyp,metric,values,dom,aw in [
            ('H3','prestamo_recibido',df.prestamo_recibido.gt(0),young,refweights),
            ('H3','retiro_ahorro',df.retiro_ahorro.gt(0),young,refweights),
            ('H4_vivienda','rentada',df.rentada,young&df.principal,refhousing),
            ('H4_vivienda','propia',df.propia,young&df.principal,refhousing)]:
            adjusted.append({'anio':year,'hipotesis':hyp,'indicador':metric,
                             **survey_mean(df,values,dom,aw)})
    outputs={'perfiles':pd.DataFrame(rows),'h2_brechas':pd.DataFrame(h2),'h3_asociacion':pd.DataFrame(h3joint),
             'h4_carga_renta':pd.DataFrame(rents),'h5_concentracion':pd.DataFrame(concentration),
             'edades_ajustadas':pd.DataFrame(adjusted),'validacion':pd.DataFrame(validation)}
    # Independent-wave contrasts; original survey covariance is retained within each year's H2 gap.
    changes=[]
    p=outputs['perfiles']
    for (hyp,metric,group),tab in p.loc[p.hipotesis.ne('H2')].groupby(['hipotesis','indicador','grupo_edad']):
        now=tab.loc[tab.anio.eq(2024)].iloc[0]
        for _,before in tab.loc[tab.anio.lt(2024)].iterrows():
            se=np.hypot(now.error_estandar,before.error_estandar)
            change=now.estimacion-before.estimacion
            margin=t.ppf(.975,min(now.gl_diseno,before.gl_diseno))*se
            changes.append({'hipotesis':hyp,'indicador':metric,'grupo_edad':group,'anio_base':int(before.anio),
                            'anio_final':2024,'cambio_pp':100*change,'error_estandar_pp':100*se,
                            'ic95_inferior_pp':100*(change-margin),'ic95_superior_pp':100*(change+margin)})
    outputs['contrastes']=pd.DataFrame(changes)
    table_names={'perfiles': 'historico_perfiles.csv', 'resumen': 'historico_resumen.csv', 'contrastes': 'historico_contrastes.csv', 'correspondencias': 'historico_correspondencias.csv', 'edades_ajustadas': 'historico_edades_ajustadas.csv', 'validacion': 'historico_validacion.csv', 'h2_brechas': 'h2_historico_brechas.csv', 'h3_asociacion': 'h3_historico_asociacion.csv', 'h4_carga_renta': 'h4_historico_carga_renta.csv', 'h5_concentracion': 'h5_historico_concentracion.csv'}
    for name,table in outputs.items():
        table.to_csv(OUT/'tables'/table_names[name],index=False,float_format='%.10f')
    # Reproduce the existing H1 estimates before interpreting the extensions.
    baseline=pd.read_csv(ROOT/'reports/tables/h1_historico_perfiles.csv')
    check=p.loc[p.hipotesis.eq('H1')].merge(baseline,on=['anio','grupo_edad','indicador'],suffixes=('_new','_old'))
    assert len(check)==48
    assert np.allclose(check.estimacion_new,check.estimacion_old,atol=1e-9)
    metadata={'base_commit':'49c36532d6d2701162ba588d57a823b8b21a9254',
              'years':list(YEARS),'income_codes':INCOME_CODES,'h1_max_difference':float(abs(check.estimacion_new-check.estimacion_old).max()),
              'new_source_files':[{'path':str(p.relative_to(RAW)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files_read)],
              'official_catalogs':[
                  'https://www.inegi.org.mx/contenidos/programas/enigh/tradicional/1994/doc/catalogo94.pdf',
                  'https://www.inegi.org.mx/contenidos/programas/enigh/tradicional/2004/doc/catalogo04.pdf']}
    (OUT/'historico_metodologia.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print('Listo:',{k:len(v) for k,v in outputs.items()},flush=True)

    return waves

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,default=RAW)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args()
    RAW=args.raw.resolve()
    OUT=args.output.resolve()
    with tempfile.TemporaryDirectory(prefix='enigh-matplotlib-') as cache:
        os.environ.setdefault('MPLCONFIGDIR',cache)
        from gpdgc import historical_figures as figures
        from gpdgc import historical_report as report
        waves=main()
        figures.concentration_uncertainty(waves,OUT)
        figures.main(OUT)
        report.main(OUT)
