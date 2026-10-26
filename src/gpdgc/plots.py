"""Figures for the original ENIGH and ENSAFI analysis."""
from . import config
from .figure_style import (plt, MaxNLocator, AGES, COLORS, MUTED, number,
                           title, axis_style, bounds, intervals, finish, age_bars)


def fig_h1_composicion(profile):
    main=age_bars(config.FIGURES / 'h1_composicion_por_edad.png','Gasto por edad de la jefatura',
             'Porcentaje del consumo monetario seleccionado · ENIGH 2024',
             [(profile,'share_d1','D1 · Canasta amplia',60),
              (profile,'share_d2','D2 · Gasto visible',20),
              (profile,'share_d3','D3 · Alcohol, tabaco y narcóticos',1)],
             'IC 95% individuales · Canastas superpuestas · Escalas por panel',digits=2)
    age_bars(config.FIGURES / 'h1_componentes_d2.png','Componentes del gasto visible',
             'D2 / consumo monetario seleccionado (%) · Edad de la jefatura · ENIGH 2024',
             [(profile,k,l,m) for k,l,m in [
                 ('share_d2_restaurantes','Restaurantes y hoteles',15),
                 ('share_d2_recreacion','Recreación y turismo',5),
                 ('share_d2_alcohol','Alcohol y tabaco',1),
                 ('share_d2_personal','Accesorios seleccionados',.15),
                 ('share_d2_streaming','Bienes y servicios digitales',.8),
                 ('share_d2_auto','Automóvil nuevo',.6)]],
             'IC 95% individuales · Escalas por panel',digits=2)
    return main


def fig_h1b_bienes(assets):
    return age_bars(config.FIGURES / 'h1b_bienes_ensafi.png','Bienes y servicios en la vivienda',
             'Porcentaje de personas adultas, por edad · ENSAFI 2023',
             [(assets,k,k,100) for k in ['Auto','Celular','Internet','TV de paga','Streaming']])


def fig_h3_finanzas(fin):
    return age_bars(config.FIGURES / 'h3_finanzas_ensafi.png','Situación financiera y estrés por edad',
             'Porcentaje de personas adultas · ENSAFI 2023',
             [(fin,k,l,60) for k,l in [('pct_afore','Tiene AFORE'),('pct_reporta_ahorro_cuentas','Reporta ahorro en cuentas'),
              ('pct_deuda_credito','Deuda o productos de crédito'),('pct_ingreso_insuficiente','Reporta ingreso insuficiente'),
              ('pct_alto_estres','Alto estrés financiero'),('pct_gasto_supera_ingreso_laboral','Gasto supera ingreso laboral¹')]],
             'IC 95% individuales · ¹ Solo casos con gasto e ingreso comparables')


def fig_h4_pensiones_vivienda(exp,housing):
    main=age_bars(config.FIGURES / 'h4_pensiones_vivienda.png','Fuentes de ingreso previstas para la vejez',
             'Porcentaje de personas adultas, por edad · ENSAFI 2023',
             [(exp,k,l,100) for k,l in [('Apoyo de gobierno','Apoyo del gobierno'),('Pensión, jubilación o AFORE','Pensión, jubilación o AFORE'),
              ('Seguir trabajando','Seguir trabajando'),('Familia','Apoyo de la familia'),('Inversiones','Ingresos de inversiones')]],
             'IC 95% individuales · Respuestas no excluyentes')
    age_bars(config.FIGURES / 'h4_vivienda.png','Renta de vivienda por edad',
             'Hogares por edad de la jefatura · ENIGH 2024',
             [(housing,'pct_rentados','Hogares que rentan (%)',50),
              (housing,'carga_renta_mediana','Renta / ingreso: mediana (%)',20)],
             'IC 95% individuales · Renta / ingreso: solo hogares rentadores',ncols=2)
    return main


