# LAB — Momentum de Medio Plazo con Entrada en Retroceso

## 1. Objetivo

Diseñar, backtestear y validar una estrategia sistemática para acciones argentinas que:

- sea rentable después de comisiones, derechos, spread y slippage;
- tenga baja rotación;
- funcione con datos disponibles para un inversor retail;
- mida resultados en moneda constante o dolarizados mediante MEP;
- sea portable posteriormente al mercado estadounidense;
- no dependa de una única acción, período o combinación exacta de parámetros.

La estrategia combinará:

1. **Momentum de medio plazo** para seleccionar activos fuertes.
2. **Tendencia de largo plazo** para evitar comprar activos estructuralmente débiles.
3. **Retroceso de corto plazo** para no entrar después de una suba extendida.
4. **Confirmación de entrada** para evitar comprar mientras continúa la caída.
5. **Control de costos y rotación** como condición central de viabilidad.

---

## 2. Hipótesis

En activos con tendencia alcista y momentum positivo, los retrocesos de corto plazo tienden a revertirse con mayor probabilidad que en activos débiles.

La ventaja debería provenir de:

- comprar activos fuertes durante correcciones temporales;
- evitar activos en tendencia bajista;
- reducir la frecuencia operativa;
- capturar movimientos suficientemente grandes para superar los costos de BYMA;
- diversificar señales entre varios activos.

La hipótesis se considera válida únicamente si sobrevive:

- costos conservadores;
- diferentes períodos;
- diferentes activos;
- validación walk-forward;
- perturbación de parámetros;
- pruebas fuera de muestra;
- comparación contra benchmarks.

---

## 3. Universo inicial

### 3.1 Acciones argentinas

Usar inicialmente:

- GGAL
- YPFD
- PAMP
- BMA
- BBAR
- TXAR
- TGSU2
- CEPU
- ALUA
- BYMA

Agregar activos únicamente si cumplen requisitos mínimos de liquidez y calidad de datos.

### 3.2 Universo alternativo

Crear una segunda prueba independiente con CEDEARs líquidos.

No mezclar acciones argentinas y CEDEARs en la primera validación.

### 3.3 Prevención del sesgo de supervivencia

Siempre que sea posible:

- incluir activos deslistados o que dejaron de integrar el universo;
- reconstruir el universo histórico por fecha;
- registrar cuándo cada activo fue incorporado o eliminado.

Si no es posible eliminar completamente el sesgo de supervivencia, documentarlo claramente.

---

## 4. Datos requeridos

### 4.1 Datos diarios

Por activo:

- fecha;
- apertura;
- máximo;
- mínimo;
- cierre;
- volumen;
- cierre ajustado;
- dividendos;
- splits;
- moneda de cotización.

### 4.2 Dólar MEP

Obtener una serie diaria de dólar MEP consistente.

Prioridad:

1. MEP calculado con bonos líquidos y metodología estable.
2. Serie externa confiable.
3. MEP implícito mediante activos duales, correctamente documentado.

No mezclar fuentes sin normalización.

### 4.3 Precios dolarizados

Calcular:

```text
precio_usd = precio_ars / mep
```

Realizar todos los cálculos principales en:

- ARS nominal;
- USD MEP;
- opcionalmente ARS ajustado por inflación.

La decisión principal debe basarse en USD MEP.

### 4.4 Benchmark

Usar como mínimo:

- índice Merval dolarizado;
- buy and hold del universo equiponderado;
- activo libre de riesgo o caución, cuando sea posible.

Para CEDEARs, usar también SPY o un benchmark estadounidense apropiado.

---

## 5. Calidad de datos

Implementar controles automáticos:

- fechas duplicadas;
- días faltantes;
- precios cero o negativos;
- saltos extremos no explicados;
- volumen cero;
- inconsistencias entre OHLC;
- splits o dividendos no ajustados;
- cambios abruptos en MEP;
- diferencias entre fuentes;
- activos con historial insuficiente.

Generar un reporte de calidad antes de cualquier backtest.

No ejecutar el laboratorio si existen errores críticos de datos.

---

## 6. Costos de transacción

Los costos deben ser parametrizables.

