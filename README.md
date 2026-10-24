# Gente pobre de gustos caros

## *tl;dr*

He oído muchas veces que los jóvenes gastan una cantidad enorme de dinero en lujos innecesarios y luego se quejan de la falta de pensiones dignas, vivienda y otras desventuras. El argumento suele usarse para desestimar esos problemas y reducirlos a un asunto de administración personal.

Este proyecto contrasta esa idea con microdatos de México. **La evidencia no respalda la caricatura.** Los hogares cuyo jefe o jefa tiene entre 18 y 29 años destinan una fracción algo mayor de su gasto a bienes y servicios "visibles" que los hogares de 60 años o más (18.8% vs. 13.3%, una diferencia de 5.5 puntos porcentuales), sobre todo a restaurantes. Pero no gastan más en vicios, no tienen más deuda ni más estrés financiero que los adultos de 30 a 44 años, y enfrentan una presión de vivienda mucho mayor: 41.1% renta, frente a 6.3% de los hogares de 60+.

El "gusto caro" también está **muy concentrado**: el 10% de hogares con mayor gasto visible concentra 54% de ese gasto, y el 20% superior concentra 74%. No es una conducta exclusiva de una generación.

> **Alcance:** este análisis cubre únicamente México. No es una comparación entre países.

---

## Veredicto por hipótesis

| Hipótesis | Veredicto | Evidencia principal |
|---|---|---|
| **H1.** Los jóvenes destinan una mayor proporción de su gasto a bienes no básicos. | **Se sostiene, con magnitud modesta** | D2: 18.8% en 18-29 vs. 13.3% en 60+ (5.5 p.p.). D1: 47.9% vs. 41.5%. |
| **H2.** La diferencia persiste al comparar hogares con ingreso similar. | **Se sostiene** | La brecha joven − 60+ es positiva en los 10 deciles de ingreso; va de 2.9 a 8.3 p.p. y se amplía en los deciles altos. |
| **H3.** Los jóvenes financian ese gasto con deuda o desahorro. | **No se sostiene** | Deuda: 40.1% en 18-29 vs. 48.8% en 30-44. Alto estrés: 28.6% vs. 40.5%. Gasta más de lo que ingresa: 33.2% vs. 41.5%. |
| **H4.** Los jóvenes tienen menor cobertura de pensión y vivienda y aun así se quejan. | **Se sostiene la desventaja, no la queja infundada** | Renta: 41.1% de los hogares 18-29 vs. 6.3% de 60+. Espera pensión/AFORE: 58.9% vs. 38.4%. Espera apoyo de gobierno: 55.2% vs. 85.0%. |
| **H5.** El gasto en "gustos caros" se concentra en una minoría. | **Se sostiene** | Gini de D2 = 0.73; top 10% = 54% del gasto visible; top 20% = 74%. |

**Conclusión general:** hay un grano de verdad —los hogares jóvenes gastan relativamente más en restaurantes, recreación y otros bienes visibles—, pero el tamaño del fenómeno no permite explicar la precariedad de pensiones o vivienda. La evidencia es más compatible con una generación con menores ingresos, menor cobertura de ahorro para el retiro y mayor incidencia de renta que con una generación que dilapida su dinero.

---

## Fuentes y alcance

| Fuente | Año | Universo utilizado | Ponderador |
|---|---|---|---|
| **ENIGH Nueva Serie** (INEGI) | 2024 | 91,414 hogares; 308,598 personas | `factor` |
| **ENSAFI** (INEGI/CONDUSEF) | 2023 | 20,448 personas de 18 años o más | `FAC_ELE` |

- **ENIGH 2024** se usa para gasto, ingreso, composición del gasto y vivienda.
- **ENSAFI 2023** se usa para deuda, ahorro, AFORE, estrés financiero, expectativas de retiro y tenencia de bienes.
- La versión anterior de este README decía "ENSAFI 2024". Es un error: la encuesta disponible y utilizada es **ENSAFI 2023**.
- Los microdatos crudos no se versionan en el repositorio porque el archivo de gastos de ENIGH pesa aproximadamente 552 MB.

