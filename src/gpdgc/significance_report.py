"""Readable pairwise contrasts: individual CIs and explicit Holm decisions."""
from pathlib import Path
import html
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

LABELS={
 'share_d1':'D1','share_d2':'D2','share_d3':'D3','h1c':'H1c',
 'h1c_sin_transferencias':'H1c sin transferencias','alimentos_fuera':'Alimentos fuera',
 'recreacion_hospedaje':'Recreación y hospedaje','gasto_d2_eq':'Monto D2 equivalente',
 'pct_afore':'Tiene AFORE','pct_reporta_ahorro_cuentas':'Reporta ahorro en cuentas',
 'pct_deuda_credito':'Deuda o productos de crédito','pct_reporta_atraso':'Reporta atraso',
 'pct_ingreso_insuficiente':'Ingreso insuficiente','pct_alto_estres':'Alto estrés',
 'pct_gasto_supera_ingreso_laboral':'Gasto supera ingreso laboral',
 'pct_comparables_ingreso_gasto':'Cobertura de comparación gasto/ingreso',
 'pct_rentados':'Hogares que rentan','carga_renta_mediana':'Mediana renta/ingreso',
 'mediana_renta_ingreso':'Mediana renta/ingreso','propia':'Vivienda propia',
 'propia_pagada':'Vivienda propia pagada','rentada':'Vivienda rentada','prestada':'Vivienda prestada',
 'pension_en_hogar':'Ingreso por pensión','programa_adultos_mayores':'Programa de adultos mayores',
 'prestamo_recibido':'Préstamo recibido','retiro_ahorro':'Retiro de ahorro',
 'h1c_segun_flujo':'H1c según préstamo/retiro','celular':'Celular','internet':'Internet',
 'tv_paga':'TV de paga','auto':'Automóvil','gini':'Gini H1c','top10':'Top 10% H1c','top20':'Top 20% H1c',
 'gini_d2':'Gini D2','top10_d2':'Top 10% D2','top20_d2':'Top 20% D2',
 'share_gasto_d2_total':'Participación en gasto nacional D2',
 'fraccion_hogares':'Proporción de hogares de cada edad','fraccion_gasto':'Participación en gasto nacional H1c',
 'prestamo_o_retiro':'Préstamo o retiro recibido',
 'share_d2_alcohol':'D2: alcohol/tabaco','share_d2_restaurantes':'D2: restaurantes/hoteles',
 'share_d2_recreacion':'D2: recreación','share_d2_personal':'D2: accesorios',
 'share_d2_streaming':'D2: digital/TV','share_d2_auto':'D2: automóvil nuevo'}


def pformat(value):
    return '<0.0001' if value < .0001 else f'{value:.4f}'


def forest(frame,path,title):
    """Every point is a difference, not a level; symbols encode the Holm decision."""
    frame=frame.reset_index(drop=True)
    if frame.empty:return
    fig,ax=plt.subplots(figsize=(12,max(4.8,.31*len(frame)+1.8)))
    y=np.arange(len(frame));labels=[]
    for i,row in frame.iterrows():
        detected=bool(row.significativa_holm_005)
        color='#00798c' if detected else '#666666'
        ax.errorbar(row.estimacion,i,xerr=[[row.estimacion-row.ic95_inferior],[row.ic95_superior-row.estimacion]],
            fmt='o' if detected else 's',mfc=color if detected else 'white',mec=color,
            ecolor=color,capsize=3,ms=5)
        labels.append(f"{row.categoria_a} − {row.categoria_b}")
        ax.text(1.02,i,pformat(row.p_ajustada_holm),transform=ax.get_yaxis_transform(),va='center',fontsize=9)
    ax.axvline(0,color='#333333',lw=1);ax.set_yticks(y,labels);ax.invert_yaxis()
    ax.set_xlabel('Diferencia ('+str(frame.unidad.iloc[0])+')');ax.grid(axis='x',alpha=.2)
    ax.set_title(title,loc='left',fontsize=14,pad=22)
    ax.text(1.02,1.02,'p de Holm',transform=ax.transAxes,fontsize=9)
    fig.text(.02,.02,'Intervalos individuales al 95%. ● Diferencia detectada con Holm < 0.05; □ evidencia insuficiente.\nLa decisión ajustada puede diferir de si el IC individual cruza cero. Universo y familias: significancia.html.',fontsize=9)
    fig.subplots_adjust(left=.23,right=.86,bottom=.18,top=.85)
    fig.savefig(path,dpi=160);plt.close(fig)