### 6.1 Componentes

Incluir:

- comisión de compra;
- comisión de venta;
- derechos de mercado;
- impuestos aplicables;
- spread;
- slippage;
- costo de custodia si corresponde;
- impacto de mercado, si el tamaño lo requiere.

### 6.2 Escenarios

Evaluar como mínimo:

| Escenario | Costo total ida y vuelta |
|---|---:|
| Optimista | 0,80% |
| Base | 1,40% |
| Conservador | 1,80% |
| Estrés | 2,50% |

No considerar rentable una estrategia que solo funciona en el escenario optimista.

### 6.3 Regla económica mínima

La ganancia bruta media por operación debe ser:

```text
ganancia_bruta_media >= 3 × costo_total_ida_vuelta
```

La estrategia debe conservar expectativa positiva al duplicar el costo base.

---

## 7. Definición de momentum

Calcular momentum en USD MEP.

Probar horizontes:

- 63 ruedas;
- 126 ruedas;
- 189 ruedas;
- 252 ruedas.

Versión base:

```text
momentum_126 = cierre_usd / cierre_usd.shift(126) - 1
```

Probar también momentum excluyendo el último mes:

```text
momentum_12_1 = cierre_usd.shift(21) / cierre_usd.shift(252) - 1
```

### 7.1 Momentum relativo

En cada fecha:

- rankear los activos del universo;
- convertir el ranking a percentil;
- permitir entradas solo por encima de un percentil mínimo.

Valores a probar:

- percentil 50;
- percentil 60;
- percentil 70;
- percentil 80.

No usar ranking diario para rotar cartera. El ranking solo filtra señales.

---

## 8. Filtro de tendencia

La versión base requiere:

```text
cierre_usd > SMA200_usd
SMA50_usd > SMA200_usd
momentum_126 > 0
percentil_momentum >= 60
```

Variantes a probar:

### Variante A

```text
cierre_usd > SMA200_usd
```

### Variante B

```text
cierre_usd > SMA200_usd
SMA50_usd > SMA200_usd
```

### Variante C

```text
cierre_usd > SMA200_usd
pendiente_SMA200 > 0
```

### Variante D

```text
cierre_usd > máximo_móvil_252 × 0.75
```

Evitar acumular filtros redundantes sin demostrar mejora fuera de muestra.

---

## 9. Definición del retroceso

Cada condición debe evaluarse como variante independiente.

### Variante 1 — RSI(2)

```text
RSI2 < 10
```

Probar rango:

- RSI2 < 5;
- RSI2 < 10;
- RSI2 < 15;
- RSI2 < 20.

### Variante 2 — Cierres descendentes

```text
close[t] < close[t-1] < close[t-2] < close[t-3]
```

Probar:

- 2 cierres descendentes;
- 3 cierres descendentes;
- 4 cierres descendentes.

### Variante 3 — Caída acumulada

```text
retorno_5d <= -4%
```

Probar rangos:

- caída entre 3% y 8%;
- caída entre 4% y 10%;
- caída entre 5% y 12%.

### Variante 4 — Distancia a media corta

```text
distancia_SMA5 <= percentil_10_historico
```

### Variante 5 — Retroceso normalizado por volatilidad

```text
retroceso_5d / ATR14
```

Probar umbrales entre:

- -1 ATR;
- -1,5 ATR;
- -2 ATR;
- -2,5 ATR.

No combinar condiciones hasta identificar cuál aporta ventaja individual.

---

## 10. Confirmación de entrada

La señal de retroceso no debe ejecutar directamente la compra.

Probar confirmaciones:

### Confirmación A

```text
entrada cuando close[t] > high[t-1]
```

### Confirmación B

```text
entrada cuando high[t] > high[t-1]
```

### Confirmación C

```text
entrada cuando close[t] > open[t]
```

### Confirmación D

```text
entrada cuando close[t] > SMA3
```

### Confirmación E

Entrada al cierre del día de señal, sin confirmación.

La variante sin confirmación sirve como benchmark.

Evitar look-ahead:

- una señal calculada al cierre solo puede ejecutarse al cierre con una hipótesis explícita de ejecución;
- preferentemente ejecutar en apertura del día siguiente;
- documentar siempre el precio usado.