---

## Estructura del proyecto

```text
.
├── README.md
├── requirements.txt
├── .gitignore
├── pdfs/                            # ocho papers de la bibliografía
├── data/
│   └── processed/                  # caché derivado (no se versiona)
├── reports/
│   ├── figures/                    # seis figuras PNG
│   └── tables/                     # doce tablas CSV agregadas y auditables
├── scripts/
│   └── make_figures.py             # punto de entrada reproducible
├── src/
│   └── gpdgc/
│       ├── __init__.py
│       ├── config.py               # rutas, grupos de edad, colores
│       ├── taxonomy.py             # definición de canastas D1/D2/D3
│       ├── io.py                   # lectura y limpieza de ENIGH/ENSAFI
│       ├── weights.py              # media, cuantiles, Gini, Lorenz, top shares
│       ├── analysis.py             # tablas H1-H5
│       └── plots.py                # figuras
└── tests/
    └── test_core.py                # pruebas de canastas y ponderadores
```

No se usan notebooks. Todo el análisis vive en módulos de Python y se ejecuta con un script.

---

## Metodología

### 1. Unidad de análisis y grupos de edad

- **ENIGH:** el gasto se observa a nivel hogar. La edad se asigna con la **edad del jefe o jefa del hogar**, porque la encuesta no permite atribuir cada consumo a una persona específica.
- **ENSAFI:** las variables financieras y de expectativas son individuales; se usan personas de 18 años o más.
- Grupos: **18-29, 30-44, 45-59 y 60+**.
- Esta decisión es conservadora para la hipótesis: un hogar con jefe/a joven puede incluir personas de otras edades, y un hogar con jefe/a mayor puede incluir jóvenes. Si el estereotipo fuera cierto, la comparación por edad del jefe/a debería mostrarlo; no lo hace con la fuerza que sugiere el relato.

### 2. Canastas de gasto

La ENIGH clasifica cada renglón con una clave de seis dígitos. Los dos primeros dígitos identifican el capítulo de la COICOP adaptada por el INEGI. Para no depender de una sola definición normativa, se reportan tres canastas:

| Canasta | Definición | Capítulos / claves |
|---|---|---|
| **D1. Discrecional amplio** | Todo gasto no básico o fácilmente postergable | 02, 05, 07, 08, 09, 11, 12, 13 |
| **D2. Gusto visible** | Gasto con alta visibilidad social: salir, viajar, alcohol, accesorios, streaming y auto nuevo | 02, 09, 11; joyería/bisutería (`1321`), bolsos (`1329`), streaming/TV de paga (`081404`, `083921`-`083924`) y auto nuevo (`071110`) |
| **D3. Vicios** | Alcohol, tabaco y narcóticos | 02 |

- **D2 es la medida principal** porque se acerca más a lo que el argumento cotidiano llama "gusto caro".
- **D3** se incluye como prueba de la versión más moralista del relato: si el problema fueran los vicios, debería aparecer una brecha clara. No aparece.
- Se excluyen el capítulo **17** (transferencias y erogaciones, que no son consumo) y **T9** (regalos a terceros).
- La definición exacta está en [`src/gpdgc/taxonomy.py`](src/gpdgc/taxonomy.py).

### 3. Ponderación e ingreso equivalente

- Todas las estimaciones usan el factor de expansión (`factor` en ENIGH, `FAC_ELE` en ENSAFI).
- Los deciles de ingreso se construyen con **ingreso corriente equivalente**, usando la escala de equivalencia OCDE modificada: `1 + 0.5 × (adultos − 1) + 0.3 × menores`.
- El gasto por adulto equivalente usa la misma escala.
- Las medias y participaciones son ponderadas; los cuantiles se calculan sobre pesos acumulados.

### 4. Validación

