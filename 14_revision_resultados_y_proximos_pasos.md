# Revisión de Resultados 11–13 y Decisión Actualizada

## Estado actual

Los nuevos resultados muestran avances, pero la estrategia todavía no está lista para paper trading.

La decisión correcta continúa siendo:

```text
REQUIRES_MORE_RESEARCH
```

El problema central es la falta de estabilidad temporal de la variante E y la ausencia de evidencia de que el trailing ATR esté funcionando realmente.

---

# 1. Hallazgos confirmados

## 1.1 La confirmación reduce drásticamente la frecuencia

| Modelo | Componentes | Trades | Neto acumulado |
|---|---|---:|---:|
| M0 | Tendencia + entrada básica + trailing ATR | 1078 | -100% |
| M1 | M0 + momentum | 1078 | -100% |
| M2 | M1 + RSI2 pullback | 843 | -100% |
| M3 | M2 + confirmación sobre máximo previo | 51 | +12.05% |
| M4 | M3 + filtro ATR | 45 | +24.11% |

La transición M2 → M3 es el cambio más importante. La confirmación `close > previous high` reduce las operaciones de 843 a 51 y evita gran parte de la destrucción por costos.

Todavía no está demostrado que aporte información predictiva; puede estar funcionando principalmente como filtro de frecuencia.

## 1.2 El filtro ATR parece mejorar el resultado

La transición M3 → M4 reduce de 51 a 45 operaciones y mejora el neto de +12.05% a +24.11%.

Esto sugiere que evitar operaciones cuyo movimiento potencial no cubre ampliamente los costos puede aportar valor.

## 1.3 La variante E no es estable temporalmente

| Ventana | Trades | Neto acumulado |
|---|---:|---:|
| 2021–2023 | 19 | +51.59% |
| 2023–2026 | 16 | -47.64% |
| Completo | 45 | +24.11% |

La segunda mitad destruye gran parte de la ganancia de la primera. La variante E no corrige la inestabilidad temporal.

---

# 2. Alerta crítica: el trailing ATR puede no estar activo

Los resultados entre ATR 2.0 y 4.0 son exactamente iguales.

Esto no debe interpretarse como robustez. Puede significar:

1. El trailing ATR nunca se activa.
2. Otra regla cierra siempre antes.
3. El parámetro no llega correctamente al motor.
4. Se reutilizan las mismas salidas.
5. El stop se calcula siempre con el mismo multiplicador.

Por cada operación registrar:

```text
symbol
entry_date
entry_price
exit_date
exit_price
exit_reason
atr_multiplier
atr_at_entry
highest_price_since_entry
trailing_stop_level
max_holding_days
bars_held
```

También generar un conteo de salidas por motivo para cada multiplicador.

Si ninguna operación sale por trailing ATR:

```text
TRAILING_ATR_INACTIVE
```

---

# 3. La atribución incremental necesita métricas no saturadas

M0, M1 y M2 llegan a -100%. Una vez alcanzado ese piso, el retorno acumulado deja de medir diferencias.

Cada modelo debe reportar además:

- retorno bruto medio por operación;
- retorno neto medio;
- profit factor;
- win rate;
- duración media;
- turnover;
- costos totales;
- costos por año;
- retorno por 100 operaciones;
- resultado con tamaño fijo por trade;
- drawdown antes de alcanzar -100%;
- exposición media.

---

# 4. El momentum todavía no está correctamente atribuido

M0 y M1 son idénticos.

Debe verificarse:

```text
signals_before_momentum
signals_after_momentum
signals_removed_by_momentum
```

Si no elimina señales:

```text
MOMENTUM_FILTER_NON_DISCRIMINANT
```

No debe concluirse que momentum no aporta valor hasta probar una configuración donde realmente modifique el universo.

---

# 5. La confirmación debe compararse con filtros de frecuencia equivalentes

Comparar variantes que generen aproximadamente 40–60 trades:

- `close > previous high`;
- espera fija de una rueda;
- cooldown;
- selección aleatoria de 51 señales entre las 843;
- filtro de liquidez;
- filtro de ATR porcentual;
- `close > open`.

Si la confirmación actual supera consistentemente alternativas con frecuencia similar, entonces existe evidencia de valor predictivo.

---

# 6. Comparación correcta con benchmark

Usar unidades inequívocas:

```text
Benchmark initial equity: 1.0000
Benchmark final equity: 4.3718
Benchmark total return: +337.18%

Strategy base initial equity: 1.0000
Strategy base final equity: 1.0805
Strategy base total return: +8.05%

Variant E initial equity: 1.0000
Variant E final equity: 1.2411
Variant E total return: +24.11%
```

Comparar también:

- CAGR;
- volatilidad;
- drawdown;
- exposición media;
- retorno sobre capital expuesto;
- benchmark con igual exposición.

---

# 7. Investigación de régimen

Tiene sentido investigar régimen únicamente después de completar las auditorías anteriores.

Primero clasificar operaciones según:

- índice sobre o debajo de SMA200;
- pendiente de SMA200;
- amplitud del mercado;
- volatilidad realizada;
- ATR promedio;
- correlación promedio;
- liquidez;
- tendencia del benchmark;
- dispersión de retornos;
- velocidad de recuperación de pullbacks.

Preguntas:

```text
¿En qué contexto gana?
¿En qué contexto pierde?
¿Qué diferencia 2021–2023 de 2023–2026?
```

No usar HMM, Markov ni ML todavía.

---

# 8. Orden de trabajo obligatorio

1. Auditar el trailing ATR.
2. Auditar que momentum realmente filtre señales.
3. Recalcular M0–M4 con métricas no saturadas.
4. Comparar confirmaciones con igual frecuencia.
5. Corregir unidades del benchmark y estrategia.
6. Analizar la degradación temporal de la variante E.
7. Evaluar variables simples de régimen.
8. Actualizar la decisión final.

---

# 9. Criterios para avanzar a paper trading

```text
trailing_ATR_validated = true
momentum_filter_audited = true
confirmation_predictive_value = demonstrated
walkforward_positive_windows >= 60%
profit_factor_oos >= 1.30
expectancy_oos > 0
max_drawdown <= 25%
parameter_stability = true
cost_stress_positive = true
```

Además:

- la segunda mitad no debe ser fuertemente negativa;
- ningún período debe explicar casi todo el resultado;
- ningún activo debe explicar más del 40% del beneficio;
- debe sobrevivir a retrasos de entrada y slippage adicional;
- debe funcionar con costos conservadores.

---

# 10. Decisión actualizada

```text
REQUIRES_MORE_RESEARCH
```

Justificación:

- la variante E pierde fuertemente en la segunda mitad;
- el trailing ATR puede estar inactivo;
- M0–M4 están afectados por saturación en -100%;
- no está demostrado que la confirmación aporte capacidad predictiva;
- el filtro momentum puede no discriminar;
- las métricas de benchmark y estrategia usan unidades inconsistentes.

---

# 11. Próximo entregable

Crear:

```text
results/14_execution_and_filter_audit.md
```

Debe incluir:

1. auditoría del trailing ATR;
2. motivos de salida por multiplicador;
3. conteo de señales antes y después de momentum;
4. métricas no saturadas M0–M4;
5. comparación de confirmaciones con frecuencia equivalente;
6. unidades corregidas;
7. decisión revisada.

Valores permitidos:

```text
APPROVED_FOR_PAPER
REQUIRES_MORE_RESEARCH
REJECTED
```
