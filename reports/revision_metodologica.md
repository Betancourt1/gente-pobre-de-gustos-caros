# Revisión metodológica y correcciones — 23 de octubre de 2026

## Alcance

Esta revisión sustituye los resultados publicados en el commit `a93b3f4`. Aquella versión era reproducible, pero contenía errores de integración y definición de indicadores. Las cifras antiguas no deben citarse como resultados vigentes. La bibliografía y los microdatos de origen se conservaron.

El proceso sigue siendo descriptivo y transversal. Corregir su implementación no identifica efectos causales, diferencias entre generaciones a la misma edad ni la fuente de financiamiento de cada compra.

## Qué se corrigió

### 1. Identificadores y cobertura de los cruces

`concentradohogar` se leía infiriendo tipos numéricos: los folios que empezaban por cero perdían ese carácter. Los gastos se leían como texto y mantenían los diez caracteres. Antes de la corrección, 29,043 hogares no encontraban sus gastos y el programa los convertía en ceros. Al preservar los identificadores, ese número bajaba a 48 antes de incorporar `gastospersona`.

Todos los CSV se leen ahora como texto; cada cargador convierte las magnitudes numéricas. Se comprueba la cardinalidad de las uniones, la correspondencia de viviendas y la igualdad del conteo de integrantes con `tot_integ`. Los gastos se cruzan mediante una unión externa: si una clave de gasto no existe en `concentradohogar`, el proceso se detiene. Un hogar sin renglones de consumo seleccionado se distingue mediante `tiene_registros_gasto` antes de asignarle cero.

### 2. Consumo del hogar y gastos personales

Se concatenan `gastoshogar` y `gastospersona`, se selecciona `tipo_gasto == G1` y se agregan los registros por `folioviv` y `foliohog`. No se deduplican compras por clave: varias compras legítimas pueden compartirla. Se excluyen capítulo 17 y regalos T9 de la canasta de consumo.

El archivo omitido contiene 268,499 renglones G1 de consumo de 46,256 hogares en los datos examinados. Su gasto equivale aproximadamente al 7.2% del consumo combinado ponderado, antes del filtro de edad del jefe. Se concentra principalmente en transporte y educación. La anterior explicación de la diferencia respecto a `gasto_mon` como producto únicamente de transferencias y regalos era insuficiente.

La caché nueva es `data/processed/gastos_consumo_g1_v2.parquet`. La anterior no se reutiliza. Si cambian las fechas de modificación de las fuentes, `io.py` o `taxonomy.py`, se reconstruye; `--force-gastos` fuerza la reconstrucción sin depender de esas fechas. Las cachés siguen fuera de Git.

### 3. Escala de equivalencia y universo de hogares

La variable ENIGH `menores` cuenta integrantes menores de 12 años. La escala OCDE modificada exige menores de 14. Se cuenta ahora ese grupo desde `poblacion`, usando los integrantes cuyo parentesco empieza por 1, 2, 3, 5 o 6, igual que la construcción de `tot_integ`. Se excluyen trabajadores domésticos, sus familiares y huéspedes.

La fórmula es `1 + 0.5 × (personas de 14 o más − 1) + 0.3 × menores de 14`. Hay 10,727 hogares de la fuente con integrantes de 12 o 13 años. La corrección afecta ingreso y gasto equivalentes y puede cambiar la pertenencia a deciles.

Las 34 jefaturas menores de 18 años se excluyen de todo el análisis: perfiles, deciles, vivienda y concentración nacional comparten un universo de 91,380 hogares. El archivo original contiene 91,414. Las personas jóvenes que viven con un jefe mayor no se reclasifican como hogares jóvenes.

### 4. Periodicidad, alcance del ingreso y datos faltantes en ENSAFI

`P5_19` es ingreso por trabajo con periodo indicado en `P5_19A`: semana, quincena, mes o año. Se comparaba directamente con `P5_21`, que es mensual. Se utiliza ahora `INGRESO_M`, el ingreso mensual por trabajo construido por INEGI.

Se elimina `tasa_ahorro`: restar gasto al ingreso laboral no mide ahorro total, pues faltan otras fuentes de ingreso. El indicador nuevo es `pct_gasto_supera_ingreso_laboral`, calculado únicamente entre personas con ingreso laboral mensual y gasto mensual conocidos y no negativos. Se incluyen ceros conocidos: ingreso cero y gasto positivo produce una comparación verdadera. Un salto de cuestionario o un monto desconocido nunca se convierte en ingreso cero ni en respuesta negativa.

Se excluyen de la comparación los códigos abiertos de 98,000 y más en `P5_19` o `P5_21`: no son importes exactos. Las medianas monetarias también excluyen esos límites abiertos. Se publican `n_comparables_ingreso_gasto` y `pct_comparables_ingreso_gasto`, esta última ponderada respecto a todos los adultos del grupo. El porcentaje de gasto mayor al ingreso tiene un denominador distinto al de los indicadores de AFORE, estrés y crédito.

