# Comparación histórica de H1–H5

ENIGH 1994, 2004, 2014 y 2024. [Informe completo](historico_hipotesis.html),
[resumen numérico](tables/historico_resumen.csv) y [correspondencias de variables](tables/historico_correspondencias.csv).

Las extensiones de gasto usan H1c (alimentos fuera más recreación, turismo y hospedaje),
con una definición distinta de D2. H3 mide movimientos financieros; H4 distingue
tenencia, pensiones recibidas y programas para adultos mayores. El informe explica
los universos, intervalos, cambios de clasificación y límites de cada comparación.

[Todas las pruebas entre categorías](significancia.html): diferencias, IC 95%, p de Holm y decisiones para cada par de edades y años.

## H1. Gasto a la misma edad

![H1: gasto histórico a la misma edad](figures/h1_historico_comparacion.png)

## H1b. Equipamiento y servicios del hogar

![H1b: equipamiento de 2004 a 2024](figures/h1b_historico_bienes.png)

## H2. Brechas dentro de cada decil de ingreso

![H2: brechas históricas joven menos mayor](figures/h2_historico_brechas.png)

## H3. Movimientos financieros y gasto

![H3: préstamos recibidos y retiros](figures/h3_historico_flujos.png)

![H3: gasto según presencia de préstamos o retiros](figures/h3_historico_gasto_flujos.png)

## H4. Vivienda y recepción de ingresos para la vejez

![H4: tenencia histórica de vivienda](figures/h4_historico_vivienda.png)

![H4: pensiones y programas para adultos mayores](figures/h4_historico_pensiones.png)

## H5. Concentración del gasto

![H5: concentración de H1c](figures/h5_historico_concentracion.png)

## Tablas

| Archivo | Contenido |
|---|---|
| [historico_resumen.csv](tables/historico_resumen.csv) | Comparación principal, en porcentajes. |
| [historico_perfiles.csv](tables/historico_perfiles.csv) | 312 estimaciones por edad, indicador y año, con IC y tamaños muestrales. |
| [h2_historico_brechas.csv](tables/h2_historico_brechas.csv) | 40 diferencias joven menos 60+ dentro de deciles de ingreso por persona. |
| [h3_historico_asociacion.csv](tables/h3_historico_asociacion.csv) | H1c según préstamos/retiros y sus contrastes. |
| [h4_historico_carga_renta.csv](tables/h4_historico_carga_renta.csv) | Medianas de renta/ingreso de 2014 y 2024, con IC por bootstrap de UPM. |
| [h5_historico_concentracion.csv](tables/h5_historico_concentracion.csv) | Gini, top 10%, top 20% e IC por bootstrap de UPM. |
| [historico_edades_ajustadas.csv](tables/historico_edades_ajustadas.csv) | Sensibilidades con distribución de edades de 2024. |
| [historico_contrastes.csv](tables/historico_contrastes.csv) | Diferencias de 2024 frente a cada año anterior, en puntos porcentuales. |
| [historico_correspondencias.csv](tables/historico_correspondencias.csv) | Claves históricas de préstamos, retiros, pensiones y vivienda. |
| [historico_validacion.csv](tables/historico_validacion.csv) | Conciliaciones y discrepancia conocida del agregado JUBILA 2004. |

Excepto historico_resumen.csv y los campos terminados en `_pp` de historico_contrastes.csv, las proporciones
y sus intervalos usan escala 0–1. `n` cuenta observaciones muestrales;
`hogares_expandidos` suma los ponderadores. Los archivos son agregados sin identificadores.
[historico_metodologia.json](historico_metodologia.json) registra las claves y hashes de las fuentes adicionales;
sus rutas son relativas al directorio de microdatos ENIGH indicado con `--raw`.

## Reproducción

Desde la raíz del proyecto, con las dependencias y las fuentes de [data/README.md](../data/README.md):

```bash
python scripts/compare_all_history.py
# Directorios alternativos:
python scripts/compare_all_history.py --raw /ruta/enigh --output /ruta/resultados
```

El comando reconstruye los CSV de estimaciones, precisión y contrastes en `reports/tables/`, los ocho PNG de niveles y los gráficos de diferencias en `reports/figures/`,
el registro de fuentes y el informe HTML en `reports/`.
Lee los microdatos de nuevo; no guarda copias ni cachés individuales en esta carpeta.

## Pruebas entre categorías

- [Edades en cada año](tables/historico_comparaciones_edad.csv).
- [Años a edad fija](tables/historico_comparaciones_tiempo.csv).
- [Precisión de todos los dominios](tables/historico_precision.csv).
- [Informe con filtros y gráficos de diferencias](significancia.html).

Los intervalos son individuales; `p_ajustada_holm` determina `significativa_holm_005`. Cada fila identifica su familia. Para H2, Holm abarca los seis pares de edades en los diez deciles del año. Para años, abarca todos los pares disponibles por indicador y edad. Las columnas `estimacion` de los archivos de comparaciones están en la unidad indicada por `unidad` (p.p., índice, años, personas o MXN); las tablas de niveles conservan su escala original.
