from __future__ import annotations

from typing import Any

import pandas as pd

from .costs import apply_entry_cost, apply_exit_cost, CostScenario, load_cost_scenarios
from .exits import compute_exits
from .signals import compute_signals


def simulate_portfolio(
    panel: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Full portfolio simulation: entries → exits → costs → PnL.

    Returns dict with entry_log, exit_log, trades_df, and summary per scenario.
    """
    # 1. Generate signals
    signals = compute_signals(panel, config)
    entries = signals[signals["entry_signal"] == 1].copy()
    if entries.empty:
        return {"entry_log": pd.DataFrame(), "exit_log": pd.DataFrame(),
                "trades": pd.DataFrame(), "scenarios": {}}

    risk = config.get("risk", {})
    max_positions = int(risk.get("max_positions", 3))
    capital_scale = float(config.get("liquidity", {}).get("capital_scales_usd_mep", [10000])[0])
    position_size = capital_scale / max_positions

    # 2. Entry: filter by max_positions (rank by momentum, take top N)
    entries = entries.sort_values(["date", "mom_rank_pct"], ascending=[True, False])
    entry_log = []
    for _date, day_entries in entries.groupby("date", sort=True):
        candidates = day_entries.head(max_positions)
        for _, row in candidates.iterrows():
            entry_log.append({
                "date": row["date"],
                "ticker": row["ticker"],
                "entry_price": row["close_usd_mep_adj"],
                "entry_close_usd": row["close_usd_mep_adj"],
                "momentum_126d": row.get("momentum_126d", 0.0),
                "rsi2": row.get("rsi2", None),
            })
    entry_df = pd.DataFrame(entry_log)

    # 3. Compute exits
    exit_df = compute_exits(entry_df, panel, config)

    # 4. Build trades table and simulate under each cost scenario
    trades = pd.DataFrame()
    scenarios = {}
    cost_scenarios = load_cost_scenarios(config.get("costs", {})) or [
        CostScenario(name="base", round_trip_total=0.014, one_way=0.007)
    ]

    for sc in cost_scenarios:
        trade_rows = []
        for _, ex in exit_df.iterrows():
            entry_net = apply_entry_cost(float(ex["entry_price"]), sc)
            exit_net = apply_exit_cost(float(ex["exit_price"]), sc)
            gross_ret = float(ex["exit_price"]) / float(ex["entry_price"]) - 1.0
            net_ret = exit_net / entry_net - 1.0
            cost_erosion_val = 1.0 - (exit_net / entry_net) / (1.0 + gross_ret) if gross_ret != 0 else sc.round_trip_total
            trade_rows.append({
                "entry_date": ex["date"],
                "exit_date": ex["exit_date"],
                "ticker": ex["ticker"],
                "holding_days": ex["holding_days"],
                "entry_price": float(ex["entry_price"]),
                "exit_price": float(ex["exit_price"]),
                "gross_return": gross_ret,
                "entry_net": entry_net,
                "exit_net": exit_net,
                "net_return": net_ret,
                "cost_scenario": sc.name,
                "exit_reason": ex["exit_reason"],
            })

        sc_trades = pd.DataFrame(trade_rows)
        if trades.empty:
            trades = sc_trades.copy()
        else:
            trades = pd.concat([trades, sc_trades], ignore_index=True)

        gross_wins = (sc_trades["gross_return"] > 0).sum()
        net_wins = (sc_trades["net_return"] > 0).sum()
        total = len(sc_trades)
        avg_gross = sc_trades["gross_return"].mean() if total > 0 else 0.0
        avg_net = sc_trades["net_return"].mean() if total > 0 else 0.0
        cum_gross = (1.0 + sc_trades["gross_return"]).prod() - 1.0 if total > 0 else 0.0
        cum_net = (1.0 + sc_trades["net_return"]).prod() - 1.0 if total > 0 else 0.0
        base_cost = sc.round_trip_total

        scenarios[sc.name] = {
            "scenario_name": sc.name,
            "total_trades": total,
            "gross_wins": int(gross_wins),
            "net_wins": int(net_wins),
            "win_rate_gross": float(gross_wins / total) if total else 0.0,
            "win_rate_net": float(net_wins / total) if total else 0.0,
            "avg_gross_return": float(avg_gross),
            "avg_net_return": float(avg_net),
            "cumulative_gross_return": float(cum_gross),
            "cumulative_net_return": float(cum_net),
            "round_trip_cost": base_cost,
        }

    return {
        "entry_log": entry_df,
        "exit_log": exit_df,
        "trades": trades,
        "scenarios": scenarios,
    }