---

## 11. Filtro de liquidez

Definir liquidez mediante:

- volumen monetario promedio de 20 ruedas;
- cantidad de ruedas con volumen;
- spread estimado;
- profundidad si existe información intradiaria.

Regla base:

```text
volumen_monetario_promedio_20d >= umbral
```

El umbral debe adaptarse al capital simulado.

También exigir:

```text
tamaño_posición <= 5% del volumen monetario diario
```

Para pruebas conservadoras usar 1%.

No asumir ejecución perfecta en activos poco líquidos.

---

## 12. Reglas de salida

Evaluar cada método por separado.

### Salida 1 — Reversión corta

```text
salir cuando close > SMA5
```

### Salida 2 — RSI

```text
salir cuando RSI2 > 70
```

Probar:

- 60;
- 70;
- 80;
- 90.

### Salida 3 — Breakout

```text
salir cuando close alcanza máximo de 10 ruedas
```

### Salida 4 — Retorno objetivo

Probar:

- +4%;
- +6%;
- +8%;
- +10%;
- +12%.

### Salida 5 — Tiempo máximo

Probar:

- 5 ruedas;
- 10 ruedas;
- 15 ruedas;
- 20 ruedas;
- 30 ruedas.

### Salida 6 — Trailing stop

Probar:

- 2 ATR;
- 2,5 ATR;
- 3 ATR.

### Salida 7 — Pérdida de tendencia

```text
salir si close_usd < SMA200_usd
```

La versión base debe incluir una salida por tiempo máximo.

---

## 13. Stop loss

No asumir que un stop fijo mejora la estrategia.

Comparar:

### Sin stop intraposición

Salida únicamente por regla o tiempo.

### Stop porcentual

- -4%;
- -6%;
- -8%;
- -10%.

### Stop por volatilidad

- 1,5 ATR;
- 2 ATR;
- 2,5 ATR;
- 3 ATR.

### Stop estructural

Debajo del mínimo reciente o swing low confirmado sin look-ahead.

Medir:

- impacto en retorno;
- impacto en drawdown;
- reducción o aumento de whipsaws;
- sensibilidad al gap;
- slippage de ejecución.

---

## 14. Construcción de cartera

### 14.1 Número de posiciones

Probar:

- máximo 3 posiciones;
- máximo 5 posiciones;
- máximo 8 posiciones.

### 14.2 Asignación

Versión base:

```text
peso_por_posición = 1 / máximo_posiciones
```

Alternativas:

- igual riesgo por ATR;
- volatilidad objetivo;
- riesgo fijo por operación.

### 14.3 Riesgo por operación

Evaluar:

- 0,25% del capital;
- 0,50%;
- 0,75%;
- 1,00%.

Para capital pequeño, considerar lotes mínimos y redondeo real.

### 14.4 Exposición máxima

Definir:

- exposición máxima total;
- exposición máxima por sector;
- exposición máxima por activo;
- efectivo mínimo.

No usar apalancamiento en la primera versión.

---

## 15. Prioridad entre señales

Si existen más señales que posiciones disponibles, ordenar por:

1. percentil de momentum;
2. liquidez;
3. profundidad del retroceso normalizado por ATR;
4. menor correlación con posiciones existentes.

No reemplazar automáticamente una posición abierta por otra con mejor ranking.

La posición debe cerrarse únicamente por sus reglas de salida.

---

## 16. Frecuencia operativa

La estrategia debe diseñarse para baja rotación.

Objetivo preliminar:

- 20 a 60 operaciones anuales agregadas;
- permanencia media entre 5 y 20 ruedas;
- rotación anual controlada;
- costo anual inferior al beneficio bruto generado.

Calcular explícitamente:

```text
erosion_costos = costos_totales / beneficio_bruto
```

Descartar si:

```text
erosion_costos > 40%
```

Marcar como frágil si supera 25%.

---

## 17. Diseño experimental

### Fase 1 — Señal individual

Probar por separado:

- RSI(2);
- cierres descendentes;
- caída acumulada;
- retroceso por ATR.

