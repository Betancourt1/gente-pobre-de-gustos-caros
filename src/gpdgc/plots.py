"""Original figures with survey confidence intervals and separate contrast reports."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
from . import config


def _style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
        'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})


def _save(fig,name,source):
    fig.text(.01,-.015,source+'\nBarras: IC 95% individuales con diseño muestral. Diferencias: contrastes_categorias.csv y significancia.html; decisión con p de Holm < 0.05.',
             ha='left',va='top',fontsize=8,color='#444444')
    path=config.FIGURES/name
    fig.savefig(path,dpi=175,bbox_inches='tight');plt.close(fig)
    return str(path)


def errors(table,col):
    v=table[col].to_numpy(float)
    return np.vstack([v-table[col+'_ic95_inferior'].to_numpy(float),table[col+'_ic95_superior'].to_numpy(float)-v])


def grouped(ax,table,metrics,title):
    x=np.arange(len(metrics))
    for i,age in enumerate(config.AGE_LABELS):
        row=table.loc[table.grupo_edad.eq(age)].iloc[0]
        v=np.array([row[k] for k,_ in metrics],float)
        err=np.array([[row[k]-row[k+'_ic95_inferior'] for k,_ in metrics],
                      [row[k+'_ic95_superior']-row[k] for k,_ in metrics]],float)
        ax.errorbar(x+(i-1.5)*.16,v,yerr=err,fmt='o',capsize=3,color=config.AGE_COLORS[age],label=age)
    ax.set_xticks(x,[label for _,label in metrics]);ax.set_title(title)
    ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylim(bottom=0)
    ax.grid(axis='y',alpha=.2);ax.legend(title='Edad',fontsize=8,frameon=False,ncol=2)


def age_series(ax,table,col,title):
    x=np.arange(len(table));v=table[col].to_numpy(float)
    ax.errorbar(x,v,yerr=errors(table,col),fmt='o',capsize=4,color='#00798c')
    ax.set_xticks(x,table.grupo_edad);ax.set_title(title);ax.grid(axis='y',alpha=.2)
    ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylim(bottom=0)
    for i,(y,upper) in enumerate(zip(v,table[col+'_ic95_superior'])):
        ax.annotate(f'{y:.1%}',(i,upper),xytext=(0,6),textcoords='offset points',ha='center',fontsize=9)
    ax.margins(y=.18)


def fig_h1_composicion(profile):
    _style();fig,axs=plt.subplots(1,2,figsize=(15,5.5),gridspec_kw={'width_ratios':[1,1.7]})
    grouped(axs[0],profile,[('share_d1','D1'),('share_d2','D2'),('share_d3','D3')],'Participación de las canastas')
    grouped(axs[1],profile,[(f'share_d2_{k}',v) for k,v in [
        ('alcohol','Alcohol y\ntabaco'),('restaurantes','Restaurantes\ny hoteles'),('recreacion','Recreación\ny turismo'),
        ('personal','Accesorios'),('streaming','Streaming /\nTV de paga'),('auto','Automóvil\nnuevo')]],'Componentes de D2, con incertidumbre propia')
    axs[0].set_ylabel('Proporción del consumo monetario analizado')
    fig.suptitle('H1 · Gasto por edad de la jefatura e IC 95%',fontsize=16);fig.tight_layout()
    return _save(fig,'h1_composicion_por_edad.png',config.SOURCE_ENIGH)


def fig_h2_decil(dec_share,dec_level):
    _style();fig,axs=plt.subplots(1,2,figsize=(14,5.5))
    for ax,data,col,title in zip(axs,[dec_share,dec_level],['share_d2','gasto_d2_eq'],['Participación D2','Monto D2 por adulto equivalente']):
        for i,age in enumerate(config.AGE_LABELS):
            d=data.loc[data.grupo_edad.eq(age)].sort_values('decil_ing')
            ax.errorbar(d.decil_ing+(i-1.5)*.1,d[col],yerr=errors(d,col),fmt='o-',lw=1,capsize=2,color=config.AGE_COLORS[age],label=age)
        ax.set_xticks(range(1,11));ax.set_xlabel('Decil de ingreso equivalente');ax.set_title(title)
        ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,fontsize=8);ax.set_ylim(bottom=0)
    axs[0].yaxis.set_major_formatter(PercentFormatter(1));axs[1].set_ylabel('MXN trimestrales')
    fig.suptitle('H2 · Gasto por edad e ingreso, con IC 95%',fontsize=16);fig.tight_layout()
    return _save(fig,'h2_brecha_por_decil.png',config.SOURCE_ENIGH+' Cortes de ingreso tratados como fijos.')


def fig_h3_finanzas(fin):
    _style();fig,axs=plt.subplots(1,2,figsize=(14,5.5))
    grouped(axs[0],fin,[('pct_afore','AFORE'),('pct_reporta_ahorro_cuentas','Reporta ahorro\nen cuentas'),
        ('pct_deuda_credito','Deuda o productos\nde crédito'),('pct_ingreso_insuficiente','Ingreso\ninsuficiente')],'Indicadores financieros')
    grouped(axs[1],fin,[('pct_alto_estres','Alto estrés'),('pct_gasto_supera_ingreso_laboral','Gasto > ingreso laboral\n(casos comparables)')],'Estrés y comparación de gasto e ingreso')
    fig.suptitle('H3 · Indicadores por edad e IC 95%',fontsize=16);fig.tight_layout()
    return _save(fig,'h3_finanzas_ensafi.png',config.SOURCE_ENSAFI+' No identifica financiamiento de compras.')


def fig_h4_pensiones_vivienda(exp,housing):
    _style();fig,axs=plt.subplots(1,3,figsize=(17,5.7),gridspec_kw={'width_ratios':[1.8,1,1]})
    grouped(axs[0],exp,[('Apoyo de gobierno','Gobierno'),('Pensión, jubilación o AFORE','Pensión /\nAFORE'),
        ('Seguir trabajando','Trabajo'),('Familia','Familia'),('Inversiones','Inversiones')],'Fuentes previstas para la vejez')
    age_series(axs[1],housing,'pct_rentados','Hogares que rentan')
    age_series(axs[2],housing,'carga_renta_mediana','Renta / ingreso: mediana')
    fig.suptitle('H4 · Expectativas y vivienda por edad, con IC 95%',fontsize=16);fig.tight_layout()
    return _save(fig,'h4_pensiones_vivienda.png',config.SOURCE_ENSAFI+' / ENIGH 2024. Mediana: bootstrap estratificado por UPM.')


def fig_h5_concentracion(conc):
    _style();fig,axs=plt.subplots(1,2,figsize=(14,5.5))
    d=conc['lorenz_precision'];x=d.proporcion_acumulada_hogares.to_numpy()*100
    axs[0].fill_between(x,d.ic95_inferior.to_numpy()*100,d.ic95_superior.to_numpy()*100,color='#d1495b',alpha=.25,label='IC 95% puntual')
    axs[0].plot(x,d.proporcion_acumulada_gasto_d2*100,color='#d1495b',label='Lorenz D2')
    axs[0].plot([0,100],[0,100],ls='--',color='#777777',label='Igualdad perfecta')
    axs[0].set_xlabel('Hogares acumulados (%)');axs[0].set_ylabel('Gasto D2 acumulado (%)');axs[0].legend(frameon=False)
    text=[]
    for key,label,scale in [('gini','Gini',1),('top10','Top 10%',100),('top20','Top 20%',100)]:
        e=conc['precision'][key]
        text.append(f"{label}: {e['estimacion']*scale:.2f} [{e['ic95_inferior']*scale:.2f}, {e['ic95_superior']*scale:.2f}]")
    axs[0].text(.05,.66,'\n'.join(text),transform=axs[0].transAxes,fontsize=10)
    axs[0].set_title('Concentración e incertidumbre del gasto')
    age_series(axs[1],conc['by_age'],'share_gasto_d2_total','Reparto del gasto nacional por edad')
    fig.suptitle('H5 · Concentración de D2 e IC 95%',fontsize=16);fig.tight_layout()
    return _save(fig,'h5_concentracion.png',config.SOURCE_ENIGH+' Lorenz y concentración: bootstrap de UPM; bandas puntuales, no simultáneas.')


def fig_h1b_bienes(assets):
    _style();fig,ax=plt.subplots(figsize=(11,5.5))
    grouped(ax,assets,[(x,x) for x in ['Auto','Celular','Internet','TV de paga','Streaming']],'Bienes y servicios de la vivienda de residencia')
    ax.set_ylabel('Proporción de personas adultas');fig.suptitle('H1b · Equipamiento por edad e IC 95%',fontsize=16);fig.tight_layout()
    return _save(fig,'h1b_bienes_ensafi.png',config.SOURCE_ENSAFI)
