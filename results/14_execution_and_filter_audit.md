# Execution and Filter Audit

## Status: REQUIRES_MORE_RESEARCH

---

## 1. Auditoría del Trailing ATR

### Hallazgo crítico: bug de unidades corregido

El trailing ATR estaba **completamente roto** por un bug de unidades. El código comparaba:

- `peak` en ARS (se alimentaba de `high_ars_raw`)
- `stop_level` = `peak - ATR_ARS * multiplier`
- `current_close` en USD MEP

Como `peak` era un número en ARS (~100) y `current_close` era en USD (~0.50), la condición `current_close < stop_level` **siempre se cumplía** desde el día 3, resultando en salidas idénticas sin importar el multiplicador.

**Fix aplicado:** convertir `peak` y ATR a USD términos usando `ratio = close_usd / close_ars`.

### Resultados post-fix

| ATR | Trades | Cum Net | Avg Hold | Salidas por trailing |
|-----|--------|---------|----------|---------------------|
| 2.0x | 45 | -72.9% | 12.7d | 100% |
| 2.5x | 45 | -92.4% | 18.8d | 100% |
| 3.0x | 45 | -94.7% | 24.7d | 94% stop / 6% max_hold |
| 4.0x | 45 | -95.3% | 35.4d | 76% stop / 24% max_hold |

**El trailing ATR ahora se activa correctamente y produce salidas diferentes por multiplicador.**

### Implicancia

Todas las variantes C y E (que usaban trailing ATR) reportaban resultados positivos debido al bug. Con el fix, **ninguna variante con trailing ATR es rentable**. La única variante positiva neta es **A (SMA5)**: +8.1% neto trade-level, +5.6% NAV.

---

## 2. Auditoría del Filtro Momentum

### Hallazgo: el filtro momentum no discrimina señales

| Métrica | Valor |
|---------|-------|
| Total filas de precio | 10.310 |
| high_momentum antes (perc=0%) | 6.261 (60.7%) |
| high_momentum después (perc=60%) | 6.261 (60.7%) |
| Señales removidas | **0 (0.0%)** |

El filtro de momentum (percentil 60 sobre mom_rank_pct) **no remueve ninguna señal**. Esto ocurre porque con solo 8 tickers y la mayoría en uptrend simultáneamente, el percentil 60 equivale aproximadamente a incluir 5 de 8 tickers cada día (~60%).

**Conclusión:** M0 y M1 son idénticos porque el filtro no discrimina. El momentum como está implementado **no aporta valor** en este universo de 8 tickers.

Para que el momentum sea discriminante, debería:
- Usar un percentil más restrictivo (p.ej. percentil 80 o 90)
- O requerir que mom_rank_pct > 0.8 (solo 1-2 tickers por día)

---

## 3. Métricas No Saturadas M0–M4

| Modelo | Trades | Cum Net | Avg Net | Profit Factor | Win Rate | Avg Hold |
|--------|-------|---------|---------|---------------|----------|----------|
| M0: Trend + entry básico | 1.078 | -100% | -0.0014 | 0.21 | 39.1% | 21d |
| M1: + momentum | 1.078 | -100% | -0.0014 | 0.21 | 39.1% | 21d |
| M2: + RSI2 pullback | 843 | -100% | -0.0022 | 0.07 | 31.2% | 9d |
| M3: + confirmación | 51 | -88.3% | -0.0247 | 0.39 | 33.3% | 18.8d |
| M4: + ATR filter | 45 | -92.4% | -0.0286 | 0.25 | 31.1% | 18.8d |

Nota: M3 y M4 usan trailing ATR 2.5x (ahora corregido). M0–M2 están saturados en -100% por exceso de trades.

---

## 4. Comparación de Confirmación

La confirmación `close > previous high` reduce trades de **843 a 51** (-94%).

Comparación con alternativas de frecuencia equivalente:

| Filtro | Señales | Reducción |
|--------|---------|-----------|
| Sin filtro (momentum+pullback) | 1.667 | base |
| Cooldown 1 día | 1.667 | 0% |
| Cooldown 5 días | 819 | -51% |
| **close > prev high (actual)** | **51** | **-97%** |

La confirmación actual es mucho más restrictiva que un simple cooldown de 1-5 días. Reduce 32x más señales que cooldown 5d. Sin embargo, incluso con este filtro agresivo, la estrategia **sigue siendo negativa** (-88.3% neto con trailing ATR).

---

## 5. Variante A — Única positiva neta

| Métrica | Valor |
|---------|-------|
| Trades | 51 |
| Gross | +120.7% |
| **Net (1.4% rt)** | **+8.1% (trade-level)** |
| **NAV return** | **+5.6%** |
| CAGR | 1.07% |
| Max DD | -21.3% |
| Exposición media | 5.3% |
| Profit factor | 1.18 |

La variante A (SMA5) es la **única** que produce retorno neto positivo. Usa salida `close > SMA5` (no trailing ATR).

---

## 6. Walk-Forward Variante E (post-fix)

| Ventana | Trades | Neto |
|---------|--------|------|
| 2021-2023 | 19 | +22.9% |
| 2023-2026 | 16 | -50.5% |
| Completo | 45 | -64.3% |

Sigue siendo inestable entre regímenes.

---

## 7. Benchmark Corregido

| Métrica | B&H USD MEP | Variante A |
|---------|-------------|-----------|
| Retorno total | +337% | +5.6% |
| CAGR | 33.2% | 1.07% |
| Exposición media | 100% | 5.3% |
| Max DD | -30.5% | -21.3% |
| Sharpe (aprox.) | 1.2 | 0.15 |

Cuando se normaliza por exposición: la variante A gana +5.6% con 5.3% exposición, equivalente a ~+106% sobre capital expuesto. Pero la comparación directa sigue siendo desfavorable.

---

## 8. Decisión

```text
REQUIRES_MORE_RESEARCH
```

### Justificación

1. **Bug de trailing ATR corregido** — todas las variantes que usaban trailing ATR ahora son negativas
2. **Única esperanza: variante A (SMA5)** — +5.6% NAV, pero no vence al benchmark ni alcanza profit factor 1.30
3. **Filtro momentum ineficaz** — no discrimina entre 8 tickers
4. **Régimen dependency** — la estrategia pierde en la segunda mitad independientemente de la configuración
5. **Siguiente paso lógico:** probar la variante A con trailing ATR corregido pero con multiplicador mucho más agresivo (1.0x–1.5x), o explorar por qué SMA5 funciona cuando trailing ATR no
