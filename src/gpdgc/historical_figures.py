"""Gráficas y precisión de concentración para la exploración histórica."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parents[2]/'reports'
YEARS=[1994,2004,2014,2024]
COLORS={'18–29':'#00798c','30–44':'#b36d23','45–59':'#777777','60+':'#b43d58','Total adulto':'#68727d'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
                     'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})

def style(ax,years=YEARS):
    ax.set_xticks(years)
    ax.grid(axis='y',alpha=.18)
    ax.set_axisbelow(True)
    ax.set_xlabel('Año de ENIGH')

def series(ax,table,groups=('18–29','60+'),scale=100,labels=False):
    for group in groups:
        d=table.loc[table.grupo_edad.eq(group)].sort_values('anio')
        p=d.estimacion.to_numpy()*scale
        err=np.vstack([p-d.ic95_inferior.to_numpy()*scale,d.ic95_superior.to_numpy()*scale-p])
        ax.errorbar(d.anio,p,yerr=err,fmt='o-',capsize=3,lw=1.5,color=COLORS[group],label=group)
        if labels and group==groups[0]:
            for x,y,upper in zip(d.anio,p,d.ic95_superior.to_numpy()*scale):
                others=table.loc[table.anio.eq(x)&table.grupo_edad.isin(groups)&table.grupo_edad.ne(group),'estimacion']*scale
                below=not others.empty and others.max()>y
                anchor=float(d.loc[d.anio.eq(x),'ic95_inferior'].iloc[0])*scale if below else upper
                ax.annotate(f'{y:.1f}',(x,anchor),xytext=(0,-13 if below else 6),textcoords='offset points',ha='center',fontsize=9)

def save(fig,name,title,note):
    fig.suptitle(title,x=.08,ha='left',fontsize=16,y=.98)
    fig.text(.08,.025,note,fontsize=9,color='#444444',va='bottom')
    fig.subplots_adjust(left=.08,right=.97,top=.84,bottom=.22,wspace=.28,hspace=.55)
    fig.savefig(OUT/'figures'/f'{name}.png',dpi=175)
    plt.close(fig)

def concentration_uncertainty(waves,out):
    out=Path(out)
    result=pd.read_csv(out/'tables/h5_historico_concentracion.csv')
    rng=np.random.default_rng(20261025)
    B=399
    for year,df in waves.items():
        print(year,'bootstrap H5',flush=True)
        units=df[['est_dis','upm']].drop_duplicates().sort_values(['est_dis','upm'])
        sizes=units.groupby('est_dis',sort=True).size().to_numpy()
        unitindex=pd.MultiIndex.from_frame(units)
        ids=unitindex.get_indexer(pd.MultiIndex.from_frame(df[['est_dis','upm']]))
        assert ids.min()>=0 and (sizes>=2).all()
        ordered={}
        for label,dom in [('Total adulto',df.edad_jefe.ge(18)),('18–29',df.edad_jefe.between(18,29)),('60+',df.edad_jefe.ge(60))]:
            pos=np.flatnonzero(dom.to_numpy())
            pos=pos[np.argsort(df.h1c.to_numpy()[pos],kind='stable')]
            ordered[label]=(df.h1c.to_numpy()[pos],df.peso.to_numpy()[pos],ids[pos])
        draws={label:[] for label in ordered}
        for _ in range(B):
            mult=np.concatenate([rng.multinomial(int(m-1),np.full(m,1/m))*m/(m-1) for m in sizes])
            for label,(values,weight,unit) in ordered.items():
                w=weight*mult[unit]
                cw=np.cumsum(w); cv=np.cumsum(values*w)
                x=np.r_[0,cw/cw[-1]]; y=np.r_[0,cv/cv[-1]]
                draws[label].append([1-2*np.trapezoid(y,x),1-np.interp(.9,x,y),1-np.interp(.8,x,y)])
        for label,draw in draws.items():
            i=result.index[result.anio.eq(year)&result.grupo_edad.eq(label)][0]
            se=np.std(draw,axis=0,ddof=1)
            for metric,s in zip(['gini','top10','top20'],se):
                point=result.at[i,metric]
                result.loc[i,metric+'_se']=s
                result.loc[i,metric+'_ic95_inferior']=point-1.96*s
                result.loc[i,metric+'_ic95_superior']=point+1.96*s
            result.loc[i,'bootstrap_replicas']=B
    result.to_csv(out/'tables/h5_historico_concentracion.csv',index=False,float_format='%.10f')

def main(out):
    global OUT
    OUT=Path(out)
    p=pd.read_csv(OUT/'tables/historico_perfiles.csv')
    # H1 retains the established definition and source reconciliation.
    fig,axs=plt.subplots(1,3,figsize=(12,4.7))
    for ax,metric,title in zip(axs,['alimentos_fuera','recreacion_hospedaje','h1c'],['Alimentos fuera','Recreación, turismo y hospedaje','Suma: H1c']):
        d=p.loc[p.hipotesis.eq('H1')&p.indicador.eq(metric)]
        series(ax,d,groups=['18–29'],labels=True);style(ax);ax.set_ylim(0,15);ax.set_title(title)
    axs[0].set_ylabel('Proporción del gasto monetario (%)')
    save(fig,'h1_historico_comparacion','H1 · El nivel de 2024 es cercano al de 2004',
         'Hogares con jefatura de 18–29 años. Medias ponderadas e IC 95% con estratos y UPM.\nH1c es una canasta amplia comparable por finalidad; difiere de D2.')
    # Equipment comparison uses households consistently, excluding ENSAFI's person-level base.
    fig,axs=plt.subplots(2,2,figsize=(10,7.5))
    for ax,metric,title in zip(axs.flat,['celular','internet','tv_paga','auto'],['Teléfono celular','Internet','Televisión de paga','Automóvil del hogar']):
        d=p.loc[p.hipotesis.eq('H1b')&p.indicador.eq(metric)]
        series(ax,d);style(ax,[2004,2014,2024]);ax.set_ylim(0,105);ax.set_title(title);ax.set_ylabel('Hogares con el bien o servicio (%)')
    axs[0,0].legend(title='Edad de jefatura',frameon=False)
    save(fig,'h1b_historico_bienes','H1b · Equipamiento y servicios del hogar, 2004–2024',
         'ENIGH. Hogares clasificados por edad de jefatura; medias ponderadas e IC 95%.\nAutomóvil excluye camionetas. Disponibilidad no indica precio, antigüedad ni propiedad personal de la jefatura.')
    # H2 tests the within-income-rank young-old gap, including its within-wave covariance.
    h2=pd.read_csv(OUT/'tables/h2_historico_brechas.csv')
    fig,axs=plt.subplots(2,2,figsize=(10,7.5),sharey=True)
    limits=(min(-2,float(h2.ic95_inferior.min()*100)-1),max(8,float(h2.ic95_superior.max()*100)+1))
    for ax,year in zip(axs.flat,YEARS):
        d=h2.loc[h2.anio.eq(year)].sort_values('decil_ingreso_pc');v=d.estimacion.to_numpy()*100
        ax.errorbar(d.decil_ingreso_pc,v,yerr=np.vstack([v-d.ic95_inferior.to_numpy()*100,d.ic95_superior.to_numpy()*100-v]),fmt='o-',color='#00798c',capsize=3)
        ax.axhline(0,color='#555555',lw=1);ax.grid(axis='y',alpha=.18);ax.set_title(str(year),loc='left');ax.set_xticks(range(1,11))
        ax.set_xlabel('Decil de ingreso por persona de cada año');ax.set_ylabel('Brecha joven − 60+ (p.p.)');ax.set_ylim(*limits)
    save(fig,'h2_historico_brechas','H2 · Brecha de H1c entre jóvenes y mayores dentro de cada decil',
         'Jefatura de 18–29 frente a 60+ años. IC 95% condicionales a los cortes de ingreso estimados.\nIngreso corriente por persona; cada decil representa una posición relativa, no el mismo poder adquisitivo.')
    fig,axs=plt.subplots(1,2,figsize=(10,5))
    for ax,metric,title in zip(axs,['prestamo_recibido','retiro_ahorro'],['Recibió préstamos no hipotecarios','Retiró ahorros o inversiones']):
        d=p.loc[p.hipotesis.eq('H3')&p.indicador.eq(metric)];series(ax,d,labels=True);style(ax);ax.set_ylim(bottom=0);ax.set_title(title);ax.set_ylabel('Hogares con monto positivo (%)')
    axs[0].legend(title='Edad de jefatura',frameon=False)
    save(fig,'h3_historico_flujos','H3 · Préstamos recibidos y retiros declarados',
         'ENIGH. Flujos reportados durante el periodo de referencia; medias ponderadas e IC 95%.\nNo miden saldo de deuda, desahorro neto ni destino de los recursos a una compra específica.')
    joint=pd.read_csv(OUT/'tables/h3_historico_asociacion.csv')
    fig,ax=plt.subplots(figsize=(9,5))
    for flag,label,color,offset in [('sin_prestamo_ni_retiro','Sin préstamo ni retiro','#777777',-.5),('con_prestamo_o_retiro','Con préstamo o retiro','#00798c',.5)]:
        d=joint.loc[joint.grupo_edad.eq(flag)];v=d.estimacion.to_numpy()*100
        ax.errorbar(d.anio+offset,v,yerr=np.vstack([v-d.ic95_inferior.to_numpy()*100,d.ic95_superior.to_numpy()*100-v]),fmt='o',capsize=4,label=label,color=color)
    style(ax);ax.set_ylim(bottom=0);ax.set_ylabel('Proporción H1c (%)');ax.legend(frameon=False)
    save(fig,'h3_historico_gasto_flujos','H3 · Gasto y movimientos financieros en los mismos hogares',
         'Hogares con jefatura de 18–29 años; medias ponderadas e IC 95%.\nAsociación descriptiva sin ajustar ingreso o composición familiar; no demuestra financiamiento del consumo.')
    fig,axs=plt.subplots(1,3,figsize=(12,5))
    for ax,metric,title in zip(axs,['rentada','propia','prestada'],['Vivienda rentada','Vivienda propia, pagada o en pago','Vivienda prestada o como prestación']):
        d=p.loc[p.hipotesis.eq('H4_vivienda')&p.indicador.eq(metric)];series(ax,d,labels=True);style(ax);ax.set_ylim(0,100);ax.set_title(title,fontsize=11)
    axs[0].set_ylabel('Hogares principales (%)');axs[0].legend(title='Edad de jefatura',frameon=False)
    save(fig,'h4_historico_vivienda','H4 · Tenencia de vivienda a edades comparables',
         'Solo hogares principales en los cuatro años, con ponderadores de hogar e IC 95%.\nPropiedad en 1994 incluye terreno ejidal e irregular. La clasificación no mide asequibilidad de compra.')
    fig,axs=plt.subplots(1,2,figsize=(10,5))
    for ax,metric,title in zip(axs,['pension_en_hogar','programa_adultos_mayores'],['Ingreso por jubilación o pensión','Programa para adultos mayores']):
        d=p.loc[p.hipotesis.eq('H4_pension')&p.indicador.eq(metric)]
        series(ax,d,groups=['45–59','60+']);style(ax,YEARS if metric=='pension_en_hogar' else [2014,2024]);ax.set_ylim(0,100);ax.set_title(title);ax.set_ylabel('Hogares con ingreso positivo (%)')
    axs[0].legend(title='Edad de jefatura',frameon=False)
    save(fig,'h4_historico_pensiones','H4 · Recepción de ingresos para retiro y vejez',
         'Ingreso de cualquier integrante del hogar; IC 95%. No mide expectativas ni suficiencia de una pensión.\nPrograma: 65 y más (2014) / Pensión para el Bienestar (2024). Cambian elegibilidad y cobertura.\n1994: código general de pensión; desde 2004 se distinguen origen nacional y extranjero.')
    c=pd.read_csv(OUT/'tables/h5_historico_concentracion.csv')
    fig,axs=plt.subplots(1,2,figsize=(10,5))
    for ax,metric,title,scale in zip(axs,['gini','top10'],['Gini de montos de H1c','Gasto que concentra el 10% que más gasta'],[1,100]):
        for group in ['Total adulto','18–29']:
            d=c.loc[c.grupo_edad.eq(group)].sort_values('anio');v=d[metric].to_numpy()*scale
            ax.errorbar(d.anio,v,yerr=1.96*d[metric+'_se'].to_numpy()*scale,fmt='o-',capsize=3,label=group,color=COLORS[group])
        style(ax);ax.set_ylim(0,1 if metric=='gini' else 100);ax.set_title(title,fontsize=11)
    axs[0].legend(title='Universo',frameon=False);axs[1].set_ylabel('Porcentaje del monto total de H1c')
    save(fig,'h5_historico_concentracion','H5 · Concentración del gasto en la canasta histórica',
         'H1c: alimentos fuera + recreación, turismo y hospedaje; montos del hogar, con ceros incluidos.\nIC 95% normales: bootstrap reescalado por UPM dentro de estrato, 399 réplicas.\nOrden por gasto H1c, no por ingreso o riqueza. Las cantidades monetarias no se comparan entre años.')
    print('8 figuras generadas',flush=True)