Mantener fijos tendencia, salida y costos.

### Fase 2 — Confirmación

Sobre la mejor señal de retroceso, comparar confirmaciones.

### Fase 3 — Salidas

Comparar métodos de salida sin cambiar la entrada.

### Fase 4 — Cartera

Incorporar múltiples activos y límites de posiciones.

### Fase 5 — Robustez

Perturbar parámetros y costos.

### Fase 6 — Walk-forward

Validar fuera de muestra.

### Fase 7 — Paper trading

Ejecutar sin capital real.

### Fase 8 — Capital mínimo

Operar con tamaño reducido.

No optimizar todas las variables simultáneamente.

---

## 18. División temporal

Usar períodos suficientemente largos.

Ejemplo:

- entrenamiento: 2010–2018;
- validación: 2019–2021;
- prueba final: 2022–actualidad.

Si los datos son más cortos:

- usar ventanas walk-forward;
- evitar reservar menos de 20% para prueba final;
- mantener el último período completamente fuera del proceso de diseño.

Nunca modificar reglas usando resultados del test final.

---

## 19. Walk-forward

Ejemplo de esquema:

```text
train: 5 años
test: 1 año
step: 1 año
```

Alternativas:

- train 3 años / test 6 meses;
- train 4 años / test 1 año;
- train expansivo / test 6 meses.

Reportar:

- resultado por ventana;
- porcentaje de ventanas rentables;
- estabilidad de parámetros;
- degradación entre train y test;
- diferencia entre ejecución bruta y neta.

---

## 20. Robustez de parámetros

No aceptar una configuración aislada.

Ejemplo:

Si RSI2 < 10 funciona, también deberían funcionar razonablemente:

- RSI2 < 5;
- RSI2 < 15;
- RSI2 < 20.

Construir mapas de calor para:

- umbral de RSI;
- horizonte de momentum;
- SMA de tendencia;
- tiempo máximo;
- stop;
- take profit;
- costo total.

Buscar mesetas, no picos.

---

## 21. Monte Carlo

Aplicar:

- reordenamiento de operaciones;
- bootstrap de operaciones;
- variación aleatoria de slippage;
- omisión aleatoria de señales;
- retraso de entrada de una rueda;
- deterioro aleatorio del precio de ejecución.

Reportar:

- drawdown percentil 50, 75, 90 y 95;
- retorno final;
- probabilidad de pérdida;
- rachas máximas negativas;
- capital mínimo razonable.

---

## 22. Pruebas de estrés

La estrategia debe probarse bajo:

- costos duplicados;
- slippage adicional;
- entradas una rueda tarde;
- salidas una rueda tarde;
- eliminación del mejor activo;
- eliminación del mejor año;
- reducción del universo;
- períodos laterales;
- mercados bajistas;
- crisis de liquidez;
- devaluaciones bruscas;
- gaps de apertura.

Descartar si el resultado depende del mejor activo o del mejor año.

---

## 23. Benchmarks

Comparar contra:

1. buy and hold de cada activo;
2. índice Merval dolarizado;
3. cartera equiponderada del universo;
4. momentum simple;
5. SMA200 simple;
6. reversión RSI(2) sin filtro;
7. efectivo o caución;
8. combinación 50/50 entre benchmark y efectivo.

La estrategia debe justificar su complejidad.

---

## 24. Métricas obligatorias

### Rentabilidad

- retorno total;
- CAGR;
- retorno anual;
- retorno mensual;
- retorno en ARS;
- retorno en USD MEP;
- retorno real si se dispone de inflación.

### Riesgo

- volatilidad;
- maximum drawdown;
- tiempo bajo agua;
- downside deviation;
- peor mes;
- peor año;
- VaR y CVaR como métricas secundarias.

### Eficiencia

- Sharpe;
- Sortino;
- Calmar;
- profit factor;
- expectancy;
- payoff ratio;
- recovery factor.

### Operaciones

- cantidad de operaciones;
- win rate;
- ganancia media;
- pérdida media;
- duración media;
- duración mediana;
- rotación;
- costo total;
- erosión por costos;
- exposición media;
- porcentaje de tiempo invertido.

