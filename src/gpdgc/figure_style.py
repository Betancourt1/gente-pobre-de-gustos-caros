"""Shared visual conventions for the project's statistical figures."""
from pathlib import Path
import math
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from . import config

INK, MUTED, GRID = '#243241', '#566474', '#e4e9ee'
AGES = [age.replace('-', '–') for age in config.AGE_LABELS]
COLORS = {age.replace('-', '–'): color for age, color in config.AGE_COLORS.items()}
COLORS.update({'Total adulto':'#555f6c', 'Sin préstamo ni retiro':'#8d99ae', 'Con préstamo o retiro':'#00798c'})
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'figure.facecolor':'white',
                     'axes.spines.top':False, 'axes.spines.right':False, 'axes.labelcolor':MUTED,
                     'xtick.color':MUTED, 'ytick.color':MUTED, 'text.color':INK, 'axes.titlecolor':INK})


def number(value, digits=1, signed=False):
    return format(value, f'{"+" if signed else ""}.{digits}f').replace('.', ',')

def clean_title(heading):
    return re.sub(r'^H\d+[a-z]?\s*[·:–—-]\s*', '', heading)

def title(fig, heading, subtitle):
    fig.text(.065, .967, clean_title(heading), fontsize=21, weight='bold', va='top')
    fig.text(.065, .967-.45/fig.get_figheight(), subtitle, fontsize=11, color=MUTED, va='top')

def axis_style(ax, percent=True, grid='y'):
    ax.spines[['top','right','left']].set_visible(False)
    ax.spines['bottom'].set_color('#cbd4dc')
    ax.tick_params(length=0, pad=7)
    ax.grid(axis=grid, color=GRID, linewidth=.8)
    ax.set_axisbelow(True)
    if percent:
        (ax.xaxis if grid=='x' else ax.yaxis).set_major_formatter(FuncFormatter(lambda x,p:f'{x:g}%'.replace('.',',')))
    else:
        (ax.xaxis if grid=='x' else ax.yaxis).set_major_formatter(FuncFormatter(lambda x,p:f'{x:g}'.replace('.',',')))

def bounds(df, key='estimacion', scale=100):
    suffix='' if key=='estimacion' else key+'_'
    v=df[key].to_numpy(float)*scale
    low=df[suffix+'ic95_inferior'].to_numpy(float)*scale
    high=df[suffix+'ic95_superior'].to_numpy(float)*scale
    return v,low,high

def intervals(ax, positions, values, low, high, *, horizontal=False, **kwargs):
    err=np.vstack([values-low, high-values])
    return ax.errorbar(values if horizontal else positions, positions if horizontal else values,
                       **({'xerr':err} if horizontal else {'yerr':err}), **kwargs)


def finish(fig, path, note='IC 95% individuales'):
    fig.text(.065,.12/fig.get_figheight(),note,va='bottom',fontsize=9.2,color=MUTED)
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return str(path)


def panel_bars(ax, data, heading, labels, colors, limit, key='estimacion', scale=100, percent=True, digits=1):
    v,lo,hi=bounds(data,key,scale);y=np.arange(len(data))
    bars=ax.barh(y,v,height=.56,color=colors,zorder=2)
    np.testing.assert_array_equal([b.get_width() for b in bars],v)
    intervals(ax,y,v,lo,hi,horizontal=True,fmt='none',ecolor=INK,capsize=4,elinewidth=1.4,zorder=3)
    ax.set_yticks(y,labels);ax.set_ylim(len(data)-.35,-.65)
    upper=float(hi.max());right=limit if upper<=limit else upper*1.1
    ax.set_xlim(min(0,float(lo.min())*1.1),right)
    ax.set_xticks([0,right/2,right]);axis_style(ax,percent,grid='x')
    ax.set_title(heading,loc='left',fontsize=12,weight='bold',pad=15)
    for i,value in enumerate(v):
        ax.text(1.035,i,number(value,digits)+('%' if percent else ''),transform=ax.get_yaxis_transform(),va='center',weight='bold',fontsize=10.5)

def age_bars(name,heading,subtitle,panels,note='IC 95% individuales',ncols=3,digits=1):
    rows=math.ceil(len(panels)/ncols)
    fig,axs=plt.subplots(rows,ncols,figsize=({1:9,2:13,3:15}[ncols],2.8*rows+1.9),squeeze=False)
    title(fig,heading,subtitle)
    for ax,(data,key,label,limit) in zip(axs.flat,panels):
        if data is None:
            ax.axis('off')
            continue
        data=data.copy();data['grupo_edad']=data.grupo_edad.str.replace('-','–')
        data=data.set_index('grupo_edad').loc[AGES].reset_index()
        panel_bars(ax,data,label,AGES,[COLORS[a] for a in AGES],limit,key=key,digits=digits)
    for ax in axs.flat[len(panels):]:ax.axis('off')
    height=fig.get_figheight()
    fig.subplots_adjust(left=.09,right=.93,top=1-1.4/height,bottom=.70/height,wspace=.65,hspace=.65)
    return finish(fig, name, note)

def time_panels(name,heading,subtitle,panels,note='IC 95% individuales',ncols=2):
    rows=math.ceil(len(panels)/ncols)
    fig,axs=plt.subplots(rows,ncols,figsize=(14 if ncols<3 else 16,3.1*rows+2.2),squeeze=False)
    title(fig,heading,subtitle)
    for ax,(data,label,groups,maximum,scale) in zip(axs.flat,panels):
        upper=float(data.ic95_superior.max()*scale)
        ymax=maximum if upper<=maximum else upper*1.13
        endpoints=[]
        for group in groups:
            d=data[data.grupo_edad.eq(group)].sort_values('anio');v,lo,hi=bounds(d,scale=scale)
            assert len(d)
            color=COLORS.get(group,'#00798c')
            intervals(ax,d.anio.to_numpy(),v,lo,hi,fmt='o-',color=color,capsize=4,lw=1.8,ms=5)
            if len(groups)==1:
                for x,y,upper in zip(d.anio,v,hi):
                    ax.annotate(number(y,1 if scale==100 else 2)+('%' if scale==100 else ''),(x,upper),xytext=(0,7),textcoords='offset points',ha='center',fontsize=10)
            else:endpoints.append([group,int(d.anio.iloc[-1]),v[-1],color])
        # Move labels, never data, when the final observations are close together.
        ordered=sorted(endpoints,key=lambda x:x[2]);last=-np.inf
        for group,x,y,color in ordered:
            label_y=max(y,last+ymax*.085);last=label_y
            ax.annotate(group+' · '+number(y,1 if scale==100 else 2)+('%' if scale==100 else ''),(x,y),xytext=(x+1.6,label_y),
                        fontsize=10,color=color,va='center',annotation_clip=False,
                        arrowprops={'arrowstyle':'-','color':color,'lw':.8})
        years=sorted(data.anio.unique());ax.set_xticks(years)
        ax.set_xlim(min(years)-2,max(years)+(10 if len(groups)>1 else 2));ax.set_ylim(0,ymax)
        ax.set_title(label,loc='left',fontsize=12,weight='bold',pad=14)
        axis_style(ax,scale==100);ax.yaxis.set_major_locator(MaxNLocator(5))
    for ax in axs.flat[len(panels):]:ax.axis('off')
    height=fig.get_figheight()
    fig.subplots_adjust(left=.085,right=.96,top=1-1.35/height,bottom=.72/height,wspace=.31,hspace=.63)
    return finish(fig, name, note)
