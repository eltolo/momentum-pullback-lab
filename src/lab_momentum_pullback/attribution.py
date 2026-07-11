from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd

from .costs import CostScenario
from .exits import compute_exits
from .portfolio import simulate_portfolio
from .signals import compute_signals


# Frozen variants for attribution analysis
VARIANTS: dict[str, dict[str, Any]] = {
    "A": {
        "label": "Momentum + RSI2 / SMA5",
        "entry": {"use_pullback": True, "use_confirmation": True},
        "exit": {"type": "close_above_sma", "sma_period": 5, "max_holding_days": 15, "min_holding_days": 0},
        "portfolio": {"min_atr_multiple": None},
    },
    "B": {
        "label": "Momentum + RSI2 / 10d fixed",
        "entry": {"use_pullback": True, "use_confirmation": True},
        "exit": {"type": "fixed_days", "max_holding_days": 10, "min_holding_days": 3},
        "portfolio": {"min_atr_multiple": None},
    },
    "C": {
        "label": "Momentum + RSI2 / trailing 2.5 ATR",
        "entry": {"use_pullback": True, "use_confirmation": True},
        "exit": {"type": "trailing_stop_atr", "trailing_stop_atr": 2.5, "atr_period": 14, "max_holding_days": 60, "min_holding_days": 3},
        "portfolio": {"min_atr_multiple": None},
    },
    "D": {
        "label": "Momentum only / monthly rebalance",
        "entry": {"use_pullback": False, "use_confirmation": False},
        "exit": {"type": "fixed_days", "max_holding_days": 21, "min_holding_days": 21},
        "portfolio": {"min_atr_multiple": None},
    },
}


def run_attribution(
    panel: pd.DataFrame,
    base_config: dict[str, Any],
    cost_scenario: CostScenario | None = None,
) -> dict[str, Any]:
    """Run all 4 attribution variants on the same panel.

    Returns dict keyed by variant id with full portfolio results.
    """
    panel = panel.copy().sort_values(["ticker", "date"])
    if cost_scenario is None:
        cost_scenario = CostScenario(name="base", round_trip_total=0.014, one_way=0.007)

    results = {}
    for vid, vcfg in VARIANTS.items():
        cfg = deepcopy(base_config)

        # Override entry config
        trend = cfg.setdefault("trend", {})
        momentum = cfg.setdefault("momentum", {})
        pullback = cfg.setdefault("pullback", {})
        confirmation = cfg.setdefault("confirmation", {})
        exit_cfg = cfg.setdefault("exit", {})

        # Apply variant entry params
        if vcfg["entry"].get("use_pullback", True):
            pullback["type"] = "RSI2"
            pullback["threshold"] = base_config.get("pullback", {}).get("threshold", 10)
        else:
            pullback["type"] = "none"
            pullback["threshold"] = 0
        if vcfg["entry"].get("use_confirmation", True):
            confirmation["type"] = base_config.get("confirmation", {}).get("type", "close_above_previous_high")
        else:
            confirmation["type"] = "none"

        # Apply variant exit params
        for k, v in vcfg["exit"].items():
            exit_cfg[k] = v

        # Apply variant portfolio params
        port_cfg = vcfg.get("portfolio", {})
        if port_cfg.get("min_atr_multiple"):
            cfg.setdefault("risk", {})["min_atr_multiple"] = port_cfg["min_atr_multiple"]

        # Run simulation
        cfg["costs"] = {"scenarios": {"base": cost_scenario.round_trip_total}}
        signals = compute_signals(panel, cfg)

        if vcfg["entry"].get("use_pullback", True):
            entries = signals[signals["entry_signal"] == 1]
        else:
            # Momentum only: rank top ticker each day
            entries = signals[signals["high_momentum"] == 1].copy()
            entries = entries.sort_values(["date", "mom_rank_pct"], ascending=[True, False])
            # Keep only top-ranked ticker per day
            entries = entries.groupby("date").head(1)

        if entries.empty:
            results[vid] = {"variant": vid, "label": vcfg["label"], "total_trades": 0,
                            "trades": pd.DataFrame(), "scenarios": {}}
            continue

        # Build entry log with max_positions from config
        risk = cfg.get("risk", {})
        max_pos = int(risk.get("max_positions", 3))
        capital = float(cfg.get("liquidity", {}).get("capital_scales_usd_mep", [10000])[0])

        entry_log = []
        for _date, day_entries in entries.groupby("date", sort=True):
            for _, row in day_entries.head(max_pos).iterrows():
                entry_log.append({
                    "date": row["date"], "ticker": row["ticker"],
                    "entry_price": row["close_usd_mep_adj"],
                    "entry_close_usd": row["close_usd_mep_adj"],
                    "momentum_126d": row.get("momentum_126d", 0.0),
                    "rsi2": row.get("rsi2", None),
                })
        entry_df = pd.DataFrame(entry_log) if entry_log else pd.DataFrame()

        if entry_df.empty:
            results[vid] = {"variant": vid, "label": vcfg["label"], "total_trades": 0,
                            "trades": pd.DataFrame(), "scenarios": {}}
            continue

        exit_df = compute_exits(entry_df, panel, cfg)

        # Build trades
        trade_rows = []
        for _, ex in exit_df.iterrows():
            entry_net = float(ex["entry_price"]) * (1.0 + cost_scenario.one_way)
            exit_net = float(ex["exit_price"]) * (1.0 - cost_scenario.one_way)
            gross = float(ex["exit_price"]) / float(ex["entry_price"]) - 1.0
            net = exit_net / entry_net - 1.0
            trade_rows.append({
                "entry_date": ex["date"], "exit_date": ex["exit_date"],
                "ticker": ex["ticker"], "holding_days": ex["holding_days"],
                "entry_price": float(ex["entry_price"]), "exit_price": float(ex["exit_price"]),
                "gross_return": gross, "net_return": net,
                "exit_reason": ex["exit_reason"],
            })
        trades = pd.DataFrame(trade_rows) if trade_rows else pd.DataFrame()

        # Summary stats
        total = len(trades)
        if total > 0:
            gross_wins = int((trades["gross_return"] > 0).sum())
            net_wins = int((trades["net_return"] > 0).sum())
            avg_gross = float(trades["gross_return"].mean())
            avg_net = float(trades["net_return"].mean())
            cum_gross = float((1.0 + trades["gross_return"]).prod() - 1.0)
            cum_net = float((1.0 + trades["net_return"]).prod() - 1.0)
        else:
            gross_wins = net_wins = 0
            avg_gross = avg_net = cum_gross = cum_net = 0.0

        results[vid] = {
            "variant": vid,
            "label": vcfg["label"],
            "total_trades": total,
            "gross_wins": gross_wins,
            "net_wins": net_wins,
            "avg_gross_return": avg_gross,
            "avg_net_return": avg_net,
            "cumulative_gross_return": cum_gross,
            "cumulative_net_return": cum_net,
            "exit_reasons": trades["exit_reason"].value_counts().to_dict() if total > 0 else {},
            "trades": trades,
        }

    return results
