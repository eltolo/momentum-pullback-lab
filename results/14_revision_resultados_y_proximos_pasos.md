# Revisión de resultados y próximos pasos

## Resumen del laboratorio

Backtest de una estrategia **momentum + pullback** sobre acciones BYMA en USD MEP.
Ventana: 2021-03-29 → 2026-07-10 (1.294 días).
8 tickers: ALUA, BYMA, CEPU, GGAL, PAMP, TGSU2, TXAR, YPFD.
Costos: 0.7% por lado (1.4% ida y vuelta, escenario base BYMA).

---

## Las 5 variantes

| Var | Entrada | Salida | Trades | Bruto | Neto (1.4% rt) |
|-----|---------|--------|-------|-------|----------------|
| A | Momentum + RSI2 | SMA5 | 51 | +120.7% | **+8.0%** |
| B | Momentum + RSI2 | 10d fijo | 51 | +3.4% | **-49.4%** |
| C | Momentum + RSI2 | trailing 2.5 ATR | 51 | +128.8% | **+12.1%** |
| D | Momentum solo | rebalanceo mensual | 1.078 | +2.933% | **-100%** |
| **E** | **+ filtro ATR 2.5x** | **trailing 2.5 ATR** | **45** | **+133.0%** | **+24.1%** |

Benchmark B&H: **+337%** USD MEP (33.2% anualizado).

---

## Métricas de cartera (variante A con equity curve)

| Métrica | Valor |
|---------|-------|
| NAV final | $5.719 (capital inicial $5.000) |
| Retorno total | +14.4% |
| CAGR | 2.65% |
| Máximo drawdown | -11.6% |
| Volatilidad anualizada | 5.0% |
| Exposición media | 3.0% |
| Exposición máxima | 84.3% |
| Días bajo agua | 626 (de 1.294) |
| Profit factor | 1.18 |

> La estrategia está invertida ~10% del tiempo. El retorno sobre capital expuesto es muy superior al retorno sobre capital total.

---

## Atribución incremental (M0→M4)

Cada modelo agrega un componente. Salida: trailing ATR para todos.

| Modelo | Trades | Neto | Δ Neto |
|--------|-------|------|--------|
| M0: Trend + entrada básica | 1.078 | -100% | base |
| M1: + momentum | 1.078 | -100% | 0% |
| M2: + RSI2 pullback | 843 | -100% | 0% |
| **M3: + close > prev high** | **51** | **+12.1%** | **+112%** |
| **M4: + filtro ATR 2.5x** | **45** | **+24.1%** | **+12%** |

**Hallazgo clave:** la confirmación (close above previous high) es el componente individual más impactante. Sin ella, la estrategia genera demasiadas entradas y los costos destruyen todo. El filtro ATR duplica el resultado.

---

## Walk-forward: variante E

| Ventana | Trades | Neto | Win rate |
|---------|-------|------|----------|
| 2021-2023 | 19 | **+51.6%** | 57.9% |
| 2023-2026 | 16 | **-47.6%** | 12.5% |
| Completo | 45 | +24.1% | 48.9% |

La estrategia sigue siendo inestable entre regímenes: funciona en la primera mitad, pierde en la segunda.

---

## Diagnóstico

### Lo que funciona
1. **Trailing ATR** es superior a SMA5 y a salida fija
2. **Filtro ATR** mejora la selección de entradas
3. **Confirmación (close > prev high)** reduce drásticamente el turnover

### Lo que no funciona
1. **Dependencia de régimen** — la estrategia gana en un período y pierde en otro
2. **Exposición muy baja** — solo 3% promedio, el capital pasa 90% del tiempo en cash
3. **Profit factor bajo** (1.18) — no alcanza el umbral de 1.30 del advisor
4. **No vence al benchmark** — +14.4% NAV vs +337% B&H

### La variante E como mejor candidata
- +24.1% neto acumulado
- 45 trades en 5 años (~9/año)
- Filtro ATR correctamente dimensionado (ATR_pct × 2.5 > costo)
- ATR trailing estable entre 2.0x y 4.0x

---

## Próximos pasos

### Prioridad 1 — Validación metodológica
- [ ] Normalizar benchmark por exposición (comparar contra B&H con 3% exposición)
- [ ] Probar costos conservadores (1.8% rt) y stress (2.5% rt)
- [ ] Probar slippage adicional y entrada diferida 1 rueda
- [ ] Auditar contabilidad de cartera: posiciones simultáneas, cash, costos acumulados

### Prioridad 2 — Mejora de la estrategia
- [ ] Investigar filtro de régimen simple (SMA200, volatilidad, ATR medio del mercado)
- [ ] Probar trailing ATR con trailing dinámico (ajustar múltiplo según volatilidad)
- [ ] Evaluar take profit parcial (dejar correr con trailing + tomar ganancias parciales)

### Prioridad 3 — Decisión
- [ ] Si supera validaciones: **APPROVED_FOR_PAPER** (3 meses paper trading)
- [ ] Si no supera: **REJECTED** o reformular approach

---

## Links a reportes

- [Attribution variants A–E](09_attribution.md)
- [Method validation](10_method_validation.md)
- [Incremental attribution M0–M4](11_incremental.md)
- [ATR trailing robustness](12_atr_robustness.md)
- [Walk-forward variant E](13_walkforward_variant_e.md)
- [Final decision](FINAL_DECISION.md)