def decile_forest(frame,path,title):
    combos=list(frame.groupby(['categoria_a','categoria_b'],sort=False))
    fig,axs=plt.subplots(2,3,figsize=(14,9),sharey=True)
    for ax,((a,b),d) in zip(axs.flat,combos):
        d=d.sort_values('decil_ingreso')
        for _,r in d.iterrows():
            detected=bool(r.significativa_holm_005);color='#00798c' if detected else '#666666'
            ax.errorbar(r.estimacion,r.decil_ingreso,xerr=[[r.estimacion-r.ic95_inferior],[r.ic95_superior-r.estimacion]],
                fmt='o' if detected else 's',mfc=color if detected else 'white',ecolor=color,mec=color,capsize=2)
        ax.axvline(0,color='#444444',lw=1);ax.set_title(f'{a} − {b}');ax.grid(axis='x',alpha=.2)
        ax.set_yticks(range(1,11));ax.set_ylabel('Decil');ax.set_xlabel('Diferencia ('+str(d.unidad.iloc[0])+')')
    fig.suptitle(title,fontsize=16)
    fig.text(.06,.02,'IC 95% individuales. ● Diferencia detectada con Holm < 0.05; □ evidencia insuficiente.\nHolm incluye los seis pares de edades en los diez deciles (60 pruebas). Valores p e intervalos exactos: significancia.html.',fontsize=10)
    fig.subplots_adjust(left=.06,right=.98,top=.90,bottom=.14,hspace=.35,wspace=.27)
    fig.savefig(path,dpi=160);plt.close(fig)


def build(out):
    out=Path(out);tables=out/'tables';figures=out/'figures';figures.mkdir(exist_ok=True)
    frames=[]
    for name in ['contrastes_categorias.csv','historico_comparaciones_edad.csv','historico_comparaciones_tiempo.csv']:
        path=tables/name
        if path.exists():
            d=pd.read_csv(path);d['archivo']=name;frames.append(d)
    if not frames:return
    all_rows=pd.concat(frames,ignore_index=True)
    all_rows.significativa_holm_005=all_rows.significativa_holm_005.astype(str).str.lower().eq('true')
    main=all_rows.loc[all_rows.archivo.eq('contrastes_categorias.csv')]
    selections=[('h1_comparaciones_edad','h1_perfil_hogares.csv','share_d2','H1 · Diferencias de D2 entre todas las edades'),
        ('h1b_comparaciones_edad','h1b_bienes_ensafi.csv','Internet','H1b · Internet: diferencias entre todas las edades'),
        ('h3_comparaciones_edad','h3_finanzas_ensafi.csv','pct_alto_estres','H3 · Alto estrés: diferencias entre todas las edades'),
        ('h4_comparaciones_edad','h4_vivienda_por_edad.csv','pct_rentados','H4 · Renta: diferencias entre todas las edades'),
        ('h5_comparaciones_edad','h5_concentracion_por_edad.csv','top20_d2','H5 · Top 20% de D2: diferencias entre edades')]
    chart_links=[]
    for name,table,metric,title in selections:
        d=main.loc[main.tabla.eq(table)&main.indicador.eq(metric)] if len(main) else pd.DataFrame()
        if len(d):forest(d,figures/(name+'.png'),title);chart_links.append((title,name+'.png'))
    history=all_rows.loc[all_rows.archivo.eq('historico_comparaciones_tiempo.csv')]
    for hypothesis,metric,title in [('H1','h1c','H1c: diferencias entre años a los 18–29'),
                                     ('H4_vivienda','propia','Vivienda propia: diferencias entre años a los 18–29'),
                                     ('H5','top10','Concentración: diferencias entre años a los 18–29')]:
        d=history.loc[history.hipotesis.eq(hypothesis)&history.indicador.eq(metric)&history.grupo_edad.eq('18–29')] if len(history) else pd.DataFrame()
        name=hypothesis.lower()+'_comparaciones_tiempo.png'
        if len(d):forest(d,figures/name,title);chart_links.append((title,name))
    for table,metric,name,title in [
        ('h2_share_d2_por_decil.csv','share_d2','h2_comparaciones_participacion.png','H2 · Diferencias de participación D2 entre edades'),
        ('h2_nivel_d2_por_decil.csv','gasto_d2_eq','h2_comparaciones_monto.png','H2 · Diferencias de monto D2 entre edades')]:
        d=main.loc[main.tabla.eq(table)&main.indicador.eq(metric)] if len(main) else pd.DataFrame()
        if len(d):decile_forest(d,figures/name,title);chart_links.append((title,name))
    historic_age=all_rows.loc[all_rows.archivo.eq('historico_comparaciones_edad.csv')]
    if len(historic_age):
        for year,d in historic_age.loc[historic_age.hipotesis.eq('H2')].groupby('anio'):
            name=f'h2_comparaciones_{int(year)}.png';title=f'H2 · Diferencias entre edades dentro de deciles, {int(year)}'
            decile_forest(d,figures/name,title);chart_links.append((title,name))
    # H2 has ten deciles: retain each family of sixty tests in the full searchable table.
    rows=[]
    for _,r in all_rows.iterrows():
        year=str(int(r.anio)) if pd.notna(r.get('anio')) else 'Entre años'
        age=str(r.get('grupo_edad','')) if pd.notna(r.get('grupo_edad')) else ''
        rank=f" · decil/quintil {int(r.decil_ingreso)}" if pd.notna(r.get('decil_ingreso')) else ''
        rows.append({'fuente':r.fuente,'tipo':r.tipo,'contexto':year+' '+age+rank,
            'indicador':LABELS.get(r.indicador,r.indicador),'a':str(r.categoria_a),'b':str(r.categoria_b),
            'diferencia':float(r.estimacion),'inferior':float(r.ic95_inferior),'superior':float(r.ic95_superior),
            'unidad':r.unidad,'p':float(r.p_valor),'p_holm':float(r.p_ajustada_holm),
            'decision':r.decision,'familia':r.familia,'pruebas':int(r.comparaciones_familia),
            'archivo':r.archivo})
    data=json.dumps(rows,ensure_ascii=False).replace('</','<\\/')
    charts=''.join(f'<figure><img src="figures/{name}" alt="{html.escape(title)}"><figcaption>{html.escape(title)}</figcaption></figure>' for title,name in chart_links)
    content='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Diferencias entre categorías — ENIGH y ENSAFI</title><style>
