# 11 Incremental Attribution M0–M4

Each model adds exactly one component. Trailing ATR exit (2.5x) for all.

## Models

| Model | Components | Trades | Cum Gross | Cum Net | Avg Net | Δ Trades | Δ Cum Net |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | Trend + basic entry + trailing ATR | 1078 | 3.1299 | -1.0000 | -0.0106 | 1078 | -1.0000 |
| M1 | M0 + momentum percentile | 1078 | 3.1299 | -1.0000 | -0.0106 | 0 | 0.0000 |
| M2 | M1 + RSI2 pullback | 843 | 0.1059 | -1.0000 | -0.0108 | -235 | 0.0000 |
| M3 | M2 + close-above-prev-high confirmation | 51 | 1.2883 | 0.1205 | 0.0041 | -792 | 1.1205 |
| M4 | M3 + ATR filter 2.5x | 45 | 1.3304 | 0.2411 | 0.0068 | -6 | 0.1206 |

## Key questions answered

- **M0 → M1**: How much does momentum filtering add?
- **M1 → M2**: How much does RSI2 pullback add?
- **M2 → M3**: How much does close-above-prev-high confirmation add?
- **M3 → M4**: How much does ATR filter add?