`weighted_share` excluye respuestas desconocidas del denominador. Para P6.3 y P6.7 se conserva deliberadamente una incidencia sobre todos los adultos: “reporta ahorro en cuentas” y “reporta atraso”, respectivamente. Los saltos por no tener las cuentas o créditos preguntados se codifican como ausencia de ese reporte; no se presentan como tasas entre cuentahabientes o deudores. P6.3 no mide ahorro informal.

Se renombra `pct_deuda` a `pct_deuda_credito`: P6.5 registra deuda, mientras que P6.6 incluye tenencia de tarjetas de crédito, que por sí sola no prueba un saldo pendiente. Tener AFORE tampoco equivale a cotizar actualmente, a tener derecho a pensión ni a contar con ahorro suficiente.

### 5. Definición explícita de accesorios D2

Se sustituyen los prefijos amplios `1321` y `1329` por seis claves:

| Clave | Descripción del catálogo |
|---|---|
| 132111 | Joyería de piedras y metales no preciosos: bisutería |
| 132112 | Relojes de pulso |
| 132911 | Bolsas |
| 132912 | Carteras y monederos |
| 132913 | Portafolios |
| 132915 | Maletas para viaje |

Quedan fuera de D2 los relojes de pared, mochilas y loncheras, artículos para bebé, paraguas, artículos funerarios y el resto de `1329` no listado. Siguen dentro del consumo total y, cuando corresponde, de D1. Esta selección es una decisión analítica que aproxima accesorios visibles; no demuestra que toda compra seleccionada sea un lujo.

Se mantienen los capítulos 02, 09 y 11, el automóvil nuevo `071110` y los códigos digitales `081404`, `083921`–`083924`. `081404` corresponde a equipos de transmisión/decodificadores, y `083923` también comprende alquileres o suscripciones de soportes y software. Los rótulos se interpretan como agrupaciones analíticas, no como categorías puras de streaming. D1 incluye transporte, comunicaciones y seguros que pueden ser necesarios; se conserva como sensibilidad amplia, no como medición literal de derroche.

### 6. Cuantiles, empates y concentración

Los cuantiles usan la inversa de la distribución empírica ponderada: el primer valor cuyo peso acumulado alcanza el umbral. No hay interpolación de ingresos.

Los deciles se asignan mediante los nueve cortes ponderados. Valores iguales permanecen en el mismo grupo, incluso si esto deja deciles vacíos; los datos sin ingreso o peso válido no reciben decil. Esta regla evita el error de límites duplicados de `pd.cut` y no introduce un orden arbitrario entre empates.

Los nueve niveles se construyen como `i / 10`, evitando acumulación de error decimal con `np.arange`. En una muestra de diez ingresos distintos y pesos iguales, la versión anterior asignaba dos ingresos a los deciles 3 y 7 y dejaba vacíos el 4 y el 8. La prueba de regresión exige un ingreso por decil en ese caso.

`top_share` usa solo la fracción del peso del registro que alcanza el corte. Antes, con dos hogares de gasto y peso iguales, el “top 10%” devolvía 50%; ahora devuelve 10%. En la base completa, el efecto aislado de este ajuste es pequeño frente al error de identificadores. El orden es por gasto en la canasta, no por riqueza ni ingreso.

### 7. Interpretación, rótulos y compatibilidad

H3 pasa de “no se sostiene” a “no identificada con estas fuentes”: comparar edades en dos encuestas separadas no vincula compras concretas con deuda o desahorro. H4 describe tenencia y expectativas; no mide quejas, suficiencia pensionaria ni deterioro entre cohortes. H5 no llama “acomodados” a quienes más gastan sin verificar su ingreso o patrimonio. H1b mide residencia en viviendas equipadas, no propiedad personal ni adquisición de autos nuevos.

Los títulos de figuras dejan de incorporar veredictos o porcentajes fijos. Las columnas ENSAFI anteriores `pct_ahorro`, `pct_deuda`, `pct_atraso`, `pct_gasta_mas`, `tasa_ahorro_mediana` e `ingreso_mensual_mediano` se reemplazan por nombres que explicitan su alcance. Quienes consuman esos CSV deben actualizar sus referencias. Se conserva el nombre de los archivos de salida.

## Validación reproducible

### Resultados antes y después

Los valores de “antes” proceden de las tablas del commit `a93b3f4`; “después” corresponde a la reconstrucción completa con las correcciones descritas, incluido el universo adulto y la selección restringida de accesorios. No representan el efecto aislado de una sola corrección.

