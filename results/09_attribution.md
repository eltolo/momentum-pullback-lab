# Attribution Lab — Resultados para revisión

## Resumen ejecutivo

Backtest de una estrategia **momentum + pullback** sobre acciones BYMA (Argentina) en USD MEP, ventana `2021-03-29 → 2026-07-10` (1.294 días). Se probaron 5 variantes congeladas para aislar qué componente de la estrategia aporta ventaja.

Benchmark: **+337%** USD MEP (buy & hold ponderado, 33.2% anualizado).

## Las 5 variantes

| Var | Entrada | Salida | Trades | Bruto | **Neto (1.4% rt)** |
|-----|---------|--------|-------|-------|------------------|
| A | Momentum + RSI2 | SMA5 | 51 | +120.7% | **+8.0%** |
| B | Momentum + RSI2 | 10 días fijo | 51 | +3.4% | **-49.4%** |
| C | Momentum + RSI2 | trailing 2.5 ATR | 51 | +128.8% | **+12.1%** |
| D | Momentum solo | rebalanceo mensual | 1.078 | +2.933% | **-100%** |
| **E** | **Momentum + RSI2 + filtro ATR 2.5x** | **trailing 2.5 ATR (3-20d)** | **45** | **+133.0%** | **+24.1%** |

Costos aplicados: 0.7% por lado (1.4% ida y vuelta, escenario base argentino BYMA).

## Conclusiones

### 1. El edge NO viene del momentum solo
La variante D hace 1.078 trades y los costos la destruyen por completo: +2.933% bruto se convierte en -100% neto. El turnover mensual es letal en Argentina.

### 2. La salida es el factor diferencial
- **Trailing ATR** (C): +12.1% neto ← exit inteligente que deja correr ganancias
- **SMA5** (A): +8.0% neto ← aceptable pero corta trades buenos
- **10 días fijo** (B): -49.4% neto ← catastrófico, fuerza salidas en el peor momento

### 3. El filtro ATR mejora significativamente
La variante E agrega un filtro de entrada: solo opera si `ATR(14) × 2.5 > costo round-trip`. Esto elimina 6 trades con poco movimiento esperado y **duplica el neto** (de +12.1% a +24.1%).

### 4. El pullback + confirmación es indispensable
Sin RSI2 ni confirmación (D), el turnover se dispara y los costos aniquilan cualquier ganancia.

## Walk-forward

| Ventana | Trades | Neto | Win rate |
|---------|--------|------|----------|
| 1ra mitad (2021-2023) | 21 | **+42.3%** | 71.4% |
| 2da mitad (2023-2026) | 20 | **-41.4%** | 40.0% |
| Completo | 51 | +8.0% | 62.7% |

La estrategia funciona bien en ciertos regímenes de mercado y pierde en otros.

## Preguntas para el asesor

1. **¿Tiene sentido explorar detección de régimen** para evitar la segunda mitad (donde la estrategia pierde -41%)?
2. **¿El trailing ATR 2.5 es el parámetro óptimo** o conviene probar 2.0/3.0/4.0?
3. **¿Vale la pena seguir refinando** o es más sensato descartar y buscar otro approach? El neto de +24% es positivo pero no se acerca al benchmark (+337%).
4. **¿Tiene sentido un paper trading** con la variante E para validar en vivo?
5. **¿La muestra de 45 trades es suficiente** para tomar una decisión?

## Cómo reproducir

```bash
git clone https://github.com/eltolo/momentum-pullback-lab.git
cd momentum-pullback-lab
pip install pandas pyyaml
# Configurar config/argentina.yaml → data.price_db_path con DB BYMA local
python run_lab.py --phase attribution
```

El reporte completo se genera en `results/09_attribution.md`.

## Estructura del repo

- `src/lab_momentum_pullback/attribution.py` — runner de variantes
- `src/lab_momentum_pullback/signals.py` — motor de señales
- `src/lab_momentum_pullback/exits.py` — reglas de salida (SMA, trailing ATR, fixed)
- `src/lab_momentum_pullback/costs.py` — escenarios de costos
- `src/lab_momentum_pullback/portfolio.py` — simulación completa
- `config/argentina.yaml` — parámetros de la estrategia
- `config/costs.yaml` — escenarios de costos
- `results/09_attribution.md` — reporte de atribución
- `results/FINAL_DECISION.md` — decisión final del lab
