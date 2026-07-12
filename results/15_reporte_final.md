# Momentum Pullback Lab — Reporte Final

## 1. Objetivo

Evaluar una estrategia **momentum + pullback** para acciones BYMA (Argentina) en USD MEP, con costos reales argentinos (0.7%/side), y determinar si tiene una ventaja explotable.

---

## 2. Metodología

**Ventana:** 2021-03-29 → 2026-07-10 (1.294 días)
**Universo:** 8 tickers (ALUA, BYMA, CEPU, GGAL, PAMP, TGSU2, TXAR, YPFD) — filtrados de 10 iniciales (BBAR y BMA excluidos por calidad de datos)
**Costos:** 0.7% por lado (1.4% ida y vuelta) — escenario base BYMA
**Benchmark:** Equal-weight buy & hold rebalanceado diariamente en USD MEP
**Pipeline:** data_audit → benchmarks → señales → exits → portafolio → walkforward → atribución

---

## 3. Pipeline y Herramientas

Se construyó un laboratorio modular en Python:

- `data_loader.py` — carga desde SQLite (historico_merval.db de ConexAR)
- `mep.py` — tipo de cambio CCL con jerarquía de fuentes (ccl_diario → especie D)
- `adjustments.py` — auditoría de calidad de datos (tolerancia: hasta 5 OHLC inválidos por ticker)
- `indicators.py` — SMA, RSI2, rolling return, ATR
- `signals.py` — motor de señales (uptrend, momentum, pullback, confirmación)
- `exits.py` — reglas de salida (SMA5, fixed_days, trailing_stop_atr)
- `portfolio.py` — simulación con equity curve diaria (NAV, CAGR, drawdown, exposición)
- `costs.py` — escenarios de costos (base 1.4%, conservative 1.8%, stress 2.5%)
- `attribution.py` — runner de variantes congeladas + incremental M0–M4
- `reporting.py` — generación de reportes markdown
- `run_lab.py` — CLI entrypoint con 13 fases

---

## 4. Las 5 Variantes

| Var | Entrada | Salida | Trades | Bruto | **Neto (1.4% rt)** |
|-----|---------|--------|-------|-------|------------------|
| **A** | Momentum + RSI2 | **SMA5** | 51 | +120.7% | **+8.1%** ✅ |
| B | Momentum + RSI2 | 10d fijo | 51 | +3.4% | **-49.4%** |
| C | Momentum + RSI2 | trailing 2.5 ATR | 51 | -76.1% | **-88.3%** |
| D | Momentum solo | rebalanceo mensual | 1.078 | +2.933% | **-100%** |
| E | + filtro ATR | trailing 2.5 ATR | 45 | -32.9% | **-92.4%** |

**Benchmark B&H USD MEP: +337% (CAGR 33.2%)**

---

## 5. Atribución Incremental M0–M4

Cada paso agrega exactamente un componente. Salida: trailing ATR para todos.

| Modelo | Trades | Cum Net | Profit Factor | Win Rate | Hallazgo |
|--------|-------|---------|---------------|----------|----------|
| M0: trend básico | 1.078 | -100% | 0.21 | 39% | Exceso de trades, costos matan |
| M1: + momentum | 1.078 | -100% | 0.21 | 39% | **Filtro no discrimina (0% remoción)** |
| M2: + RSI2 pullback | 843 | -100% | 0.07 | 31% | Pullback solo no alcanza |
| M3: + confirmación | 51 | -88.3% | 0.39 | 33% | Reduce 94% de trades |
| M4: + ATR filter | 45 | -92.4% | 0.25 | 31% | Filtra más pero empeora |

→ **La confirmación (close > previous high) es el componente más impactante**, reduciendo trades de 843 a 51. Pero con trailing ATR, todas las variantes pierden.

---

## 6. Hallazgo Crítico: Bug de Trailing ATR

### El problema
El trailing ATR comparaba unidades inconsistentes:
- `peak` se alimentaba de `high_ars_raw` → valores en ARS (~100)
- `stop_level` = `peak - ATR_ARS × multiplier`
- `current_close` estaba en USD MEP (~0.50)

La condición `current_close < stop_level` **siempre se cumplía** desde el día 3, sin importar el multiplicador.

### El resultado
- Variantes C y E reportaban resultados positivos (**falsos positivos**)
- El ATR "robustez" mostraba resultados idénticos para 2.0–4.0x (otra señal del bug)
- El advisor lo detectó en su segunda review

### El fix
```python
ratio = current_close / close_ars
atr_usd = atr_ars * ratio
peak = max(peak, high_ars * ratio)
stop_level = peak - atr_usd * multiplier
```

### Post-fix
| ATR | Trades | Cum Net | Avg Hold |
|-----|--------|---------|----------|
| 2.0x | 45 | -72.9% | 12.7d |
| 2.5x | 45 | -92.4% | 18.8d |
| 3.0x | 45 | -94.7% | 24.7d |
| 4.0x | 45 | -95.3% | 35.4d |

