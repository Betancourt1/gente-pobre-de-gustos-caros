"""Explicit age and historical contrasts for all reported historical indicators."""
from itertools import combinations
from pathlib import Path
import json
import numpy as np
import pandas as pd

from .survey import Design, public, difference, pairs, adjust_holm
from .historical import compare_waves
from .inference import scaled_rows

AGES={'18–29':(18,29),'30–44':(30,44),'45–59':(45,59),'60+':(60,120)}


def run(waves,out,replicates=999):
    out=Path(out); folder=out/'tables'
    registry={}; age_tests=[]; rent=[]; concentration=[]
    for year,frame in waves.items():
        print(year,'precision and all age pairs',flush=True)
        design=Design(frame,'peso','est_dis','upm',replicates=replicates,seed=20261025+year)
        groups={age:frame.edad_jefe.between(*bounds).to_numpy(bool) for age,bounds in AGES.items()}

        def add(hyp,metric,values,*,restriction=None,decile=None,kind='mean',unit='p.p.'):
            estimates={}
            for age,domain in groups.items():
                dom=domain.copy()
                if restriction is not None:dom &= np.asarray(restriction,bool)
                est=(design.distribution(values,dom)['mediana'] if kind=='median' else design.mean(values,dom))
                estimates[age]=est
                registry[(hyp,metric,decile,age,year)]=(est,unit)
            rows=pairs(estimates,family=f'edad|{year}|{hyp}|{metric}',tipo='edad',
                fuente='ENIGH',anio=year,hipotesis=hyp,indicador=metric,decil_ingreso=decile)
            age_tests.extend(scaled_rows(rows,100 if unit=='p.p.' else 1))
            return estimates

        for metric in ['alimentos_fuera','recreacion_hospedaje','h1c','h1c_sin_transferencias']:
            add('H1',metric,frame['share_'+metric])
        for decile in range(1,11):
            add('H2','h1c',frame.share_h1c,restriction=frame.decil_pc.eq(decile),decile=decile)
        for quintile in range(1,6):
            add('H1_quintil','h1c',frame.share_h1c,restriction=frame.quintil_ingreso_pc.eq(quintile),decile=quintile)
        for metric in ['prestamo_recibido','retiro_ahorro']:
            add('H3',metric,frame[metric].gt(0))
        add('H3','prestamo_o_retiro',frame.flujo_financiero)
        for metric in ['propia','propia_pagada','rentada','prestada']:
            add('H4_vivienda',metric,frame[metric],restriction=frame.principal)
        add('H4_pension','pension_en_hogar',frame.pension.gt(0))
        if year>=2014:add('H4_pension','programa_adultos_mayores',frame.apoyo_mayores.gt(0))
        if year>=2004:
            for metric in ['celular','internet','tv_paga','auto']:
                add('H1b',metric,frame['bien_'+metric])
        if year>=2014:
            valid=frame.principal&frame.unico_hogar&frame.rentada.eq(1)&frame.ing_cor.gt(0)&frame.renta_mensual.ge(0)
            values=3*frame.renta_mensual/frame.ing_cor.where(frame.ing_cor.gt(0))
            estimates=add('H4_renta','mediana_renta_ingreso',values,restriction=valid,kind='median')
            for age,est in estimates.items():
                row=dict(anio=year,grupo_edad=age,mediana_renta_ingreso=est['estimacion'],**public(est))
                rent.append(row)
        concentration_estimates={k:{} for k in ['gini','top10','top20','fraccion_hogares','fraccion_gasto']}
        for age,dom in {'Total adulto':frame.edad_jefe.ge(18).to_numpy(bool),**groups}.items():
            estimates=design.distribution(frame.h1c,dom,concentration=True)
            row={'anio':year,'grupo_edad':age,'n':int(dom.sum()),
                 'fraccion_hogares':frame.loc[dom,'peso'].sum()/frame.loc[frame.edad_jefe.ge(18),'peso'].sum(),
                 'fraccion_gasto':(frame.loc[dom,'h1c']*frame.loc[dom,'peso']).sum()/(frame.loc[frame.edad_jefe.ge(18),'h1c']*frame.loc[frame.edad_jefe.ge(18),'peso']).sum(),
                 'bootstrap_replicas':replicates}
            for metric,est in estimates.items():
                row[metric]=est['estimacion'];row[metric+'_se']=est['error_estandar']
                row[metric+'_ic95_inferior']=est['ic95_inferior'];row[metric+'_ic95_superior']=est['ic95_superior']
                row['gl_diseno']=est['gl_diseno']
                unit='índice' if metric=='gini' else 'p.p.'
                registry[('H5',metric,None,age,year)]=(est,unit)
                if age!='Total adulto':concentration_estimates[metric][age]=est
            adult=frame.edad_jefe.ge(18).to_numpy(bool)
            fractions={'fraccion_hogares':design.mean(dom,adult),
                       'fraccion_gasto':design.ratio(frame.h1c*dom,frame.h1c,adult)}
            for metric,est in fractions.items():
                assert np.isclose(row[metric],est['estimacion'],atol=1e-10)
                for field in ['error_estandar','ic95_inferior','ic95_superior']:
                    row[metric+'_'+field]=est[field]
                if age!='Total adulto':
                    registry[('H5',metric,None,age,year)]=(est,'p.p.')
                    concentration_estimates[metric][age]=est
            concentration.append(row)
        for metric,estimates in concentration_estimates.items():
            age_tests.extend(scaled_rows(pairs(estimates,family=f'edad|{year}|H5|{metric}',tipo='edad',
                fuente='ENIGH',anio=year,hipotesis='H5',indicador=metric),1 if metric=='gini' else 100))
        # The finance/spending association is a paired survey-domain contrast, by age.
        for age,domain in groups.items():
            estimates={label:design.mean(frame.share_h1c,domain&frame.flujo_financiero.eq(flag).to_numpy(bool))
                for flag,label in [(1,'Con préstamo o retiro'),(0,'Sin préstamo ni retiro')]}
            age_tests.extend(scaled_rows(pairs(estimates,family=f'flujo|{year}|H3',tipo='flujo',fuente='ENIGH',
                anio=year,hipotesis='H3',indicador='h1c_segun_flujo',grupo_edad=age),100))

    historical=[]
    keys=sorted({key[:-1] for key in registry},key=str)
    for hyp,metric,decile,age in keys:
        years=sorted(y for h,m,d,a,y in registry if (h,m,d,a)==(hyp,metric,decile,age))
        for earlier,later in combinations(years,2):
            now,unit=registry[(hyp,metric,decile,age,later)];before,_=registry[(hyp,metric,decile,age,earlier)]
            row=dict(tipo='historico',fuente='ENIGH',hipotesis=hyp,indicador=metric,
                grupo_edad=age,decil_ingreso=decile,categoria_a=str(later),categoria_b=str(earlier),
                anio_base=earlier,anio_final=later,familia=f'historico|{hyp}|{metric}|{age}',
                **difference(now,before,independent=True))
            historical.extend(scaled_rows([row],100 if unit=='p.p.' else 1))
    # Existing sensitivity/composition estimates have complete within-wave variances.
    legacy=compare_waves(waves)
    for name in ['edades_ajustadas','composicion']:
        for metric,sub in legacy[name].groupby('indicador'):
            for earlier,later in combinations(sorted(sub.anio.unique()),2):
                before=sub.loc[sub.anio.eq(earlier)].iloc[0].to_dict();now=sub.loc[sub.anio.eq(later)].iloc[0].to_dict()
                row=dict(tipo='historico',fuente='ENIGH',hipotesis='H1_'+name,indicador=metric,
                    grupo_edad='18–29',categoria_a=str(later),categoria_b=str(earlier),anio_base=earlier,anio_final=later,
                    familia=f'historico|H1_{name}|{metric}',**difference(now,before,independent=True))
                scale=100 if name=='edades_ajustadas' or metric.startswith('proporcion_') else 1
                historical.extend(scaled_rows([row],scale))
                if scale==1:historical[-1]['unidad']='años' if metric=='edad_media' else 'personas'
    adjusted=pd.read_csv(folder/'historico_edades_ajustadas.csv')
    for (hyp,metric),sub in adjusted.groupby(['hipotesis','indicador']):
        for earlier,later in combinations(sorted(sub.anio.unique()),2):
            before=sub.loc[sub.anio.eq(earlier)].iloc[0].to_dict();now=sub.loc[sub.anio.eq(later)].iloc[0].to_dict()
            row=dict(tipo='historico',fuente='ENIGH',hipotesis=hyp+'_ajustada',indicador=metric,
                grupo_edad='18–29',categoria_a=str(later),categoria_b=str(earlier),anio_base=earlier,anio_final=later,
                familia=f'historico|{hyp}_ajustada|{metric}',**difference(now,before,independent=True))
            historical.extend(scaled_rows([row],100))
    age_table=adjust_holm(pd.DataFrame(age_tests))
    time_table=adjust_holm(pd.DataFrame(historical))
    test_columns=['p_valor','p_ajustada_holm','familia','comparaciones_familia','significativa_holm_005','decision']
    old=pd.read_csv(folder/'historico_contrastes.csv')
    keys=['hipotesis','indicador','grupo_edad','anio_base','anio_final']
    old=old.merge(time_table.loc[time_table.decil_ingreso.isna(),keys+test_columns],on=keys,how='left',validate='one_to_one')
    assert old.p_ajustada_holm.notna().all()
    old.to_csv(folder/'historico_contrastes.csv',index=False,float_format='%.10g')
    h2=pd.read_csv(folder/'h2_historico_brechas.csv')
    tests=age_table.loc[age_table.hipotesis.eq('H2')&age_table.categoria_a.eq('18–29')&age_table.categoria_b.eq('60+')]
    tests=tests.rename(columns={'decil_ingreso':'decil_ingreso_pc'})
    h2=h2.merge(tests[['anio','decil_ingreso_pc']+test_columns],on=['anio','decil_ingreso_pc'],validate='one_to_one')
    h2.to_csv(folder/'h2_historico_brechas.csv',index=False,float_format='%.10g')
    association=pd.read_csv(folder/'h3_historico_asociacion.csv')
    tests=age_table.loc[age_table.tipo.eq('flujo')&age_table.grupo_edad.eq('18–29')]
    for idx,row in association.loc[association.indicador.eq('brecha_h1c_con_menos_sin_flujo')].iterrows():
        match=tests.loc[tests.anio.eq(row.anio)].iloc[0]
        for field in test_columns:association.loc[idx,field]=match[field]
    association.to_csv(folder/'h3_historico_asociacion.csv',index=False,float_format='%.10g')
    for name,frame in [('historico_comparaciones_edad.csv',age_table),
                       ('historico_comparaciones_tiempo.csv',time_table),
                       ('h4_historico_carga_renta.csv',pd.DataFrame(rent)),
                       ('h5_historico_concentracion.csv',pd.DataFrame(concentration))]:
        frame.to_csv(folder/name,index=False,float_format='%.10g')
    precision=pd.DataFrame([dict(hipotesis=h,indicador=m,decil_ingreso=d,grupo_edad=a,anio=y,unidad='proporción' if unit=='p.p.' else unit,
        **public(est)) for (h,m,d,a,y),(est,unit) in registry.items()])
    precision.to_csv(folder/'historico_precision.csv',index=False,float_format='%.10g')
    metadata_path=out/'historico_metodologia.json'
    metadata=json.loads(metadata_path.read_text())
    metadata['inferencia']={'replicas':replicates,'semilla_por_ola':'20261025 + año',
        'medias':'Taylor por estratos y UPM, con reemplazo, sin FPC',
        'no_lineales':'Rao–Wu m-1 UPM por estrato, reescaladas; IC t',
        'factores':'publicados, sin recalibración','contrastes':'covarianza dentro de ola; independencia entre olas',
        'multiplicidad':'Holm por familia explícita; IC individuales',
        'cortes_ingreso_y_pesos_edad':'tratados como fijos'}
    metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    return legacy