### Robustez

- porcentaje de activos rentables;
- porcentaje de años rentables;
- porcentaje de ventanas walk-forward positivas;
- degradación train-test;
- sensibilidad a parámetros;
- sensibilidad a costos.

---

## 25. Criterios de aprobación

La estrategia se considera candidata solo si cumple simultáneamente:

```text
expectativa_neta > 0
profit_factor >= 1.30
sharpe_oos >= 0.80
max_drawdown <= 25%
operaciones_historicas_agregadas >= 100
activos_rentables >= 60%
ventanas_walkforward_positivas >= 60%
erosion_costos <= 40%
```

Además:

- debe ser rentable en USD MEP;
- debe sobrevivir al escenario conservador de costos;
- debe conservar expectativa positiva al duplicar costos;
- no debe depender de un único activo;
- no debe depender de un único año;
- debe presentar una meseta de parámetros;
- debe superar al menos a un benchmark simple en relación retorno/riesgo.

---

## 26. Criterios de descarte

Descartar si ocurre cualquiera de los siguientes:

- resultado negativo en USD MEP;
- beneficio explicado principalmente por inflación o devaluación;
- costos superiores al 40% del beneficio bruto;
- más del 50% del beneficio proviene de un activo;
- más del 40% del beneficio proviene de un año;
- parámetros óptimos extremadamente estrechos;
- resultado positivo solo sin costos;
- drawdown superior a 30%;
- menos de 100 operaciones agregadas;
- degradación extrema fuera de muestra;
- profit factor inferior a 1,20;
- incapacidad de ejecutar por liquidez;
- dependencia de información futura.

---

## 27. Prevención de errores metodológicos

Prohibido:

- usar precios futuros;
- elegir activos según desempeño futuro;
- ajustar parámetros usando el test final;
- ignorar activos sin datos completos sin documentarlo;
- ejecutar al mismo cierre con información conocida únicamente después del cierre;
- usar cierre ajustado para ejecutar sin revisar el precio real;
- ignorar dividendos;
- ignorar splits;
- omitir spread;
- asumir liquidez infinita;
- rankear con datos no disponibles en la fecha;
- seleccionar solo períodos alcistas.

---

## 28. Portabilidad a Estados Unidos

La estrategia debe diseñarse con componentes abstractos.

### Argentina

- universo: acciones Merval;
- moneda: USD MEP;
- benchmark: Merval USD;
- liquidez: volumen monetario local;
- costos: broker BYMA;
- ejecución: apertura o cierre local.

### Estados Unidos

- universo: S&P 500, Russell 1000 o ETFs líquidos;
- moneda: USD;
- benchmark: SPY;
- liquidez: dollar volume;
- costos: broker estadounidense;
- ejecución: NBBO o datos equivalentes.

### Reglas que deben mantenerse

- definición de momentum;
- filtro de tendencia;
- definición de retroceso;
- confirmación;
- salida;
- control de riesgo;
- límites de cartera;
- metodología walk-forward.

Solo deben recalibrarse:

- costos;
- liquidez;
- tamaño de posición;
- universo;
- horarios;
- restricciones regulatorias.

---

## 29. Prueba cruzada en Estados Unidos

No esperar a finalizar toda la optimización argentina.

Cuando exista una versión preliminar estable:

1. congelar reglas;
2. aplicarlas sin modificar a un universo estadounidense;
3. usar costos reales de EE.UU.;
4. evaluar si la ventaja persiste;
5. comparar degradación o mejora;
6. evitar retocar reglas por país sin justificación.

Una estrategia portable debería mostrar:

- misma dirección de expectativa;
- métricas razonables en ambos mercados;
- menor erosión por costos en EE.UU.;
- mayor diversificación;
- mayor cantidad de señales sin aumentar excesivamente la rotación.

---

## 30. Arquitectura sugerida

