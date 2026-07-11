# Momentum Pullback Lab

A cost-aware backtesting framework for a **momentum + pullback** strategy on BYMA (Argentina) equities, with a planned USA transfer test.

**Status:** v0.3.0 — Full pipeline from data audit to final decision. Ready for external review.

---

## What it does

1. Loads daily BYMA data from ConexAR (yfinance-backed), validates OHLC quality, converts to USD MEP
2. Computes benchmarks (equal-weight buy & hold)
3. Generates entry signals: uptrend (close > SMA200) + top-60th-percentile momentum (126d) + RSI2 pullback (< 10) + close above previous high confirmation
4. Exits: close above SMA(5) or max 15 holding days
5. Applies Argentine costs (1.4% round-trip base scenario)
6. Runs walk-forward, produces a final decision

## Results summary

| Metric | Value |
|--------|-------|
| Analysis window | 2021-03-29 → 2026-07-10 (1,294 days) |
| Tradable universe | 8 tickers: ALUA, BYMA, CEPU, GGAL, PAMP, TGSU2, TXAR, YPFD |
| Total trades | 51 |
| Avg holding | exited via close_above_sma5 (100%) |
| Benchmark (B&H) USD MEP | **+337%** (33.2% annualized) |
| Strategy gross USD MEP | +120.7% (78.4% win rate) |
| Strategy net (1.4% rt) | **+8.0%** (62.7% win rate) |

### Walk-forward

| Window | Trades | Net return | Win rate |
|--------|--------|------------|----------|
| First half (Mar21–Nov23) | 21 | **+42.3%** | 71.4% |
| Second half (Nov23–Jul26) | 20 | **-41.4%** | 40.0% |
| Full | 51 | +8.0% | 62.7% |

### Final decision

**REQUIRES_MORE_RESEARCH** — Strategy is net positive but does not clearly beat buy-and-hold (0.08x vs 4.37x). Strong regime dependency: works in first half, loses in second.

---

## Quick start

```bash
python run_lab.py --check                          # validate config
python run_lab.py --phase data_audit               # data quality gate
python run_lab.py --phase benchmarks               # benchmark returns
python run_lab.py --phase pullback_signals         # entry signals
python run_lab.py --phase entry_confirmation       # confirmed entries
python run_lab.py --phase exit_rules               # exit analysis
python run_lab.py --phase portfolio_results        # PnL with costs
python run_lab.py --phase walkforward              # regime stability
python run_lab.py --phase final_decision           # full verdict
```

Requires Python ≥3.11 and access to the ConexAR SQLite database at `~tato/proyectos/MPC_Conexar/historico_merval.db`. To run elsewhere, point `config/argentina.yaml → data.price_db_path` to your own BYMA daily OHLCV database.

## Project structure

```
├── config/               # YAML parameters (market, costs, experiments)
├── src/lab_momentum_pullback/
│   ├── adjustments.py    # Data quality audit, panel construction
│   ├── config_loader.py  # YAML loading & validation
│   ├── costs.py          # Cost scenarios (0.8%–2.5% round-trip)
│   ├── data_loader.py    # SQLite price loading
│   ├── exits.py          # Exit rule engine
│   ├── indicators.py     # SMA, RSI2, rolling returns
│   ├── mep.py            # FX series (CCL/MEP) with hierarchy fallback
│   ├── portfolio.py      # Full simulation: entries → exits → costs → PnL
│   ├── reporting.py      # Markdown report writers
│   └── signals.py        # Signal engine (trend, momentum, pullback, confirmation)
├── results/              # Generated reports (01–07 + FINAL_DECISION)
├── data/                 # Generated CSVs (gitignored)
├── run_lab.py            # CLI entrypoint
├── README.md
├── pyproject.toml
```

## Configuration

All strategy parameters live in `config/argentina.yaml`:

- **Trend:** close > SMA200
- **Momentum:** 126-day return, top 60th percentile
- **Pullback:** RSI2 < 10
- **Confirmation:** close above previous day's high
- **Exit:** close above SMA5 or max 15 days
- **Risk:** max 3 positions, position-weighted
- **Costs:** 1.4% base round-trip (0.7%/side)

## License

MIT
