# 10 Method Validation Report

## Status: REQUIRES_METHOD_VALIDATION (in progress)

## Benchmark
- Buy & hold USD MEP: `4.4011`

## Attribution variants (A–E)

| Var | Config | Trades | Cum Gross | Cum Net |
| --- | --- | --- | --- | --- |
| A | Momentum + RSI2 / SMA5 | 51 | 1.2066 | 0.0805 |
| B | Momentum + RSI2 / 10d fixed | 51 | 0.0336 | -0.4939 |
| C | Momentum + RSI2 / trailing 2.5 ATR | 51 | -0.7606 | -0.8828 |
| D | Momentum only / monthly rebalance | 1078 | 28.4900 | -1.0000 |
| E | Momentum + RSI2 + ATR filter / trailing 2.5 ATR | 45 | -0.3292 | -0.6427 |

## Incremental attribution M0–M4

| Model | Components | Trades | Cum Net | Δ Cum Net |
| --- | --- | --- | --- | --- |
| M0 | Trend + basic entry + trailing ATR | 1078 | -1.0000 | -1.0000 |
| M1 | M0 + momentum percentile | 1078 | -1.0000 | 0.0000 |
| M2 | M1 + RSI2 pullback | 843 | -1.0000 | 0.0000 |
| M3 | M2 + close-above-prev-high confirmation | 51 | -0.8828 | 0.1172 |
| M4 | M3 + ATR filter 2.5x | 45 | -0.9236 | -0.0408 |

## ATR trailing robustness

| ATR | Trades | Cum Net |
| --- | --- | --- |
| 2.0 | 45 | -0.7291 |
| 2.5 | 45 | -0.9236 |
| 3.0 | 45 | -0.9467 |
| 3.5 | 45 | -0.8922 |
| 4.0 | 45 | -0.9526 |

## Walk-forward: variant E

| Window | Trades | Cum Net |
| --- | --- | --- |
| first_half_2021_2023 | 19 | 0.2292 |
| second_half_2023_2026 | 16 | -0.5046 |
| full | 45 | -0.6427 |

## Next steps

1. Audit backtester accounting (cash, costs, capital)
2. Normalize benchmarks by exposure
3. Test with conservative cost scenarios
4. Paper trading eligibility assessment