def fig_h2_decil(dec_share,dec_level):
    paths=[]
    for d,key,heading,subtitle,scale,name in [
        (dec_share,'share_d2','Proporción del gasto visible según el ingreso',
         'D2 / consumo monetario seleccionado (%) · Edad de la jefatura · ENIGH 2024',100,'h2_brecha_por_decil.png'),
        (dec_level,'gasto_d2_eq','Monto del gasto visible según el ingreso',
         'D2 por adulto equivalente · MXN trimestrales · Edad de la jefatura · ENIGH 2024',1,'h2_monto_por_decil.png')]:
        fig,axs=plt.subplots(2,2,figsize=(12,7.6));title(fig,heading,subtitle)
        maximum=float(d[key+'_ic95_superior'].max()*scale)*1.15
        for ax,age in zip(axs.flat,AGES):
            sub=d[d.grupo_edad.str.replace('-','–').eq(age)].sort_values('decil_ing');v,lo,hi=bounds(sub,key,scale)
            intervals(ax,sub.decil_ing.to_numpy(),v,lo,hi,fmt='o-',color=COLORS[age],capsize=3,lw=1.5,ms=4)
            ax.set_title(age+' años',loc='left',weight='bold',fontsize=13)
            ax.set_xticks(range(1,11));ax.set_xlim(.5,10.7);ax.set_ylim(0,maximum)
            axis_style(ax,scale==100);ax.yaxis.set_major_locator(MaxNLocator(4));ax.tick_params(labelsize=9)
            ax.annotate(number(v[-1],1 if scale==100 else 0)+('%' if scale==100 else ''),(10,hi[-1]),
                        xytext=(-4,7),textcoords='offset points',ha='right',fontsize=10)
        fig.subplots_adjust(left=.08,right=.96,top=.81,bottom=.15,wspace=.25,hspace=.42)
        fig.text(.52,.075,'Decil de ingreso equivalente · 1: menor ingreso; 10: mayor ingreso',ha='center',fontsize=10,color=MUTED)
        paths.append(finish(fig,config.FIGURES / name))
    return paths[0]


def fig_h5_concentracion(conc):
    lorenz=conc['lorenz_precision']
    fig=plt.figure(figsize=(12,7));title(fig,'Concentración del gasto visible',
             'D2 · Hogares con jefatura adulta · ENIGH 2024')
    ax=fig.add_axes([.09,.16,.50,.62]);x=lorenz.proporcion_acumulada_hogares.to_numpy()*100;y=lorenz.proporcion_acumulada_gasto_d2.to_numpy()*100
    ax.fill_between(x,lorenz.ic95_inferior.to_numpy()*100,lorenz.ic95_superior.to_numpy()*100,color='#d1495b',alpha=.18)
    ax.plot(x,y,color='#d1495b',lw=2,label='Gasto observado');ax.plot([0,100],[0,100],ls='--',color=MUTED,lw=1.2,label='Igualdad perfecta')
    ax.set_xlim(0,100);ax.set_ylim(0,100);axis_style(ax)
    ax.set_xlabel('Hogares acumulados, de menor a mayor gasto (%)');ax.set_ylabel('Gasto D2 acumulado (%)')
    ax.legend(frameon=False,loc='upper left')
    for j,(key,label,scale) in enumerate([('gini','Gini',1),('top10','10% que más gasta',100),('top20','20% que más gasta',100)]):
        r=conc['precision'][key];suffix='%' if scale==100 else '';y=.73-j*.19
        fig.text(.68,y,label,fontsize=11)
        fig.text(.68,y-.06,number(r['estimacion']*scale,2)+suffix,fontsize=20,weight='bold')
        fig.text(.68,y-.105,f'IC 95%: {number(r["ic95_inferior"]*scale,2)}–{number(r["ic95_superior"]*scale,2)}'+suffix,fontsize=10,color=MUTED)
    main=finish(fig,config.FIGURES / 'h5_concentracion.png','Banda: IC 95% puntual')
    age_bars(config.FIGURES / 'h5_distribucion_por_edad.png','Distribución del gasto visible por edad',
             'Porcentaje del gasto nacional en D2 · Edad de la jefatura · ENIGH 2024',
             [(conc['by_age'],'share_gasto_d2_total','',40)],ncols=1)
    return main