- `gasto_total_g1` (suma de consumo analizado) equivale a una **mediana de 87.4%** de `gasto_mon` (gasto monetario oficial), porque excluye el capítulo 17 y los regalos. Las participaciones se calculan sobre el total analizado, no sobre `gasto_mon`.
- La renta de ENIGH es **mensual** y el ingreso es **trimestral**; la carga de renta se calcula como `renta × 3 / ing_cor`.
- ENSAFI usa `EDAD_V`, no `EDAD`, porque la primera es la variable validada de edad.

---

## Hallazgos

### H1. Los hogares jóvenes gastan una fracción algo mayor en bienes no básicos

![H1: composición del gasto por edad](reports/figures/h1_composicion_por_edad.png)

- **D2 (gusto visible):** 18.8% del gasto en hogares 18-29, 18.0% en 30-44, 16.2% en 45-59 y 13.3% en 60+. La brecha joven − 60+ es de **5.5 p.p.**
- **D1 (discrecional amplio):** 47.9% vs. 41.5% en 60+; brecha de **6.5 p.p.**
- **D3 (vicios):** 0.68% vs. 0.56% en 60+. Prácticamente no hay diferencia. **El relato de "se gastan todo en alcohol y tabaco" no se sostiene.**
- **Composición de D2 en 18-29:** restaurantes y hoteles 12.9 p.p., recreación 3.6 p.p., alcohol/tabaco 0.7 p.p., accesorios personales 0.4 p.p., streaming/TV de paga 0.7 p.p. y auto nuevo 0.4 p.p.
- El gasto visible por adulto equivalente es de **4,578 MXN trimestrales** en 18-29 vs. **2,564 MXN** en 60+.
- Al mismo tiempo, los hogares jóvenes destinan menos a alimentos (27.7% vs. 35.5%) y a salud (2.2% vs. 4.8%), y más a vivienda (12.8% vs. 10.4%). No es que "no gasten en lo básico"; es que tienen una estructura de gasto distinta.

**Lectura:** la hipótesis tiene sustento, pero el efecto es de unos **5.5 puntos porcentuales**, no de una orgía de lujos. Restaurantes explica la mayor parte de la diferencia.

### H1b. Los jóvenes no declaran más bienes "visibles" que los adultos

![H1b: tenencia de bienes y servicios](reports/figures/h1b_bienes_ensafi.png)

- **Automóvil:** 47.0% en 18-29 vs. 53.7% en 45-59.
- **Internet:** 81.0% en 18-29 vs. 65.6% en 60+.
- **TV de paga:** 40.6% vs. 46.0% en 45-59.
- **Streaming:** 30.3% vs. 19.0% en 60+.

**Lectura:** hay más adopción de servicios digitales entre jóvenes, pero no una tenencia superior de bienes durables costosos. El estereotipo del joven con auto nuevo y televisión de paga no aparece en los datos.

### H2. La brecha por edad persiste dentro de cada decil de ingreso

![H2: brecha por decil](reports/figures/h2_brecha_por_decil.png)

- La participación de D2 en los hogares 18-29 es mayor que en los hogares 60+ **en los 10 deciles**.
- La brecha va de **2.9 p.p.** (decil 2) a **8.3 p.p.** (decil 10). No es un artefacto de que los jóvenes tengan más ingreso: se amplía en la parte alta.
- En el decil 1, los jóvenes destinan 11.4% a D2 vs. 7.4% de los 60+.
- En el decil 10, 29.8% vs. 21.5%.
- El **nivel** de gasto visible por adulto equivalente también es mayor entre jóvenes en todos los deciles: desde 886 MXN vs. 595 MXN en el decil 1 hasta 15,245 MXN vs. 8,281 MXN en el decil 10.

**Lectura:** no es solo un efecto de composición por ingreso. La diferencia por edad existe dentro de estratos comparables. La hipótesis se sostiene.

### H3. Los jóvenes no están más endeudados ni más estresados que los adultos de 30-44

![H3: finanzas personales](reports/figures/h3_finanzas_ensafi.png)

