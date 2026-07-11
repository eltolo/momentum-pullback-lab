# Contexto del dominio

## Términos

### Fuente canónica de datos
Conjunto de series que el laboratorio acepta como fuente oficial y reproducible para construir señales, benchmarks y validaciones. Si otra fuente difiere, se trata como contraste o insumo secundario, no como verdad principal.

### Store diario BYMA
Repositorio histórico diario de acciones argentinas usado por el laboratorio como base de precios local. La decisión actual es usar `historico_merval.db / historico_diario` como store canónico para T267.

### Serie MEP canónica
Serie única de dólar MEP elegida para dolarizar precios y medir resultados en USD MEP. Debe mantenerse estable y versionable dentro del laboratorio.

### Gap crítico de MEP
Ausencia de valor MEP para una fecha requerida por el laboratorio. La decisión actual es tratarlo como falla dura en T267, no rellenarlo automáticamente.

### Ticket de frontera
Siguiente slice habilitado para ejecución según `tickets.json`, siempre respetando bloqueos previos.

### Universo inicial ejecutable
Subconjunto del universo deseado que realmente existe en el store canónico con cobertura suficiente para correr el laboratorio sin backfill nuevo. La decisión actual es priorizar la intersección disponible y líquida antes que forzar el universo ideal del spec desde el día 1.

### Exclusión por calidad
Regla por la cual un ticker con cobertura insuficiente o errores críticos de datos queda fuera del backtest base. La decisión actual es excluirlo de la corrida base y documentar el motivo y la severidad en `01_data_quality_report.md`.

### Cobertura completa requerida
Condición por la cual un ticker solo entra en la corrida base si cubre todo el período objetivo definido para esa corrida. La decisión actual es no permitir entradas tardías por disponibilidad parcial.

### Período base de primera corrida
Ventana temporal usada para la primera auditoría y corrida base del laboratorio. La decisión actual es usar 2021 en adelante, alineado con el antecedente del ecosistema para comparación rápida.

### Anomalía OHLC crítica
Registro con valores imposibles o no confiables, como `Low=0`, que invalida la confiabilidad del ticker para la corrida base. La decisión actual es excluir el ticker completo de la corrida base salvo corrección proveniente de una fuente canónica ya aprobada.

### Dataset curado
Conjunto versionado de datos que ya pasó la auditoría, respeta las exclusiones decididas y queda listo para la siguiente frontera del laboratorio. La decisión actual es que T267 debe dejar tanto el reporte de auditoría como este dataset curado para T268.

### Snapshot materializado
Copia persistida del dataset curado para inspección, handoff y trazabilidad. La decisión actual es usar dos capas: snapshot materializado en `data/processed/` y regeneración determinística desde código como fuente de verdad.

### Panel largo canónico
Forma persistida del dataset curado en una sola tabla por `date,ticker`, apta para filtros cross-sectional, benchmarks y ranking de momentum. La decisión actual es persistir el snapshot materializado como panel largo único.

### Serie cruda vs serie ajustada
Dos representaciones complementarias del mismo activo: precios observados y precios ajustados por eventos corporativos. La decisión actual es persistir ambas lado a lado en el panel largo para preservar auditabilidad y evitar recalcular ajustes en cada frontera.

### Benchmark primario del laboratorio
Referencia principal contra la cual se juzga la estrategia dentro del lab. La decisión actual es usar como benchmark primario una cartera equal-weight del universo curado, y mantener el Merval USD del ecosistema como benchmark secundario.

### Benchmark con fricciones realistas
Benchmark usado como referencia del universo curado incorporando fricciones cuando la construcción del benchmark implica rotación o rebalanceo. La decisión actual es que un benchmark buy and hold puede no rotar, pero cualquier benchmark que rebalancea debe incluir costos para no volverse irreal.

### Benchmark primario buy-and-hold
Versión principal del benchmark equal-weight que fija pesos al inicio y no rebalancea luego. La decisión actual es usar esta variante como benchmark primario del lab, dejando cualquier benchmark rebalanceado como comparación secundaria con costos explícitos.

### Universo tradable del día
Subconjunto del universo curado que, en una fecha concreta, cumple los requisitos de liquidez y ejecutabilidad definidos por el laboratorio. La decisión actual es calcular el ranking de momentum sobre este subconjunto, no sobre tickers no operables.

### Liquidez relativa al capital simulado
Criterio por el cual la operabilidad de un ticker se evalúa respecto del tamaño de capital que el laboratorio pretende mover, no con un umbral absoluto aislado. La decisión actual es adoptar este criterio desde el día 1.

### Familia de escalas de capital
Conjunto obligatorio de tamaños de capital sobre los cuales se evalúa una misma corrida del laboratorio. La decisión actual es no usar un único capital fijo como verdad suficiente, sino exigir sensibilidad por escala desde el inicio.

### Tríada inicial de escalas
Primera materialización operativa de la familia de escalas de capital. La decisión actual es comenzar con tres tamaños — chico, medio y grande — para detectar no linealidad sin inflar innecesariamente la complejidad de T267.

### Escala nominal en USD MEP
Representación de cada tamaño de capital como un monto económico fijo expresado en USD MEP. La decisión actual es definir la tríada inicial en montos fijos, no como porcentajes de una cartera abstracta.

### Tríada nominal inicial
Valores concretos de la primera familia de escalas del laboratorio. La decisión actual es usar 5k / 10k / 15k USD MEP como tamaños chico / medio / grande.