```text
lab_momentum_pullback/
├── README.md
├── config/
│   ├── argentina.yaml
│   ├── usa.yaml
│   ├── costs.yaml
│   └── experiments.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── quality_reports/
├── src/
│   ├── data_loader.py
│   ├── mep.py
│   ├── adjustments.py
│   ├── indicators.py
│   ├── signals.py
│   ├── portfolio.py
│   ├── execution.py
│   ├── costs.py
│   ├── backtest.py
│   ├── walkforward.py
│   ├── montecarlo.py
│   ├── robustness.py
│   └── reporting.py
├── experiments/
├── results/
├── tests/
└── run_lab.py
```

---

## 31. Requisitos de implementación

- Python 3.11 o superior.
- Código modular y reutilizable.
- Configuración externa mediante YAML.
- Sin parámetros hardcodeados.
- Resultados reproducibles mediante semilla.
- Logs completos.
- Tests unitarios.
- Caché de datos.
- Separación entre señal, ejecución y cartera.
- Separación entre datos argentinos y estadounidenses.
- Backtester event-driven o vectorizado con control estricto de look-ahead.
- Exportación a CSV, JSON y Markdown.
- Gráficos separados para equity, drawdown, costos y distribución de operaciones.

---

## 32. Entregables

### Entregable 1 — Auditoría de datos

Archivo:

```text
01_data_quality_report.md
```

Debe incluir:

- cobertura;
- errores;
- activos descartados;
- calidad del MEP;
- ajustes aplicados.

### Entregable 2 — Benchmark

Archivo:

```text
02_benchmarks.md
```

### Entregable 3 — Señales de retroceso

Archivo:

```text
03_pullback_signals.md
```

### Entregable 4 — Confirmaciones

Archivo:

```text
04_entry_confirmation.md
```

### Entregable 5 — Salidas

Archivo:

```text
05_exit_rules.md
```

### Entregable 6 — Cartera

Archivo:

```text
06_portfolio_results.md
```

### Entregable 7 — Walk-forward

Archivo:

```text
07_walkforward.md
```

### Entregable 8 — Robustez

Archivo:

```text
08_robustness.md
```

### Entregable 9 — Monte Carlo

Archivo:

```text
09_montecarlo.md
```

### Entregable 10 — Portabilidad USA

Archivo:

```text
10_usa_transfer_test.md
```

### Entregable final

Archivo:

```text
FINAL_DECISION.md
```

Debe concluir únicamente con:

```text
APPROVED_FOR_PAPER
REQUIRES_MORE_RESEARCH
REJECTED
```

---

## 33. Orden de trabajo obligatorio

1. Auditar datos.
2. Construir precios USD MEP.
3. Crear benchmarks.
4. Implementar señal base.
5. Validar ausencia de look-ahead.
6. Incorporar costos.
7. Comparar variantes de retroceso.
8. Comparar confirmaciones.
9. Comparar salidas.
10. Construir cartera.
11. Ejecutar walk-forward.
12. Ejecutar robustez.
13. Ejecutar Monte Carlo.
14. Probar reglas congeladas en EE.UU.
15. Emitir decisión final.

No avanzar a optimización si la versión base no supera costos.

---

## 34. Configuración base inicial

Usar esta configuración únicamente como punto de partida:

```yaml
universe:
  - GGAL
  - YPFD
  - PAMP
  - BMA
  - BBAR
  - TXAR
  - TGSU2
  - CEPU
  - ALUA
  - BYMA

currency: USD_MEP

trend:
  price_above_sma: 200
  fast_sma: 50
  slow_sma: 200

momentum:
  lookback: 126
  min_percentile: 60
  min_absolute_return: 0

pullback:
  type: RSI2
  threshold: 10

confirmation:
  type: close_above_previous_high
  execute_on: next_open

exit:
  type: close_above_sma
  sma_period: 5
  max_holding_days: 15

risk:
  max_positions: 5
  risk_per_trade: 0.005
  max_position_weight: 0.20
  leverage: 1.0

costs:
  round_trip_base: 0.014
  round_trip_conservative: 0.018
  round_trip_stress: 0.025
```

---

## 35. Pregunta final del laboratorio

La pregunta no es:

> ¿Cuál combinación produce el mayor retorno histórico?

La pregunta correcta es:

> ¿Existe una ventaja simple, repetible, ejecutable y robusta que sobreviva a costos argentinos y conserve la misma lógica al trasladarse a Estados Unidos?
