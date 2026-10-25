"""Informe autocontenido y resumen de la comparación histórica H1–H5."""
from pathlib import Path
import base64
import html
import json
import numpy as np
import pandas as pd

def main(out):
    OUT=Path(out)
    p=pd.read_csv(OUT/'tables/historico_perfiles.csv')
    c=pd.read_csv(OUT/'tables/h5_historico_concentracion.csv')
    h2=pd.read_csv(OUT/'tables/h2_historico_brechas.csv')

    def series(hyp,metric,group='18–29'):
        return p.loc[p.hipotesis.eq(hyp)&p.indicador.eq(metric)&p.grupo_edad.eq(group)].set_index('anio').estimacion*100

    summary=pd.DataFrame({
        'H1: proporción H1c, jefatura 18–29':series('H1','h1c'),
        'H3: recibió préstamo no hipotecario, jefatura 18–29':series('H3','prestamo_recibido'),
        'H3: retiró ahorro o inversiones, jefatura 18–29':series('H3','retiro_ahorro'),
        'H4: vivienda propia, hogar principal 18–29':series('H4_vivienda','propia'),
        'H4: vivienda rentada, hogar principal 18–29':series('H4_vivienda','rentada'),
        'H4: recibió pensión en el hogar, jefatura 60+':series('H4_pension','pension_en_hogar','60+'),
        'H5: concentración del top 10%, todas las jefaturas adultas':c.loc[c.grupo_edad.eq('Total adulto')].set_index('anio').top10*100,
    }).T
    summary.index.name='Indicador (porcentaje)'
    summary.to_csv(OUT/'tables/historico_resumen.csv',float_format='%.4f')

    mapping=pd.DataFrame([
        [1994,'P033','P031','P023','TENENCIA=5','TENENCIA=1,2,3,4','FOLIO termina en 0'],
        [2004,'P064','P062','P048,P049','TENENCIA12=1','TENENCIA12=4,5','FOLIO termina en 0'],
        [2014,'P053','P051','P032,P033','tenencia=1','tenencia=3,4','foliohog=1'],
        [2024,'P053','P051','P032,P033','tenencia=1','tenencia=3,4','foliohog=1'],
    ],columns=['anio','prestamos_ingresos','retiros_ingresos','pensiones_ingresos','vivienda_rentada','vivienda_propia','hogar_principal'])
    mapping.to_csv(OUT/'tables/historico_correspondencias.csv',index=False)

    def table(df):
        return '<div class="table-wrap">'+df.to_html(border=0,na_rep='—',float_format=lambda x:f'{x:.2f}',classes='data')+'</div>'

    def figure(file,caption):
        data=base64.b64encode((OUT/'figures'/(file+'.png')).read_bytes()).decode()
        return '<figure><img alt="'+html.escape(caption)+'" src="data:image/png;base64,'+data+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>'

    parts=['''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Comparación histórica ENIGH — H1 a H5</title><style>
    body{font:17px/1.6 system-ui,sans-serif;color:#222;background:#fff;margin:0}main{max-width:1120px;margin:auto;padding:40px 24px 80px}h1{font-size:36px;line-height:1.2;max-width:900px}h2{margin-top:54px;font-size:26px}h3{font-size:20px}p,li{max-width:900px}a{color:#006d80}nav{display:flex;gap:18px;flex-wrap:wrap;margin:25px 0}figure{margin:28px 0}img{display:block;width:100%;height:auto}figcaption,.note{font-size:14px;color:#555}table{border-collapse:collapse;font-size:14px;width:100%;font-variant-numeric:tabular-nums}td,th{padding:10px 12px;border-bottom:1px solid #ddd;text-align:right}th:first-child,td:first-child{text-align:left}.table-wrap{overflow:auto}details{margin:20px 0}code{font-size:14px}pre{overflow:auto;background:#f4f6f7;padding:16px} @media(max-width:600px){main{padding:22px 14px}h1{font-size:29px}figure{overflow:auto}figure img{min-width:760px}figcaption{position:sticky;left:0}table{min-width:650px}}@media print{nav{display:none}h2{break-before:page}figure{break-inside:avoid}}
    </style></head><body><main><p class="note">ENIGH 1994, 2004, 2014 y 2024 · Exploración calculada el 25 de octubre de 2026</p>
    <h1>El patrón de gasto por edad persiste; vivienda, financiamiento y concentración cuentan historias distintas</h1>
    <p>Se amplía la comparación a H1–H5 y al complemento de equipamiento H1b. El gasto se mide con <strong>H1c: alimentos fuera del hogar más recreación, turismo y hospedaje</strong>. Esta canasta histórica y su denominador difieren de D2. Los indicadores de deuda y retiro son aproximaciones a partes de H3 y H4: se explicita qué se observa en cada caso.</p>
    <nav><a href="#h1">H1</a><a href="#h1b">H1b</a><a href="#h2">H2</a><a href="#h3">H3</a><a href="#h4">H4</a><a href="#h5">H5</a><a href="#metodo">Método y fuentes</a></nav>
    <h2>Resultados comparables</h2><p>Todos los valores de esta tabla son porcentajes. “Joven” significa hogar con jefatura de 18–29 años; no todas las personas jóvenes del país.</p>''',table(summary),
    '''<h2 id="h1">H1. Gasto a la misma edad</h2><p>H1c representa 9.60%, 11.27%, 10.02% y 11.21% del gasto monetario de los hogares jóvenes. En 2024 supera a 1994 y 2014; frente a 2004 la diferencia es −0.06 puntos porcentuales (IC 95%: −1.05 a +0.93). No aparece un aumento continuo entre las ediciones analizadas. Estos cálculos reproducen los 48 perfiles comparables ya publicados en el proyecto.</p>''',
    figure('h1_historico_comparacion','H1: comparación a la misma edad y descomposición de la canasta. Los segmentos conectan solo cuatro observaciones; no representan datos anuales intermedios.'),
    '''<h2 id="h1b">H1b. Equipamiento y servicios, 2004–2024</h2><p>Entre hogares jóvenes, el celular pasa de 40.43% a 97.67% y el internet de 3.91% a 69.44%. El automóvil aumenta de 20.40% a 27.10%. La televisión de paga alcanza 31.28% en 2014 y baja a 26.22% en 2024. El acceso a tecnologías cambia; su presencia por sí sola no identifica gasto de lujo.</p><p>La unidad es siempre el hogar ENIGH. La comparación no mezcla estos porcentajes con los de personas residentes en viviendas de ENSAFI. Automóvil se limita al rubro automóvil, excluyendo camionetas. Para 1994 no se construyó una serie equivalente de estos cuatro bienes; no se imputan ceros.</p>''',
    figure('h1b_historico_bienes','H1b: disponibilidad del bien o servicio por edad de jefatura. No identifica quién lo compró, su precio ni su antigüedad.'),
    '''<h2 id="h2">H2. Brecha dentro de niveles de ingreso</h2><p>Las estimaciones de H1c son mayores para hogares de 18–29 que para los de 60+ en los diez deciles, en las cuatro ediciones. Los IC 95% de la brecha quedan por encima de cero en 8 de 10 deciles de 1994, 2004 y 2014; en 2024 ocurre en los diez. Son intervalos individuales, sin ajuste por pruebas múltiples.</p><p>Esto muestra que el patrón descriptivo por edad ya existía en otras épocas. Los deciles se construyen con ingreso corriente por integrante y ponderadores de hogares adultos dentro de cada año. El H2 original usaba ingreso equivalente y D2; esta extensión emplea otra medida explícita. Posiciones relativas de ingreso no igualan poder adquisitivo ni controlan conjuntamente empleo, composición familiar o urbanización.</p>''',
    figure('h2_historico_brechas','H2: diferencia de medias de proporciones H1c, joven menos 60+, con covarianza del diseño muestral dentro de cada ola.'),
    '''<h2 id="h3">H3. Movimientos financieros y gasto</h2><p>La proporción de hogares jóvenes que declara recibir préstamos no hipotecarios es 6.46%, 9.59%, 7.86% y 3.76%. La de retiros de ahorro o inversiones es 12.07%, 15.23%, 10.39% y 11.00%. El contraste 2024–2004 en préstamos es −5.83 p.p. (IC 95%: −7.68 a −3.98).</p><p>ENIGH sí permite observar estas entradas financieras y el gasto en el mismo hogar. En 2024, H1c es 11.12% entre hogares jóvenes con préstamos o retiros y 11.22% entre los demás: diferencia −0.10 p.p. (IC 95%: −1.18 a +0.98). Los cuatro intervalos de esta asociación incluyen cero. Esto no prueba igualdad ni identifica el destino del dinero.</p><p>Se mide un flujo reportado, no el saldo de deuda ni todos los productos de crédito. Retirar recursos no equivale a desahorro neto: puede coexistir con depósitos. No se atribuyen compras de H1c a crédito, ni se compara estrés financiero de ENSAFI con estas variables.</p>''',
    figure('h3_historico_flujos','H3: proporción de hogares con un monto positivo en las claves específicas de préstamos o retiros durante el periodo de referencia.'),
    figure('h3_historico_gasto_flujos','H3: asociación descriptiva de H1c con presencia de un préstamo o retiro. No ajusta ingreso ni otros factores.'),
    '''<h2 id="h4">H4. Vivienda y recepción de ingresos para la vejez</h2><p>Entre hogares jóvenes principales, la vivienda propia —pagada o en pago— pasa de 45.56% a 32.94% entre 1994 y 2024. La diferencia es −12.62 p.p. (IC 95%: −18.56 a −6.68). La vivienda rentada aumenta de 30.50% a 42.20%, un cambio de +11.70 p.p. (IC 95%: +4.72 a +18.68).</p><p>La comparación usa únicamente hogares principales en los cuatro años porque las olas antiguas no registraban tenencia para los adicionales. Al fijar la distribución de edades simples de los jóvenes en la de 2024, vivienda propia cambia de 46.99% a 32.94% y rentada de 29.81% a 42.20%. La mezcla de edades 18–29 no explica la dirección del cambio.</p><p>En 1994 propiedad incluye vivienda en terreno ejidal o de asentamiento irregular; es una categoría amplia de tenencia. Una proporción menor de propietarios entre quienes ya encabezan un hogar no mide por sí sola la probabilidad de emancipación, asequibilidad de compra ni el efecto causal del consumo.</p>''',
    figure('h4_historico_vivienda','H4: tenencia entre hogares principales, manteniendo comparable el universo por edad de jefatura.'),
    '''<p>En hogares con jefatura de 60+, la recepción de ingreso por jubilación o pensión de algún integrante aumenta de 22.65% en 1994 a 42.52% en 2024. Esta medida no incluye como pensión laboral los apoyos de programas para adultos mayores. Separadamente, la recepción del programa 65 y más en 2014 es 32.49%, y la del Programa Pensión para el Bienestar en 2024 es 63.37%; las reglas y la cobertura de esos programas cambiaron.</p><p>Son ingresos observados en hogares distintos, no las expectativas de retiro ni la pensión que obtendrán los jóvenes actuales. La presencia de una pensión no mide su suficiencia, y dos fuentes pueden coexistir en un mismo hogar.</p>''',
    figure('h4_historico_pensiones','H4: pensiones y programa para adultos mayores se muestran por separado; cualquiera de los integrantes puede ser el receptor.'),
    '''<p>Para alquiler se calculó además una sensibilidad de 2014–2024 en viviendas rentadas con un solo hogar. Entre jefaturas jóvenes, la mediana de renta mensual dividida entre ingreso corriente mensual del hogar es 16.54% y 13.20%, respectivamente. Son medianas descriptivas sin IC; el ingreso corriente incluye componentes no monetarios. Esta carga entre quienes efectivamente rentan no mide el precio de comprar ni las restricciones de quienes todavía no forman un hogar.</p>''',
    '''<h2 id="h5">H5. Concentración del gasto</h2><p>Entre todos los hogares con jefatura adulta, el 10% que más gasta en H1c concentra 67.49%, 58.12%, 59.11% y 52.47% del monto de esa canasta. Su Gini es 0.817, 0.752, 0.761 y 0.714. La concentración sigue siendo alta y su estimación es menor en 2024 que en las otras tres ediciones.</p><p>La proporción de hogares con monto H1c igual a cero baja de 41.32% en 1994 a 26.47% en 2024. La distribución incluye esos ceros y refleja tanto extensión del consumo como diferencias en montos. El ranking es por gasto H1c, no por ingreso o patrimonio. No se comparan niveles de pesos entre años; el Gini y las participaciones dentro de cada año son invariantes a un deflactor común.</p>''',
    figure('h5_historico_concentracion','H5: concentración de montos H1c, incluida incertidumbre del diseño mediante bootstrap de UPM dentro de estratos.'),
    '''<h2 id="metodo">Alcance, método y controles</h2><ul>
    <li>Cuatro cortes transversales independientes. Mantener la edad no separa efectos de cohorte y periodo. Los hogares con jefatura joven son una selección de los jóvenes de cada época.</li>
    <li>H1c conserva categorías amplias por finalidad, no productos idénticos. El denominador es el gasto corriente monetario oficial. Los cambios de clasificación y precios relativos no están incluidos en los intervalos muestrales.</li>
    <li>Se conserva la exclusión previa de jefaturas menores de 18; los 285 registros con edad cero de 1994 no se imputan. Las proporciones excluyen denominadores cero. H5 incluye hogares con gasto H1c cero.</li>
    <li>Medias e incidencias: linealización de Taylor con estratos y UPM completos, aproximación con reemplazo y sin corrección por población finita. Las diferencias dentro de una ola conservan la covarianza entre dominios. Contrastes entre olas asumen independencia.</li>
    <li>H2 trata los cortes estimados de ingreso como fijos. La sensibilidad por edad trata los pesos de referencia de 2024 como fijos. Los IC son individuales al 95%, sin ajuste por comparaciones múltiples.</li>
    <li>H5: bootstrap reescalado, 399 réplicas, semilla 20261025. En cada estrato con m UPM se extraen m−1 UPM con reemplazo y se reescala por m/(m−1). IC normales alrededor de la estimación original. Es una aproximación exploratoria sin recalibrar factores.</li>
    <li>Los movimientos financieros se reconstruyen desde ingresos, con claves explícitas. Se concilian préstamos y retiros con los concentrados de 2004, 2014 y 2024. Las pensiones de 2014/2024 también concilian.</li>
    <li>JUBILA 2004 mezcla pensiones e indemnizaciones P048–P052. Se conservan solo P048 y P049 para la serie. Incluso reconstruyendo el agregado amplio queda una discrepancia de fuente en un hogar: 10,500 frente a 21,000. Ambos montos son positivos, por lo que esa discrepancia de monto no cambia la incidencia; se registra en historico_validacion.csv y no se altera el dato fuente.</li>
    <li>Se verificó la reproducción de los 48 perfiles H1 previos, los cruces de llaves, dominios, conteos y límites de los indicadores. Las ocho gráficas se inspeccionaron visualmente.</li>
    </ul><h3>Claves empleadas en las extensiones</h3>''',table(mapping.set_index('anio')),
    '''<h3>Fuentes y lectura para verificar las correspondencias</h3><ul>
    <li>INEGI, <a href="https://www.inegi.org.mx/contenidos/programas/enigh/tradicional/1994/doc/catalogo94.pdf">Catálogo ENIGH 1994</a>, páginas PDF 57–58: P023, P031 y P033. La construcción de vivienda 1994 identifica rentada como 5 y propiedad como 1–4.</li>
    <li>INEGI, <a href="https://www.inegi.org.mx/contenidos/programas/enigh/tradicional/2004/doc/catalogo04.pdf">Catálogo ENIGH 2004</a>, páginas PDF 1 y 3: folio y tenencia; 20: equipamiento; 51: pensiones y movimientos financieros.</li>
    <li>INEGI, <a href="https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/nueva_estruc/702825070373.pdf">Descripción de la base ENIGH 2014</a>, variables tenencia, renta, foliohog, jubilacion, retiro_inv y prestamos; catálogo P032, P033, P044, P051 y P053.</li>
    <li>INEGI, <a href="https://www.inegi.org.mx/contenidos/programas/enigh/nc/2024/microdatos/889463924494.pdf">Descripción de la base ENIGH 2024</a>, las mismas variables y catálogo P032, P033, P104, P051 y P053.</li>
    </ul><h3>Archivos y reproducción</h3><p>Las ocho gráficas están en reports/figures/, los diez CSV agregados en reports/tables/ y el registro de fuentes en reports/historico_metodologia.json. El comando está en scripts/compare_all_history.py. No contiene identificadores de hogares ni microdatos. Los CSV de proporciones e incidencias usan escala 0–1; historico_resumen.csv usa porcentajes y historico_contrastes.csv puntos porcentuales. Los tamaños n son observaciones muestrales; hogares_expandidos es la suma de factores.</p>
    <p>Ejecuta <code>python scripts/compare_all_history.py</code> desde la raíz del repositorio. El comando lee las cuatro olas desde data/raw/enigh, recalcula las tablas y sus intervalos, dibuja las ocho figuras y reconstruye este informe. Admite <code>--raw</code> y <code>--output</code> para directorios alternativos. No guarda cachés de microdatos ni modifica los resultados originales de D2 o ENSAFI.</p>
    <p class="note">Esta ampliación calcula indicadores históricos para cada hipótesis y señala los componentes que siguen sin identificarse: financiamiento de compras específicas, desahorro neto, suficiencia pensionaria y juicios sobre las quejas de las personas.</p>
    </main></body></html>''']
    (OUT/'historico_hipotesis.html').write_text(''.join(parts),encoding='utf-8')