- **AFORE:** 14.4% en 18-29, 22.9% en 30-44, 22.7% en 45-59 y 6.3% en 60+. Los jóvenes tienen baja cobertura, pero los 60+ también, por razones históricas.
- **Deuda:** 40.1% en 18-29 vs. 48.8% en 30-44 y 28.4% en 60+.
- **Atraso en pagos:** 10.1% vs. 12.3% en 30-44.
- **Alto estrés financiero:** 28.6% vs. 40.5% en 30-44 y 35.8% en 60+.
- **Gasta más de lo que ingresa:** 33.2% vs. 41.5% en 30-44 y 19.6% en 60+.
- **Ingreso mensual mediano:** 2,200 MXN en 18-29 vs. 3,200 MXN en 30-44 y 2,000 MXN en 60+.

**Lectura:** los jóvenes tienen menos colchón financiero y menor cobertura de AFORE, pero **no** presentan más deuda, más atraso ni más estrés que los adultos en edad productiva. La idea de que el gasto visible se financia con deuda juvenil no se sostiene con estos datos. La desventaja principal es de **ingreso y cobertura**, no de impulsividad financiera.

### H4. La desventaja de vivienda y pensión es real; la queja no es infundada

![H4: pensiones y vivienda](reports/figures/h4_pensiones_vivienda.png)

- **Hogares que rentan:** 41.1% en 18-29, 23.6% en 30-44, 12.3% en 45-59 y 6.3% en 60+.
- **Carga de renta mediana (solo rentadores):** 13.4% del ingreso en 18-29 vs. 17.0% en 60+. La incidencia de renta es mucho mayor entre jóvenes, aunque quienes rentan a los 60+ destinan una fracción algo mayor de su ingreso.
- **Espera pensión, jubilación o AFORE:** 58.9% en 18-29 vs. 38.4% en 60+.
- **Espera apoyo de gobierno:** 55.2% en 18-29 vs. 85.0% en 60+.
- **Espera seguir trabajando:** 72.5% en 18-29 vs. 35.3% en 60+.
- **Tiene vivienda como meta:** 37.4% en 18-29 vs. 21.5% en 60+.

**Lectura:** los jóvenes no son más dependientes de la pensión pública que los mayores; de hecho, esperan más pensión/AFORE y mucho menos apoyo gubernamental. Pero **sí** enfrentan una incidencia de renta casi siete veces mayor que los hogares de 60+ y una baja cobertura de ahorro para el retiro. La preocupación por vivienda y pensión está materialmente fundada. Lo que no se sostiene es la idea de que se quejan mientras derrochan.

### H5. El gasto visible se concentra en una minoría, no en una generación

![H5: concentración del gasto visible](reports/figures/h5_concentracion.png)

- **Gini de D2:** 0.73.
- **Top 10% de hogares:** concentra **54%** del gasto visible.
- **Top 20%:** concentra **74%**.
- **Top 20% dentro de cada grupo de edad:** 71.6% en 18-29, 69.7% en 30-44, 73.0% en 45-59 y 78.7% en 60+.
- Los hogares 18-29 son **7.4%** de los hogares, pero concentran **8.2%** del gasto visible total. Los hogares 60+ son 31.9% de los hogares y concentran 24.0% del gasto visible.

**Lectura:** el gasto visible es un fenómeno de minorías acomodadas en **todas** las edades. Los jóvenes están ligeramente sobrerrepresentados (8.2% del gasto vs. 7.4% de los hogares), pero la mayor parte del gasto visible del país no viene de ellos. Atribuir el fenómeno a "los jóvenes" oculta la concentración de ingreso y gasto.

---

## Limitaciones

