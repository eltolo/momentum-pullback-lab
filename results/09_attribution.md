# 09 Attribution Analysis

## Benchmark

- Equal-weight buy & hold USD MEP: `4.4011`

## Variant comparison (all at base cost 1.4% rt)

| Var | Entry / Exit | Trades | Gross W | Avg Gross | Cum Gross | Cum Net | Net W |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Momentum + RSI2 / SMA5 | 51 | 40 | 0.0170 | 1.2066 | 0.0805 | 32 |
| B | Momentum + RSI2 / 10d fixed | 51 | 31 | 0.0201 | 0.0336 | -0.4939 | 29 |
| C | Momentum + RSI2 / trailing 2.5 ATR | 51 | 22 | 0.0043 | -0.7606 | -0.8828 | 18 |
| D | Momentum only / monthly rebalance | 1078 | 561 | 0.0205 | 28.4900 | -1.0000 | 514 |
| E | Momentum + RSI2 + ATR filter / trailing 2.5 ATR | 45 | 23 | 0.0135 | -0.3292 | -0.6427 | 21 |

## What the comparison tells us

- **A vs D**: isolates pullback + exit contribution (A has both, D has neither)
- **A vs B**: isolates exit method (SMA5 vs fixed 10d)
- **A vs C**: compares SMA5 exit vs trailing ATR stop
- **D alone**: answers whether momentum-only with rebalancing is viable

## Detailed exit breakdown

### A — Momentum + RSI2 / SMA5
| Exit reason | Trades |
| --- | --- |
| close_above_sma5 | 51 |

### B — Momentum + RSI2 / 10d fixed
| Exit reason | Trades |
| --- | --- |
| fixed_days | 51 |

### C — Momentum + RSI2 / trailing 2.5 ATR
| Exit reason | Trades |
| --- | --- |
| trailing_stop_atr | 51 |

### D — Momentum only / monthly rebalance
| Exit reason | Trades |
| --- | --- |
| fixed_days | 1057 |
| end_of_data | 20 |

### E — Momentum + RSI2 + ATR filter / trailing 2.5 ATR
| Exit reason | Trades |
| --- | --- |
| trailing_stop_atr | 31 |
| max_holding_20d | 14 |