**Todas las variantes con trailing ATR ahora son negativas.** El bug explicaba toda la "rentabilidad" de C y E.

---

## 7. Variante A — La Única Positiva

Con el bug corregido, solo **A (SMA5)** produce retorno neto positivo.

| Métrica | Valor |
|---------|-------|
| Retorno neto (trade-level) | +8.1% |
| NAV return | +5.6% |
| CAGR | 1.07% |
| Max drawdown | -21.3% |
| Profit factor | 1.18 |
| Exposición media | 5.3% |
| Volatilidad anualizada | 8.9% |
| Días bajo agua | 927 / 1.294 (72%) |

La variante A gana +5.6% con 5.3% de exposición promedio. Sobre capital expuesto sería ~+106%, pero la comparación directa contra B&H (+337%) es desfavorable.

---

## 8. Walk-Forward

### Variante A
| Ventana | Trades | Neto | Win Rate |
|---------|--------|------|----------|
| 2021-2023 | 21 | +42.3% | 71.4% |
| 2023-2026 | 20 | -41.4% | 40.0% |

### Variante E (post-fix)
| Ventana | Trades | Neto |
|---------|--------|------|
| 2021-2023 | 19 | +22.9% |
| 2023-2026 | 16 | -50.5% |

**Dependencia de régimen:** la estrategia funciona en 2021–2023 pero pierde fuertemente en 2023–2026, independientemente de la configuración.

---

## 9. Diagnóstico

### Lo que funciona
- **SMA5 como salida** es superior a trailing ATR y a salida fija
- **Confirmación (close > previous high)** reduce drásticamente el turnover
- **Filtro ATR** conceptualmente tiene sentido (evitar trades con poco movimiento)

### Lo que no funciona
- **Trailing ATR** produce resultados negativos con el bug corregido
- **Momentum filter** no discrimina entre 8 tickers (0% remoción)
- **Dependencia de régimen** — inconsistente entre períodos
- **Profit factor bajo** (1.18 vs 1.30 requerido)
- **No vence al benchmark** (+5.6% NAV vs +337% B&H)

---

## 10. Decisiones de las Reviews

| Review | Fecha | Decisión |
|--------|-------|----------|
| Lab pipeline | 2026-07-11 | REQUIRES_MORE_RESEARCH |
| Advisor review 1 | 2026-07-11 | REQUIRES_METHOD_VALIDATION |
| Advisor review 2 | 2026-07-11 | REQUIRES_MORE_RESEARCH |
| **Post bug-fix** | **2026-07-11** | **REJECTED** |

### Decisión final: REJECTED

La estrategia momentum + pullback sobre BYMA no es viable en su forma actual. El único resultado positivo neto (variante A: +5.6% NAV en 5 años) es insuficiente para justificar capital real: no vence al benchmark, el profit factor es bajo, y la dependencia de régimen la hace impredecible.

El bug de trailing ATR explicaba los resultados prometedores de las variantes C y E. Con el bug corregido, todas las configuraciones con trailing ATR pierden dinero.

---

## 11. Reportes Generados

| # | Archivo | Contenido |
|---|---------|-----------|
| 01 | data_quality_report.md | Calidad de datos (8/10 tickers) |
| 02 | benchmarks.md | Benchmark B&H USD MEP (+337%) |
| 03 | pullback_signals.md | Señales de entrada |
| 04 | entry_confirmation.md | Confirmación de entradas |
| 05 | exit_rules.md | Análisis de salidas |
| 06 | portfolio_results.md | Resultados de cartera |
| 07 | walkforward.md | Walk-forward variante A |
| 08 | — | (no generado) |
| 09 | attribution.md | Variantes A–E |
| 10 | method_validation.md | Validación metodológica |
| 11 | incremental.md | Atribución M0–M4 |
| 12 | atr_robustness.md | Robustez trailing ATR |
| 13 | walkforward_variant_e.md | Walk-forward variante E |
| **14** | **execution_and_filter_audit.md** | **Auditoría final (bug fix + métricas)** |
| — | FINAL_DECISION.md | Decisión final |

---

## 12. Lecciones

1. **Validar unidades siempre.** El bug de ARS vs USD pasó desapercibido por semanas y afectó todos los resultados de las variantes C y E.
2. **Las 2 reviews del advisor fueron acertadas.** Detectaron el problema de unidades, la saturación en -100%, y la falta de discriminación del filtro momentum.
3. **La confirmación close > previous high es el hallazgo más valioso del lab** — reduce trades 94% y es el único filtro que realmente cambia el resultado.
4. **Con 8 tickers, un filtro de momentum por percentil no discrimina.** Se necesitaría un universo más grande o un filtro más restrictivo.