1. **No es causal.** Todas las estimaciones son descriptivas y transversales. No se puede concluir que la edad "cause" el gasto, ni que el gasto cause endeudamiento o malestar.
2. **Edad del jefe/a en ENIGH.** El gasto se atribuye al hogar, no a la persona. Un hogar joven puede incluir personas mayores y viceversa. Esto atenúa las diferencias y hace que los resultados sean conservadores.
3. **Canastas normativas.** D1, D2 y D3 son definiciones analíticas discutibles. Por eso se reportan tres versiones y se documentan las claves exactas. Restaurantes puede incluir comidas necesarias por trabajo; vivienda incluye servicios y combustibles.
4. **Subreporte y diseño muestral.** ENIGH y ENSAFI tienen subreporte, especialmente en alcohol, gastos irregulares y deuda. No se calcularon errores estándar ni intervalos de confianza; las cifras son estimaciones puntuales ponderadas.
5. **ENSAFI mide percepciones y autopercepción.** "Alto estrés" y "gasta más de lo que ingresa" dependen de lo que la persona declara.
6. **Comparación de ingresos entre fuentes.** ENIGH y ENSAFI tienen universos y preguntas distintas; no se mezclan en una misma estimación, solo se presentan lado a lado.
7. **Cobertura geográfica.** Solo México. No hay datos de otros países en este repositorio.

---

## Reproducción

```bash
git clone git@github.com:Betancourt1/gente-pobre-de-gustos-caros.git
cd gente-pobre-de-gustos-caros
python -m pip install -r requirements.txt

# Primera ejecución: construye el caché de gastos (~552 MB de CSV -> parquet)
python scripts/make_figures.py

# Si se quiere reconstruir el caché desde cero
python scripts/make_figures.py --force-gastos
```

Los datos crudos deben colocarse en la raíz del repositorio con estos nombres:

```text
conjunto_de_datos_enigh2024_ns_csv/
conjunto_de_datos_ensafi_2023_csv/
```

Se pueden descargar de los sitios de INEGI:

- ENIGH 2024 Nueva Serie: <https://www.inegi.org.mx/programas/enigh/nc/2024/>
- ENSAFI 2023: <https://www.inegi.org.mx/programas/ensafi/2023/>

Descarga los conjuntos CSV de microdatos y descomprímelos conservando sus subcarpetas. Las rutas exactas están en [`src/gpdgc/config.py`](src/gpdgc/config.py). El proceso utiliza `concentradohogar`, `poblacion`, `viviendas` y `gastoshogar` de ENIGH, y `tmodulo` y `tvivienda` de ENSAFI. No requiere una caché previa: crea `data/processed/` al construir el agregado de gastos.

### Qué se publica y cómo ampliar el análisis

El repositorio incluye código, bibliografía en PDF, figuras y CSV agregados de `reports/tables/`. Los microdatos completos, los ZIP de descarga con nombre `conjunto_de_datos_*` y las cachés Parquet quedan excluidos mediante `.gitignore`. Los CSV publicados no contienen registros individuales ni identificadores de hogares o personas.

`python scripts/make_figures.py --force-gastos` reconstruye las doce tablas y las seis figuras a partir de los microdatos de origen. Las funciones `load_enigh_hogares()` y `load_ensafi_personas()` de [`src/gpdgc/io.py`](src/gpdgc/io.py) preparan las bases analíticas locales para realizar cruces adicionales; no unen personas de una encuesta con hogares de la otra.

Tres CSV complementan las tablas originales para ampliar la discusión sin publicar el dataset:

| Archivo en `reports/tables/` | Contenido y uso |
|---|---|
| `h2_sensibilidad_canastas_por_decil.csv` | 40 combinaciones de edad y decil de ingreso equivalente, con tamaño de muestra `n` y medias ponderadas de las participaciones D1, D2 y D3. Permite comprobar cuánto depende la brecha de la canasta elegida. |
| `h5_concentracion_nacional.csv` | Gini de D1 y D2, participación del 10% superior en ambas canastas y del 20% superior en D2. Los hogares se ordenan por gasto en la canasta correspondiente, no por ingreso. |
| `h5_curva_lorenz_d2.csv` | 200 puntos interpolados de la curva de Lorenz ponderada de D2, ordenando hogares de menor a mayor gasto visible. Permite reproducir la curva; el Gini publicado se calcula sobre los datos originales, no sobre estos puntos interpolados. |

