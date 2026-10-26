"""Historical figures from the published aggregate tables."""
from pathlib import Path
import pandas as pd
from .figure_style import (plt, np, AGES, COLORS, INK, title, axis_style, bounds,
                           intervals, finish, panel_bars, time_panels)

def main(out):
    out=Path(out)
    def read(name):return pd.read_csv(out/'tables'/name)
    p=read('historico_perfiles.csv')
    def historic(hyp,metric):return p[p.hipotesis.eq(hyp)&p.indicador.eq(metric)]
    h1panels=[(historic('H1',key)[lambda d:d.grupo_edad.eq('18–29')],label,['18–29'],15,100) for key,label in
              [('alimentos_fuera','Alimentos fuera del hogar'),('recreacion_hospedaje','Recreación, turismo y hospedaje'),('h1c','H1c · Ambas categorías')]]
    for name in ['h1_historico_comparacion.png']:
        time_panels(out / 'figures' / name,'H1 · Gasto de los hogares jóvenes en cuatro encuestas','ENIGH · Jefatura de 18–29 años · Porcentaje del gasto monetario oficial',h1panels,
                    'IC 95% individuales',3)
    time_panels(out / 'figures' / 'h1b_historico_bienes.png','H1b · Cómo cambió el equipamiento del hogar','ENIGH 2004–2024 · Hogares por edad de la jefatura · Disponibilidad (%)',
                [(historic('H1b',k),l,['18–29','60+'],105,100) for k,l in [('celular','Teléfono celular'),('internet','Internet'),('tv_paga','Televisión de paga'),('auto','Automóvil')]],
                'IC 95% individuales · Automóvil excluye camionetas')
    time_panels(out / 'figures' / 'h3_historico_flujos.png','H3 · Préstamos recibidos y retiros de ahorro','ENIGH · Hogares con monto positivo durante el periodo de referencia (%)',
                [(historic('H3',k),l,['18–29','60+'],22,100) for k,l in [('prestamo_recibido','Recibió préstamos no hipotecarios'),('retiro_ahorro','Retiró ahorros o inversiones')]],
                'IC 95% individuales · Edad de la jefatura')
    joint=read('h3_historico_asociacion.csv');joint=joint[joint.grupo_edad.isin(['sin_prestamo_ni_retiro','con_prestamo_o_retiro'])].copy()
    joint.grupo_edad=joint.grupo_edad.map({'sin_prestamo_ni_retiro':'Sin préstamo ni retiro','con_prestamo_o_retiro':'Con préstamo o retiro'})
    fig,axs=plt.subplots(2,2,figsize=(13,8.8));title(fig,'H3 · Gasto y movimientos financieros en los mismos hogares','ENIGH · Jefatura de 18–29 años · H1c como porcentaje del gasto monetario')
    for ax,year in zip(axs.flat,[1994,2004,2014,2024]):
        d=joint[joint.anio.eq(year)].set_index('grupo_edad').loc[['Sin préstamo ni retiro','Con préstamo o retiro']].reset_index()
        panel_bars(ax,d,str(year),['Sin préstamo\nni retiro','Con préstamo\no retiro'],['#8d99ae','#00798c'],15)
    fig.subplots_adjust(left=.17,right=.90,top=.82,bottom=.08,wspace=.7,hspace=.55)
    finish(fig, out / 'figures' / 'h3_historico_gasto_flujos.png', 'IC 95% individuales · Asociación descriptiva')
    time_panels(out / 'figures' / 'h4_historico_vivienda.png','H4 · Tenencia de vivienda a edades comparables','ENIGH · Solo hogares principales, por edad de la jefatura · Porcentaje de hogares',
                [(historic('H4_vivienda',k),l,['18–29','60+'],100,100) for k,l in [('rentada','Vivienda rentada'),('propia','Propia, pagada o en pago'),('prestada','Prestada o como prestación')]],
                'IC 95% individuales · 1994: propiedad incluye terreno ejidal e irregular',3)
    time_panels(out / 'figures' / 'h4_historico_pensiones.png','H4 · Recepción de ingresos para retiro y vejez','Hogares con ingreso positivo de cualquier integrante (%) · ENIGH',
                [(historic('H4_pension',k),l,['45–59','60+'],100,100) for k,l in [('pension_en_hogar','Jubilación o pensión'),('programa_adultos_mayores','Programa para adultos mayores')]],
                'IC 95% individuales · Edad de la jefatura · Programas: 65 y más / Pensión para el Bienestar')
    c=read('h5_historico_concentracion.csv');panels=[]
    for key,label,maximum,scale in [('gini','Gini de los montos de H1c',1,1),('top10','Gasto del 10% que más gasta',100,100)]:
        d=c[c.grupo_edad.isin(['Total adulto','18–29'])].rename(columns={key:'estimacion',key+'_ic95_inferior':'ic95_inferior',key+'_ic95_superior':'ic95_superior'})
        panels.append((d,label,['Total adulto','18–29'],maximum,scale))
    time_panels(out / 'figures' / 'h5_historico_concentracion.png','H5 · Concentración del gasto en la canasta histórica','H1c · Hogares por edad de la jefatura · ENIGH',panels,
                'IC 95% individuales · Incluye hogares con gasto cero')

    # H2 historical gaps: preserve all ten points, use the same range in all years.
    h2=read('h2_historico_brechas.csv');fig,axs=plt.subplots(2,2,figsize=(13,8.8));title(fig,'H2 · Diferencia de gasto entre jóvenes y mayores','ENIGH · H1c: jefatura de 18–29 menos 60+ · Puntos porcentuales, dentro de cada decil')
    low=min(-1,float(h2.ic95_inferior.min()*100));high=float(h2.ic95_superior.max()*100)*1.15
    for ax,year in zip(axs.flat,[1994,2004,2014,2024]):
        d=h2[h2.anio.eq(year)].sort_values('decil_ingreso_pc');v,lo,hi=bounds(d)
        intervals(ax,d.decil_ingreso_pc.to_numpy(),v,lo,hi,fmt='o',color='#00798c',capsize=4,ms=5)
        ax.axhline(0,color=INK,lw=1.1);ax.set_xticks(range(1,11));ax.set_ylim(low,high);axis_style(ax,False)
        ax.set_title(str(year),loc='left',weight='bold');ax.set_xlabel('Decil de ingreso por persona');ax.set_ylabel('Diferencia (p.p.)')
    fig.subplots_adjust(left=.09,right=.97,top=.83,bottom=.12,hspace=.4,wspace=.25)
    finish(fig, out / 'figures' / 'h2_historico_brechas.png', 'IC 95% individuales · 1: menor ingreso; 10: mayor ingreso')
