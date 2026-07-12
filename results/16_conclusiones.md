# Momentum Pullback Lab — Conclusiones

## Proyecto cerrado

---

## Decisión final: REJECTED

La estrategia momentum + pullback sobre BYMA (Argentina) no es viable para capital real en su forma actual.

---

## Resumen de las 5 variantes

| Var | Entrada | Salida | Trades | Bruto | Neto (1.4% rt) |
|-----|---------|--------|-------|-------|----------------|
| **A** | Momentum + RSI2 | SMA5 | 51 | +120.7% | **+8.1%** |
| B | Momentum + RSI2 | 10d fijo | 51 | +3.4% | **-49.4%** |
| C | Momentum + RSI2 | trailing ATR 2.5x | 51 | -76.1% | **-88.3%** |
| D | Momentum solo | rebalanceo mensual | 1.078 | +2.933% | **-100%** |
| E | + filtro ATR 2.5x | trailing ATR 2.5x | 45 | -32.9% | **-92.4%** |

Benchmark B&H USD MEP: **+337%**

---

## Métricas clave (variante A)

| Métrica | Valor |
|---------|-------|
| Retorno neto (trade-level) | +8.1% |
| NAV return | +5.6% |
| CAGR | 1.07% |
| Max drawdown | -21.3% |
| Profit factor | 1.18 |
| Exposición media | 5.3% |
| Trades por año | ~10 |
| Período | 5 años (2021–2026) |

---

## Por qué se rechaza

1. **No vence al benchmark.** La estrategia rinde +5.6% NAV vs +337% de buy & hold.

2. **Profit factor insuficiente.** 1.18 vs el mínimo de 1.30 requerido para estrategias discrecionales.

3. **Dependencia de régimen.** Gana en 2021–2023 (+42.3%) y pierde en 2023–2026 (-41.4%). No hay estabilidad temporal.

4. **Bug crítico corregido.** El trailing ATR comparaba ARS vs USD. Antes del fix, las variantes C y E reportaban ganancias falsas. Post-fix, todas pierden con trailing ATR.

5. **Filtro momentum ineficaz.** Con solo 8 tickers, el percentil 60 no discrimina ninguna señal.

6. **Exposición muy baja.** La estrategia está invertida solo 5.3% del tiempo. El 95% del capital está en efectivo.

---

## Lo que aprendimos

- SMA5 como salida supera a trailing ATR y a salida fija
- La confirmación (close > previous high) es el filtro más potente: reduce 94% de los trades
- Con universos pequeños (< 20 tickers), los filtros por percentil no funcionan
- Los costos argentinos (0.7%/side) castigan severamente estrategias de alta frecuencia
- Un bug de unidades invalidó semanas de trabajo — las 2 reviews del advisor tenían razón

---

## Próximos pasos sugeridos

- Explorar breakout en lugar de pullback (entrar cuando cruza resistencia en lugar de esperar caída)
- Probar en USA donde los costos son 0.1%/side (el transfer test del spec original)
- Usar un universo más grande (> 100 tickers) para que el filtro momentum discrimine
- Investigar por qué SMA5 funciona cuando trailing ATR no (¿corte rápido vs trailing lento?)

---

## Reportes

Todos los reportes están en `results/`:

| Archivo | Contenido |
|---------|-----------|
| 09_attribution.md | Variantes A–E |
| 10_method_validation.md | Validación metodológica |
| 11_incremental.md | Atribución M0–M4 |
| 12_atr_robustness.md | Robustez trailing ATR |
| 13_walkforward_variant_e.md | Walk-forward variante E |
| 14_execution_and_filter_audit.md | Auditoría final |
| 15_reporte_final.md | Reporte completo |
| FINAL_DECISION.md | Decisión final |

---

*Lab cerrado el 2026-07-11*