Las participaciones, cargas y coeficientes se exportan como proporciones de 0 a 1, salvo indicadores rotulados explícitamente en puntos porcentuales o columnas `peso_pct`, que usan escala de 0 a 100. Los montos ENIGH son pesos trimestrales y los montos ENSAFI indicados como mensuales son pesos mensuales. `n` es el número de observaciones sin expandir. Las tablas permiten comparaciones descriptivas; no incluyen errores estándar ni intervalos de confianza.

Para correr las pruebas:

```bash
python -m unittest discover -s tests
```

### Salidas generadas

| Figura | Archivo |
|---|---|
| H1. Composición del gasto | `reports/figures/h1_composicion_por_edad.png` |
| H1b. Bienes y servicios | `reports/figures/h1b_bienes_ensafi.png` |
| H2. Brecha por decil | `reports/figures/h2_brecha_por_decil.png` |
| H3. Finanzas personales | `reports/figures/h3_finanzas_ensafi.png` |
| H4. Pensiones y vivienda | `reports/figures/h4_pensiones_vivienda.png` |
| H5. Concentración | `reports/figures/h5_concentracion.png` |

Las tablas que respaldan cada figura están en `reports/tables/`, incluida `hallazgos_clave.csv`.

---

## Qué haría falta para sostener la hipótesis original

Para afirmar que los jóvenes "se gastan todo en lujos y por eso no tienen pensión ni vivienda" haría falta, como mínimo:

1. Que la brecha de gasto visible fuera mucho mayor que 5.5 p.p. y que explicara una parte relevante del ingreso.
2. Que los jóvenes tuvieran más deuda, más atraso o más desahorro que los adultos; no ocurre.
3. Que la falta de vivienda y pensión se debiera principalmente a decisiones de consumo y no a ingresos, cobertura laboral, informalidad y precios de vivienda; los datos no permiten esa conclusión.
4. Que el fenómeno estuviera localizado en los jóvenes; en realidad está concentrado en minorías de todos los grupos de edad.

La hipótesis original contiene un grano de verdad sobre patrones de consumo, pero **no alcanza para explicar ni para desestimar** los problemas estructurales de vivienda y pensiones.

---

## Bibliografía comentada

Estos ocho trabajos aportan evidencia y contrapuntos sobre consumo visible, comparación social, ciclo de vida, vivienda y ahorro para el retiro. Las aplicaciones al proyecto son propuestas de interpretación; los resultados de otros países no se trasladan automáticamente a México. Los documentos de trabajo y las versiones abiertas anteriores a la publicación se identifican en cada ficha.

### 1. Consumo y ciclo de vida