body{font:16px/1.5 system-ui;margin:0;color:#222}main{max-width:1250px;margin:auto;padding:28px}h1{line-height:1.15}p{max-width:950px}input,select{font:inherit;padding:9px;max-width:100%;margin:5px}label{display:inline-block}table{border-collapse:collapse;font-size:14px;width:100%}th,td{padding:9px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}th{background:#f2f4f5;position:sticky;top:0}td.num{white-space:nowrap;font-variant-numeric:tabular-nums}.scroll{overflow:auto;max-height:75vh}img{width:100%;height:auto}figure{margin:30px 0}small{color:#555}.yes{color:#006b7c;font-weight:700}button{font:inherit;padding:8px}summary{cursor:pointer;font-weight:600}@media(max-width:600px){main{padding:16px}h1{font-size:27px}}@media print{input,select,button{display:none}.scroll{max-height:none;overflow:visible}th{position:static}}
</style><main><h1>¿Qué categorías presentan diferencias detectables?</h1>
<p>Cada renglón contrasta <b>categoría A menos categoría B</b>. Se informa el tamaño de la diferencia, su IC 95% individual y el valor p ajustado con Holm. <b>“Diferencia detectada” significa p de Holm &lt; 0.05</b>. “Evidencia insuficiente” no demuestra igualdad. La magnitud y el intervalo permiten valorar la importancia práctica.</p>
<p>Se comparan los seis pares de los cuatro grupos principales (18–29, 30–44, 45–59 y 60+) dentro de cada indicador y año, y todos los años disponibles a una misma edad. Los grupos corresponden a jefatura del hogar en ENIGH y a personas adultas en ENSAFI. H1c y D2 conservan sus definiciones distintas.</p>
<details><summary>Método, familias y límites</summary><p>Medias y razones: linealización de Taylor por estratos y UPM, con todas las UPM de la muestra, incluso las que no aportan observaciones al dominio. Las diferencias dentro de una encuesta retienen la covarianza. Medianas, Gini, participaciones superiores y Lorenz: réplicas Rao–Wu de UPM (cantidad registrada en los CSV de precisión), con ponderadores publicados y sin recalibración. Aproximación con reemplazo, sin corrección por población finita. IC t; grados de libertad UPM menos estratos, limitados a B−1 para réplicas.</p><p>Holm controla el error familiar entre todos los pares de edad de un indicador/año; H2 incluye los pares de los diez deciles en esa familia. Los pares de años forman otra familia por indicador/edad; quintiles/deciles se incluyen conjuntamente. Las pruebas de gasto según flujos se ajustan entre edades dentro de cada año. La columna Familia muestra el alcance exacto. Los IC son individuales, no intervalos simultáneos.</p><p>Las comparaciones entre olas suponen independencia. Los cortes de ingreso y los pesos de estandarización por edad se tratan como fijos. No se incorpora incertidumbre por cambios de cuestionario, clasificación, calibración, no respuesta o subreporte. Estas pruebas describen diferencias; no identifican efectos causales, equivalencia ni diferencias puras de cohorte.</p></details>
<p><a href="../README.md">README</a> · <a href="tables/contrastes_categorias.csv">CSV original</a> · <a href="tables/historico_comparaciones_edad.csv">CSV edades históricas</a> · <a href="tables/historico_comparaciones_tiempo.csv">CSV años</a></p>
<label>Buscar indicador, edad, año o familia<br><input id="query" type="search" placeholder="Ej.: H1c, 2024, 18–29"></label>
<label>Tipo<br><select id="kind"><option value="">Todos</option><option value="edad">Edades</option><option value="historico">Años a igual edad</option><option value="flujo">Préstamos/retiros</option></select></label>
<label>Resultado<br><select id="decision"><option value="">Todos</option><option value="yes">Diferencia detectada</option><option value="no">Evidencia insuficiente</option></select></label>
<p id="count" aria-live="polite"></p><div class="scroll"><table><thead><tr><th>Indicador / universo</th><th>A − B</th><th>Diferencia [IC 95%]</th><th>p</th><th>p Holm</th><th>Resultado / familia</th></tr></thead><tbody id="rows"></tbody></table></div>
'''+charts+'''<script>const data='''+data+''';const body=document.querySelector('#rows');
const number=x=>x.toLocaleString('es-MX',{maximumFractionDigits:3});const p=x=>x<.0001?'<0.0001':x.toFixed(4);
function cell(tr,text,cls=''){const td=document.createElement('td');td.textContent=text;td.className=cls;tr.append(td)}
function render(){const q=document.querySelector('#query').value.toLocaleLowerCase(),kind=document.querySelector('#kind').value,decision=document.querySelector('#decision').value;const filtered=data.filter(r=>(!q||Object.values(r).join(' ').toLocaleLowerCase().includes(q))&&(!kind||r.tipo===kind)&&(!decision||(r.p_holm<.05)===(decision==='yes')));body.replaceChildren();for(const r of filtered){const tr=document.createElement('tr');cell(tr,r.indicador+' · '+r.fuente+' '+r.contexto);cell(tr,r.a+' − '+r.b);cell(tr,number(r.diferencia)+' ['+number(r.inferior)+', '+number(r.superior)+'] '+r.unidad,'num');cell(tr,p(r.p),'num');cell(tr,p(r.p_holm),'num');cell(tr,r.decision+' · '+r.familia+' ('+r.pruebas+' pruebas)',r.p_holm<.05?'yes':'');body.append(tr)}document.querySelector('#count').textContent=filtered.length+' de '+data.length+' comparaciones.'}for(const id of ['query','kind','decision'])document.querySelector('#'+id).addEventListener('input',render);render();</script></main></html>'''
    (out/'significancia.html').write_text(content)
    summary=all_rows.groupby(['archivo','tipo']).agg(comparaciones=('p_valor','size'),diferencias_holm=('significativa_holm_005','sum')).reset_index()
    summary.to_csv(tables/'resumen_significancia.csv',index=False)
    print('Significance report:',len(rows),'comparisons;',len(chart_links),'contrast figures',flush=True)
