# Revisión Metodológica del Laboratorio 09

## Estado de la investigación

La variante E presenta una mejora aparente respecto de las variantes anteriores, pero todavía no existe evidencia suficiente para afirmar que el sistema posee una ventaja robusta y explotable.

Antes de investigar regímenes, incorporar Machine Learning o iniciar paper trading, deben resolverse varios problemas metodológicos.

La decisión actual debe ser:

```text
REQUIRES_METHOD_VALIDATION
```

---

# 1. Conclusiones que sí están respaldadas

El laboratorio permite afirmar lo siguiente:

1. La variante A tiene una ventaja bruta pequeña y los costos consumen la mayor parte del resultado.
2. La salida fija a 10 días no funciona en esta muestra.
3. El trailing ATR parece superior a la salida SMA5 dentro de la muestra completa.
4. Evitar operaciones cuyo movimiento potencial es pequeño respecto de los costos parece prometedor.
5. La configuración base presenta una degradación temporal muy fuerte.

---

# 2. Conclusiones que todavía no están demostradas

No puede afirmarse todavía que:

- la variante E sea robusta;
- el momentum no aporte valor;
- el pullback sea indispensable;
- ATR 2.5 sea el parámetro correcto;
- exista un régimen de mercado claramente identificable;
- el retorno de +24.1% sea comparable directamente con el benchmark de +337%;
- el sistema esté listo para paper trading.

---

# 3. Problema principal: la variante E no está validada fuera de muestra

El walk-forward informado corresponde a la estrategia base de 51 operaciones.

La variante E tiene:

- 45 operaciones;
- +24.1% neto;
- filtro ATR;
- trailing ATR;
- permanencia de 3 a 20 días.

Sin embargo, no se presenta su comportamiento por ventanas temporales.

Por lo tanto, hoy sabemos:

- la variante base es temporalmente inestable;
- la variante E mejora el resultado completo;
- no sabemos si E corrige la inestabilidad o si elimina operaciones malas observadas dentro de la misma muestra.

Este es actualmente el mayor riesgo de sobreajuste.

---

# 4. Verificación obligatoria del filtro ATR

El filtro informado es:

```text
ATR(14) × 2.5 > costo round-trip
```

Debe verificarse que ambas variables estén expresadas en la misma unidad.

El costo round-trip es un porcentaje.

El ATR tradicional está expresado en unidades de precio.

La comparación correcta debería usar ATR porcentual:

```text
ATR_pct = ATR14 / precio
```

Luego:

```text
ATR_pct × 2.5 > costo_round_trip
```

Ejemplo:

```text
2.5 × ATR14 / close > 0.014
```

Una formulación más general sería:

```text
movimiento_esperado > costos + margen_de_seguridad
```

Si el backtester compara ATR absoluto contra un porcentaje, la variante E debe considerarse inválida hasta corregir el cálculo.

---

# 5. Auditoría de las métricas de cartera

Los retornos reportados deben aclarar si representan:

- suma de retornos por operación;
- capital compuesto;
- cartera con posiciones simultáneas;
- retorno sobre capital total;
- retorno sobre capital invertido;
- retorno sobre capital promedio expuesto.

No se debe comparar directamente una estrategia intermitente con un benchmark permanentemente invertido sin normalizar exposición o riesgo.

## Métricas obligatorias

Incorporar:

- equity curve diaria;
- capital inicial y final;
- CAGR;
- máximo drawdown;
- exposición media;
- exposición máxima;
- retorno sobre capital total;
- retorno sobre capital expuesto;
- volatilidad;
- tiempo bajo agua;
- costos acumulados;
- rotación;
- posiciones simultáneas;
- efectivo medio.

---

# 6. La variante D no descarta el factor momentum

La variante D cambia simultáneamente:

- entrada;
- salida;
- frecuencia;
- confirmación;
- rotación;
- construcción de cartera.