**Referencia:** Aguiar, Mark, y Erik Hurst (2013). “Deconstructing Life Cycle Expenditure”. *Journal of Political Economy*, 121(3), 437–492. DOI: [10.1086/670740](https://doi.org/10.1086/670740).

**Sinopsis:** Con datos de Estados Unidos, los autores descomponen el gasto a lo largo del ciclo de vida. Encuentran que su caída después de la edad media se concentra en alimentación, transporte y ropa o cuidado personal, categorías relacionadas con el trabajo y la disponibilidad de tiempo. En alimentación fuera del hogar, distinguen la reducción de visitas a comida rápida y cafeterías de las visitas a restaurantes con servicio de mesa. Estos patrones muestran que gastar menos al envejecer no necesariamente significa tener preferencias más austeras.

**Aporte al proyecto — H1 y H2:** Como restaurantes explica gran parte de la brecha de D2, conviene separar el gasto asociado al trabajo del consumo recreativo y considerar empleo y composición familiar. Una comparación por edad en un solo año no separa efectos del ciclo de vida de diferencias entre generaciones.

**Acceso:** [Texto completo en el sitio del autor](https://www.markaguiar.com/files/deconstructing.pdf).

### 2. Cómo medir el consumo visible

**Referencia:** Heffetz, Ori (2011). “A Test of Conspicuous Consumption: Visibility and Income Elasticities”. *The Review of Economics and Statistics*, 93(4), 1101–1117. DOI: [10.1162/REST_a_00116](https://doi.org/10.1162/REST_a_00116).

**Sinopsis:** Construye un índice de visibilidad mediante una encuesta que pregunta qué tan rápido se perciben los gastos de otros hogares. Después lo relaciona con la respuesta del gasto al ingreso en distintas categorías de consumo estadounidenses. La visibilidad explica parte de las diferencias entre categorías, en línea con la idea de que ciertos bienes también sirven para comunicar posición económica.

**Aporte al proyecto — canasta D2:** Ofrece un criterio empírico para definir “visible”. Visibilidad, lujo y gasto prescindible son conceptos distintos; la canasta puede beneficiarse de esa separación. El índice se construyó en Estados Unidos y requeriría validación para México.

**Acceso:** [Texto completo](https://lindseyresearch.com/wp-content/uploads/2019/06/NHTSA-2018-0067-12410-Heffetz_2011-1.pdf).

### 3. Comparación social y consumo en México

**Referencia:** González Olivares, Daniel, y Mauricio Ramírez Grajeda (2020). “Trickle-Down Consumption in a Country with High Income Inequality: Evidence from Mexico”. *Review of Economics and Finance*, 18, 142–155. DOI: [10.55365/1923.x2020.18.16](https://doi.org/10.55365/1923.x2020.18.16).

**Sinopsis:** Utiliza ENIGH 1992–2010 para construir un pseudopanel: grupos de hogares con características similares que pueden seguirse entre encuestas. Encuentra evidencia compatible con que los hogares de ingresos medios aumentan su consumo al estar expuestos a mayores ingresos y consumo de los hogares ricos. Sus estimaciones plantean que esa relación puede reducir el ahorro.

**Aporte al proyecto — H2, H3 y H5:** Es un antecedente mexicano directo para discutir presión de consumo y desigualdad. La concentración del gasto en hogares ricos puede coexistir con efectos sobre otros hogares. El artículo estudia consumo agregado, no la canasta D2, y no identifica un efecto exclusivamente juvenil.

**Acceso:** [Artículo y descarga del PDF](https://refpress.org/ref-vol18-a16/).

### 4. Consumo de los ricos y ahorro del resto

**Referencia:** Bertrand, Marianne, y Adair Morse (2016). “Trickle-Down Consumption”. *The Review of Economics and Statistics*, 98(5), 863–879.

**Sinopsis:** Con variación entre estados y años en Estados Unidos, examina si el crecimiento del ingreso y consumo de los hogares de la parte alta de la distribución se relaciona con un mayor consumo relativo de los demás. Encuentra evidencia de esa relación, especialmente en bienes y servicios visibles, y de mayores dificultades financieras entre hogares expuestos a ingresos altos en su entorno. Los resultados son compatibles con mecanismos de comparación social y cambios en la oferta de bienes.

**Aporte al proyecto — H3:** Introduce un contrapunto: una menor incidencia de deuda entre jóvenes que entre adultos no descarta efectos del consumo sobre el ahorro. Para evaluar ese vínculo directamente se necesitaría observar gasto y financiamiento en las mismas unidades de análisis.

**Acceso:** [Resumen y versión de trabajo de 2013, NBER Working Paper 18883](https://www.nber.org/papers/w18883).

### 5. El papel del grupo de referencia

**Referencia:** Charles, Kerwin Kofi, Erik Hurst y Nikolai Roussanov (2009). “Conspicuous Consumption and Race”. *The Quarterly Journal of Economics*, 124(2), 425–467. DOI: [10.1162/qjec.2009.124.2.425](https://doi.org/10.1162/qjec.2009.124.2.425).

**Sinopsis:** Analiza diferencias de gasto en ropa, joyería y automóviles entre grupos raciales y étnicos en Estados Unidos. Presenta un modelo en el que el consumo visible comunica posición económica y encuentra que las características de ingreso del grupo de referencia explican buena parte de las diferencias observadas. El entorno social importa además de los recursos propios del hogar.

**Aporte al proyecto — H2:** Comparar hogares del mismo decil de ingreso no controla todos los mecanismos relevantes. Una extensión podría estudiar diferencias por entorno geográfico y grupos de referencia. Los resultados raciales del artículo no deben extrapolarse al caso mexicano.

**Acceso:** [Artículo y resumen](https://academic.oup.com/qje/article-abstract/124/2/425/1905068).

### 6. Barreras de acceso a la vivienda en México

**Referencia:** Maravalle, Alessandro, Aida Caldera Sánchez y Alberto González Pandiella (2024). “Improving Housing and Urban Development Policies in Mexico”. *OECD Economics Department Working Papers*, núm. 1801. DOI: [10.1787/c2229c19-en](https://doi.org/10.1787/c2229c19-en). Documento de trabajo.

**Sinopsis:** Examina precios elevados, acceso limitado al crédito, insuficiente oferta de vivienda asequible y problemas de ubicación y coordinación urbana en México. Documenta que los precios de vivienda crecieron más rápido que el ingreso promedio entre 2005 y 2020. También analiza cómo las restricciones de financiamiento y el escaso desarrollo del mercado de renta afectan a los hogares de ingresos bajos y medios.

**Aporte al proyecto — H4:** Aporta evidencia sobre mecanismos estructurales de acceso a vivienda. Complementa la incidencia de renta con precios, financiamiento y calidad habitacional; rentar más, por sí solo, no demuestra un deterioro entre generaciones.

**Acceso:** [Texto completo](https://www.oecd.org/content/dam/oecd/en/publications/reports/2024/05/improving-housing-and-urban-development-policies-in-mexico_a5e81d35/c2229c19-en.pdf).

### 7. Reglas del sistema de pensiones mexicano

**Referencia:** Bonthuis, Boele (2024). “An Assessment of the 2019 and 2020 Pension Reforms in Mexico”. *IMF Working Papers*, 2024/53. DOI: [10.5089/9798400269431.001](https://doi.org/10.5089/9798400269431.001). Documento de trabajo.

**Sinopsis:** Evalúa los resultados esperados de las reformas mexicanas de pensiones de 2019 y 2020. Examina cambios en aportaciones, requisitos de elegibilidad y pensiones mínimas, así como problemas de diseño e incentivos. Sitúa los resultados del retiro dentro de las reglas institucionales y las trayectorias de cotización.

**Aporte al proyecto — H4:** Ayuda a distinguir entre tener una cuenta AFORE, cumplir los requisitos de pensión y recibir un ingreso suficiente al retirarse. Las expectativas declaradas en ENSAFI no miden por sí solas esas tres condiciones. El trabajo analiza aquellas reformas y no es una descripción completa del sistema vigente en 2026.

**Acceso:** [Texto completo](https://www.imf.org/-/media/files/publications/wp/2024/english/wpiea2024053-print-pdf.pdf).

### 8. Acceso, mensajes y ahorro voluntario para el retiro

**Referencia:** Bosch, Mariano, y Adrian Rubli (2023). “Increasing Retirement Savings through Access Points and Persuasive Messages: Evidence from Mexico”. *Journal of Human Resources*, 58(5), 1752–1781.

**Sinopsis:** Estudia la ampliación de puntos para realizar aportaciones voluntarias al retiro en tiendas 7-Eleven y su combinación con una campaña de mensajes. La versión de trabajo de 2019, consultada aquí, encuentra efectos pequeños del acceso por sí solo y mayores efectos cuando se combina con la campaña. Utiliza datos administrativos y un diseño de diferencias en diferencias; no permite aislar el efecto de los mensajes sin la ampliación del acceso.

**Aporte al proyecto — H3 y H4:** Muestra que el ahorro responde a fricciones de acceso y a intervenciones sobre el comportamiento. Es un matiz frente a explicaciones basadas exclusivamente en ingreso o impulsividad. El resultado se refiere a aportaciones voluntarias y no demuestra por sí solo una mejora equivalente en la suficiencia de las pensiones.

**Acceso:** [Versión de trabajo de 2019, BID, núm. 1018](https://publications.iadb.org/publications/english/document/Increasing_Retirement_Savings_through_Access_Points_and_Persuasive_Messages_Evidence_from_Mexico_en_en.pdf).