### Participación máxima conservadora
Límite de tamaño por posición respecto del volumen monetario diario del activo usado para decidir si un ticker es realmente operable. La decisión actual es usar 1% como umbral inicial conservador.

### Tradabilidad por escala
Propiedad por la cual un ticker puede ser operable para algunos tamaños de capital y no para otros dentro de la misma fecha. La decisión actual es preservar esa granularidad en lugar de excluirlo totalmente del laboratorio.

### Ranking por escala
Versión del ranking de momentum calculada sobre el universo tradable específico de cada tamaño de capital. La decisión actual es no reutilizar un ranking único para todas las escalas.

### Universo tradable precalculado
Artefacto derivado en T267 que deja resuelta la operabilidad por fecha y por escala antes de la fase de señales. La decisión actual es que T267 debe entregarlo junto con el dataset curado.

### Versión base de señal
Primera formulación explícita de la estrategia sobre la cual se construyen las comparaciones posteriores del laboratorio. La decisión actual es usar tendencia positiva + ranking de momentum como filtro + pullback a EMA21 + confirmación de entrada.

### Tendencia positiva base
Definición operativa mínima de tendencia para habilitar la búsqueda de pullbacks en la versión base. La decisión actual es usar `close > EMA21 > EMA50` para mantener continuidad con el antecedente del ecosistema.

### Pullback válido a EMA21
Retroceso que alcanza o perfora intradía la EMA21 pero termina con fortaleza suficiente como para cerrar nuevamente por encima de ella. La decisión actual es exigir toque o perforación intradía y cierre sobre EMA21.

### Confirmación de entrada diferida
Regla por la cual la señal de pullback no se ejecuta en la misma vela que la genera, sino tras una confirmación posterior. La decisión actual es modelar la entrada base con confirmación al día siguiente.

### Confirmación por quiebre de máximo
Condición objetiva por la cual la vela posterior valida la intención compradora rompiendo el máximo de la vela de pullback. La decisión actual es usar este criterio como confirmación base.

### Expiración corta de señal
Regla por la cual una oportunidad de entrada pierde validez rápidamente si no confirma en el plazo esperado. La decisión actual es hacer expirar la señal si no confirma al día siguiente.

### Filtro base de momentum
Umbral inicial del ranking por escala que define qué activos siguen elegibles para buscar pullbacks. La decisión actual es comenzar con una sola versión base: top 30% del ranking.

### Momentum base auditable
Definición simple y trazable de momentum usada para el ranking inicial del laboratorio. La decisión actual es usar retorno de 6 meses excluyendo el último mes como versión base.

### Salida base única
Primera regla de salida usada para evaluar si la lógica de entrada tiene edge antes de abrir una familia de variantes. La decisión actual es comenzar con una salida simple: stop bajo el low de la vela de pullback y manejo posterior con trailing, sin take profit fijo inicial.

### Trailing base sobre EMA21
Regla inicial de seguimiento de la posición que actualiza la salida en torno a la media principal del setup. La decisión actual es usar EMA21 como trailing base antes de explorar ATR o swings.

### Concurrencia base de cartera
Cantidad máxima de posiciones simultáneas permitidas en la versión base del laboratorio. La decisión actual es usar hasta 3 posiciones concurrentes por escala.

### Cash ocioso permitido
Regla de asignación por la cual el laboratorio puede mantener parte del capital sin invertir cuando no hay suficientes señales válidas para ocupar todos los slots. La decisión actual es reservar cash antes que forzar inversión completa.

### Benchmark secundario exposure-matched
Benchmark adicional usado para comparar la estrategia contra una referencia con exposición equivalente, sin reemplazar el benchmark primario simple. La decisión actual es incluirlo como lectura secundaria para separar efecto de exposición de efecto de selección.

### Exposure match agregado
Forma de emparejar un benchmark secundario con la estrategia usando la exposición total diaria como variable objetivo. La decisión actual es igualar la exposición agregada diaria sin copiar el número de posiciones de la cartera.

### Gate principal de robustez por escala
Criterio de aprobación que define en qué tamaños de capital la estrategia debe funcionar para seguir viva en el laboratorio. La decisión actual es exigir robustez en 5k y 10k USD MEP, tratando 15k como lectura de capacidad y stretch goal.

### Doble umbral de aprobación
Regla por la cual la estrategia no solo debe superar una referencia de preservación de capital sino también una referencia de mercado comparable. La decisión actual es exigir superioridad tanto frente a caución/cash como frente al benchmark primario del universo curado.

### Superioridad neta con riesgo razonable
Interpretación del verbo "superar" dentro del gate principal del laboratorio. La decisión actual es exigir retorno neto superior, mientras el drawdown no resulte grotescamente peor que las referencias; Sharpe no se usa como requisito duro inicial.

### Guardrail inicial de drawdown
Límite numérico simple para evitar aprobar una estrategia con retorno superior pero riesgo desproporcionado. La decisión actual es exigir que el max drawdown no supere 1.5x el del benchmark primario.

### Transferencia con parámetros congelados
Prueba de portabilidad del laboratorio hacia otro mercado manteniendo intacta la configuración aprobada en el mercado origen. La decisión actual es que la corrida USA de T270 use los mismos principios y parámetros, sin recalibración.

### Aprobación local con portabilidad fallida
Criterio de cierre por el cual una estrategia puede quedar aprobada para paper trading en su mercado origen aunque no transfiera con éxito a otro mercado. La decisión actual es permitir `APPROVED_FOR_PAPER` para Argentina aunque USA falle, tratando esa falla como evidencia de no-portabilidad y no como invalidación del edge local.