Por lo tanto, únicamente permite concluir:

> Esa implementación de momentum con rebalanceo mensual y costos BYMA no es viable.

No permite concluir que el factor momentum no agregue valor.

## Comparación correcta

Crear una nueva variante:

```text
F = Tendencia + Pullback + Confirmación + Trailing ATR
```

Compararla contra:

```text
C = Tendencia + Momentum + Pullback + Confirmación + Trailing ATR
```

La única diferencia entre ambas debe ser el filtro momentum.

Así se mide su contribución incremental.

---

# 7. El pullback tampoco está aislado correctamente

La comparación entre C y D no mide exclusivamente el aporte del pullback.

Para validar el pullback se necesita comparar:

```text
Momentum + Pullback + Confirmación + Trailing ATR
```

contra:

```text
Momentum + Entrada básica o breakout + Trailing ATR
```

Manteniendo iguales:

- universo;
- costos;
- cartera;
- salida;
- tamaño;
- liquidez;
- período;
- límites de posiciones.

---

# 8. Nuevo orden de trabajo

## Paso 1 — Auditoría del backtester

Verificar:

- cálculo de capital compuesto;
- simultaneidad de posiciones;
- aplicación de costos;
- redondeo;
- tamaño de posiciones;
- capital disponible;
- exposición máxima;
- ausencia de capital negativo;
- ausencia de doble cobro de comisiones;
- ejecución de entrada y salida;
- unidad utilizada por el filtro ATR;
- tratamiento de gaps;
- ausencia de look-ahead;
- tratamiento de días sin liquidez.

La variante D debe revisarse especialmente porque pasa de +2933% bruto a -100% neto.

Confirmar que esto provenga realmente de rotación y costos, y no de un error contable.

---

## Paso 2 — Walk-forward de la variante E

Congelar completamente la variante E.

No modificar parámetros.

Evaluarla por ventanas temporales.

Ejemplo:

```text
Ventana 1: 2021–2022
Ventana 2: 2023–2024
Ventana 3: 2025–2026
```

O mediante esquema rodante:

```text
train: 3 años
test: 1 año
step: 1 año
```

En cada ventana reportar:

- operaciones;
- retorno bruto;
- retorno neto;
- CAGR;
- expectativa;
- profit factor;
- win rate;
- drawdown;
- exposición;
- costos;
- operaciones rechazadas por el filtro ATR.

---

## Paso 3 — Robustez del trailing ATR

Probar una grilla predefinida:

```text
2.0
2.5
3.0
3.5
4.0
```

El objetivo no es seleccionar el máximo retorno.

El objetivo es encontrar una zona estable.

Resultado deseado:

```text
ATR 2.5, 3.0 y 3.5 muestran resultados similares
```

Resultado sospechoso:

```text
solo ATR 2.5 funciona
```

---

## Paso 4 — Robustez del filtro de movimiento esperado

Probar:

```text
ATR_pct × multiplicador > costo_round_trip
```

Multiplicadores:

```text
1.5
2.0
2.5
3.0
3.5
4.0
```

Comparar también contra:

```text
ATR_pct > costo_round_trip × margen
```

Márgenes:

```text
1.5
2.0
3.0
4.0
```

Evaluar:

- cantidad de operaciones eliminadas;
- expectativa de operaciones aceptadas;
- expectativa de operaciones rechazadas;
- impacto por ventana temporal;
- estabilidad por activo.

---

# 9. Atribución verdaderamente incremental

Construir una secuencia donde cada modelo agregue exactamente un componente.

## M0 — Base

```text
Tendencia
Entrada básica
Trailing ATR
```

## M1 — Momentum

```text
M0 + Momentum
```

## M2 — Pullback

```text
M1 + Pullback
```

## M3 — Confirmación

```text
M2 + Confirmación
```

## M4 — Movimiento esperado

```text
M3 + Filtro Expected Move
```

Para cada paso medir:

- retorno incremental;
- expectativa incremental;
- reducción o aumento de trades;
- costo incremental;
- drawdown incremental;
- estabilidad temporal;
- estabilidad entre activos.

No avanzar si el nuevo componente mejora únicamente el período completo pero empeora la mayoría de ventanas.

---

# 10. Benchmarks correctos

Comparar la variante E contra:

1. buy and hold;
2. buy and hold ajustado a igual volatilidad;
3. benchmark con igual exposición media;
4. SMA200;
5. momentum simple de baja frecuencia;
6. cartera equiponderada;
7. efectivo cuando la estrategia no está invertida;
8. estrategia base sin filtro ATR;
9. estrategia base sin momentum;
10. estrategia base sin pullback.

La comparación principal debe usar:

- mismo capital inicial;
- misma base temporal;
- misma moneda;
- costos reales;
- retorno diario de cartera;
- exposición comparable.

---

# 11. Criterios para aprobar la variante E

La variante E podrá avanzar únicamente si cumple:

```text
expectativa_neta > 0
profit_factor >= 1.30
walkforward_positivo >= 60% de las ventanas
max_drawdown <= 25%
resultado_positivo_en_activos >= 60%
estabilidad_parametros = verdadera
costos_correctamente_modelados = verdadero
filtro_ATR_correctamente_dimensionado = verdadero
```

Además:

- ninguna ventana individual debe explicar la mayor parte del beneficio;
- ningún activo debe explicar más del 40% del resultado;
- debe sobrevivir a costos conservadores;
- debe sobrevivir a retrasar la entrada una rueda;
- debe sobrevivir a slippage adicional;
- debe mantener resultados razonables entre ATR 2.0 y 4.0.

---

# 12. Paper trading

No iniciar paper trading todavía.

Requisitos previos:

1. auditoría del backtester completada;
2. filtro ATR validado en porcentaje;
3. walk-forward de la variante E;
4. atribución incremental;
5. estabilidad del trailing;
6. equity curve diaria correcta;
7. resultados robustos con costos conservadores.

Una vez superados:

```text
paper trading mínimo: 3 meses
```

Durante paper trading medir:

- señales generadas;
- señales ejecutables;
- spread real;
- slippage;
- diferencias entre backtest y ejecución;
- operaciones omitidas por liquidez;
- retraso de datos;
- costos reales.

---

# 13. Investigación de régimen

No implementar HMM, Markov o ML todavía.

Primero comprobar si la degradación temporal puede explicarse mediante variables simples:

- índice sobre SMA200;
- amplitud del mercado;
- volatilidad;
- ATR medio;
- correlación media;
- liquidez;
- tendencia del benchmark;
- velocidad de recuperación de pullbacks;
- dispersión de retornos.

Solo si estas variables muestran relación estable con el resultado se justifica crear un filtro de régimen.

El detector debe surgir de una explicación económica y no de una búsqueda automática de estados.

---

# 14. Decisión final actual

La estrategia no debe ser descartada.

La estrategia tampoco debe ser aprobada.

La variante E contiene señales prometedoras, pero su mejora todavía puede provenir de:

- problemas de unidades;
- optimización dentro de muestra;
- comparación incorrecta;
- atribución incompleta;
- errores de contabilidad de cartera.

Decisión:

```text
REQUIRES_METHOD_VALIDATION
```

---

# 15. Próximo entregable

Crear:

```text
results/10_method_validation.md
```

Debe incluir:

1. auditoría de unidades del filtro ATR;
2. definición exacta del retorno de cartera;
3. equity curve diaria;
4. walk-forward de la variante E;
5. robustez ATR 2.0–4.0;
6. atribución incremental M0–M4;
7. benchmarks normalizados;
8. decisión actualizada.

Valores permitidos:

```text
APPROVED_FOR_PAPER
REQUIRES_MORE_RESEARCH
REJECTED
```
