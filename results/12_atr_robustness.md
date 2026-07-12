# 12 ATR Trailing Stop Robustness

Test trailing ATR at 2.0–4.0 on variant E config.

## Results

| ATR | Trades | Gross W | Net W | Cum Gross | Cum Net | Avg Net |
| --- | --- | --- | --- | --- | --- | --- |
| 2.0 | 45 | 31 | 22 | 1.3304 | 0.2411 | 0.0068 |
| 2.5 | 45 | 31 | 22 | 1.3304 | 0.2411 | 0.0068 |
| 3.0 | 45 | 31 | 22 | 1.3304 | 0.2411 | 0.0068 |
| 3.5 | 45 | 31 | 22 | 1.3304 | 0.2411 | 0.0068 |
| 4.0 | 45 | 31 | 22 | 1.3304 | 0.2411 | 0.0068 |

## Stability assessment

- Similar results across 2.0–4.0 → robust exit.
- Only one value works → fragile / overfit.