| Indicador | Antes | Después |
|---|---:|---:|
| Hogares usados en concentración nacional | 91,414 | 91,380 |
| D2, jefatura 18–29 | 18.75% | 17.01% |
| D2, jefatura 60+ | 13.27% | 12.76% |
| Brecha D2 joven − 60+ | 5.48 p.p. | 4.25 p.p. |
| D2 por adulto equivalente, 18–29, pesos trimestrales | 4,578 | 5,959 |
| D2 por adulto equivalente, 60+, pesos trimestrales | 2,564 | 3,681 |
| Gini D2 | 0.7306 | 0.6508 |
| Top 10% por gasto D2 | 54.30% | 47.98% |
| Top 20% por gasto D2 | 73.75% | 66.21% |
| Mediana de consumo seleccionado / gasto monetario oficial | 87.4% | 99.76% |
| Mediana publicada como ingreso mensual, 18–29 | $2,200, mezclaba periodos | $6,450 de ingreso laboral mensual conocido y no topado |
| Indicador de gasto mayor al ingreso, 18–29 | 33.2%, inválido por periodos y denominador | 17.8% frente al ingreso **laboral mensual**, entre 2,942 casos comparables |
| Cobertura ponderada de esa comparación, 18–29 | No se publicaba | 64.0% del grupo |

La última comparación no conserva el mismo concepto ni el mismo denominador; no debe interpretarse como una caída económica del desahorro. Cambió la medición. En 60+, el nuevo indicador es 34.5% entre casos comparables, con cobertura ponderada de 38.3%: precisamente por ello no se presenta como estimación del desahorro de todos los adultos mayores.

Las diferencias de vivienda y expectativas permanecen, pero sus interpretaciones se acotan. La brecha D2 sigue siendo positiva en los diez deciles; su máximo está ahora en el decil 5, por lo que se retiró la afirmación de que aumenta hacia la parte alta.

### Comandos y controles

```bash
python -m unittest discover -s tests -v
python scripts/make_figures.py --force-gastos
```

Las pruebas usan CSV sintéticos, de modo que funcionan sin los microdatos. Cubren clasificación por claves reales, exclusión de accesorios no seleccionados, ceros iniciales, agregación de gastos personales, composición familiar, filtros de edad, uniones duplicadas o huérfanas, periodicidad, ceros conocidos, datos desconocidos, límites abiertos, cuantiles, empates y fraccionamiento del top ponderado.

Resultado de la ejecución: **13 pruebas aprobadas**. La reconstrucción forzada generó las trece tablas y las seis figuras, con 91,380 hogares y 20,448 personas. Hay 91,333 hogares con consumo seleccionado positivo y 47 sin registros seleccionados; 13,225 personas tienen montos mensuales comparables. El proceso imprime estas magnitudes y exporta la validación para repetir la comprobación.

El proceso con fuentes completas verifica cardinalidad y correspondencia de uniones, integrantes del hogar, `0 <= D3 <= D2 <= D1 <= consumo`, suma de componentes de D2 y distribución nacional por edades. La cobertura y exclusiones se guardan en [`tables/validacion_datos.csv`](tables/validacion_datos.csv); los denominadores de la comparación mensual, en [`tables/h3_finanzas_ensafi.csv`](tables/h3_finanzas_ensafi.csv).

La ejecución posterior con caché reprodujo los trece CSV sin diferencias. Se contrastaron las cifras principales del README con esas tablas y se revisaron visualmente las seis figuras. Entorno de validación: Python 3.12.14, pandas 3.0.1, NumPy 2.3.5, Matplotlib 3.11.2 y PyArrow 26.0.0. Las pruebas y estos controles no sustituyen una validación causal ni estimaciones de incertidumbre muestral.

## Límites pendientes

- No se estiman errores estándar con estratos y UPM: las brechas no son pruebas de significancia.
- Los hogares sin consumo seleccionado permanecen con gasto cero para concentración y niveles; las participaciones de gasto excluyen denominadores cero. `n` es tamaño del grupo, no necesariamente tamaño válido de cada media.
- La renta se observa por vivienda y se compara con ingreso del hogar. En viviendas con varios hogares es una aproximación, no una asignación del pago efectivo a cada hogar; su número se publica en la validación. No se infiere la capacidad de comprar vivienda a partir de esa razón.
- Persisten subreporte, límites de las canastas normativas y diferencias de universo entre ENIGH y ENSAFI. El ingreso corriente ENIGH incluye componentes no monetarios; el de ENSAFI utilizado aquí es laboral.
- Para inferir deterioro generacional se requieren comparaciones a edades equivalentes en distintos años. Para atribuir falta de vivienda o retiro al consumo se requiere un contrafactual de acumulación y una estrategia causal.

## Fuentes de las definiciones

- [INEGI: descripción de la base ENIGH 2024](https://www.inegi.org.mx/contenidos/programas/enigh/nc/2024/microdatos/889463924494.pdf), construcción de `tot_integ`, `menores` y agregados de gasto. Los catálogos locales se distribuyen con los microdatos.
- [INEGI: ENSAFI 2023](https://www.inegi.org.mx/programas/ensafi/2023/), diccionario de `tmodulo` y catálogos `p5_19`, `p5_19a`, `p5_21`, `p6_3`, `p6_5_*`, `p6_6_*` y `p6_7` incluidos en la descarga.
- [OCDE: escala modificada](https://www.oecd.org/en/publications/oecd-handbook-on-the-compilation-of-household-distributional-results-on-income-consumption-and-saving-in-line-with-national-accounts-totals_5a3b9119-en/full-report/component-11.html): primer adulto 1, personas adicionales de 14 o más 0.5, menores de 14 0.3.
