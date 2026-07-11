from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np
import pandas as pd

from .costs import CostScenario
from .exits import compute_exits
from .indicators import atr
from .signals import compute_signals


# Frozen variants for attribution analysis
VARIANTS: dict[str, dict[str, Any]] = {
    "A": {
        "label": "Momentum + RSI2 / SMA5",
        "entry": {"use_pullback": True, "use_confirmation": True},
        "exit": {"type": "close_above_sma", "sma_period": 5, "max_holding_days": 15, "min_holding_days": 0},
        "portfolio": {},
    },
    "B": {
        "label": "Momentum + RSI2 / 10d fixed",
        "entry": {"use_pullback": True, "use_confirmation": True},
        "exit": {"type": "fixed_days", "max_holding_days": 10, "min_holding_days": 3},
        "portfolio": {},
    },
    "C": {
        "label": "Momentum + RSI2 / trailing 2.5 ATR",
        "entry": {"use_pullback": True, "use_confirmation": True},
        "exit": {"type": "trailing_stop_atr", "trailing_stop_atr": 2.5, "atr_period": 14, "max_holding_days": 60, "min_holding_days": 3},
        "portfolio": {},
    },
    "D": {
        "label": "Momentum only / monthly rebalance",
        "entry": {"use_pullback": False, "use_confirmation": False},
        "exit": {"type": "fixed_days", "max_holding_days": 21, "min_holding_days": 21},
        "portfolio": {},
    },
    "E": {
        "label": "Momentum + RSI2 + ATR filter / trailing 2.5 ATR",
        "entry": {"use_pullback": True, "use_confirmation": True, "min_atr_multiple": 2.5},
        "exit": {"type": "trailing_stop_atr", "trailing_stop_atr": 2.5, "atr_period": 14, "max_holding_days": 20, "min_holding_days": 3},
        "portfolio": {},
    },
}


def _compute_atr_pct(panel: pd.DataFrame) -> pd.Series:
    """Return ATR(14) as fraction of close (series aligned to panel index)."""
    tickers = panel["ticker"].unique()
    atr_pct = pd.Series(np.nan, index=panel.index)
    for t in tickers:
        mask = panel["ticker"] == t
        sub = panel.loc[mask].sort_values("date")
        raw_atr = atr(sub["high_ars_raw"], sub["low_ars_raw"], sub["close_ars_raw"], period=14)
        price = sub["close_ars_raw"].replace(0, np.nan)
        atr_pct.loc[mask] = (raw_atr / price).values
    return atr_pct


def run_attribution(
    panel: pd.DataFrame,
    base_config: dict[str, Any],
    cost_scenario: CostScenario | None = None,
) -> dict[str, Any]:
    """Run all attribution variants on the same panel.

    Returns dict keyed by variant id with portfolio results.
    """
    panel = panel.copy().sort_values(["ticker", "date"])
    if cost_scenario is None:
        cost_scenario = CostScenario(name="base", round_trip_total=0.014, one_way=0.007)

    # Precompute ATR% for all variants that need it
    panel["atr_pct"] = _compute_atr_pct(panel)

    results = {}
    for vid, vcfg in VARIANTS.items():
        cfg = deepcopy(base_config)
        pullback = cfg.setdefault("pullback", {})
        confirmation = cfg.setdefault("confirmation", {})
        exit_cfg = cfg.setdefault("exit", {})

        # Entry config
        if vcfg["entry"].get("use_pullback", True):
            pullback["type"] = "RSI2"
            pullback["threshold"] = base_config.get("pullback", {}).get("threshold", 10)
        else:
            pullback.update({"type": "none", "threshold": 0})
        if vcfg["entry"].get("use_confirmation", True):
            confirmation["type"] = base_config.get("confirmation", {}).get("type", "close_above_previous_high")
        else:
            confirmation["type"] = "none"

        # Exit config
        for k, v in vcfg["exit"].items():
            exit_cfg[k] = v

        # Run signal engine
        cfg["costs"] = {"scenarios": {"base": cost_scenario.round_trip_total}}
        signals = compute_signals(panel, cfg)

        # Build candidate entries
        if vcfg["entry"].get("use_pullback", True):
            candidates = signals[signals["entry_signal"] == 1].copy()
        else:
            candidates = signals[signals["high_momentum"] == 1].copy()
            candidates = candidates.sort_values(["date", "mom_rank_pct"], ascending=[True, False])
            candidates = candidates.groupby("date").head(1)

        if candidates.empty:
            results[vid] = {"variant": vid, "label": vcfg["label"], "total_trades": 0,
                            "trades": pd.DataFrame(), "scenarios": {}}
            continue

        # Apply min_atr_multiple filter
        min_atr_mult = vcfg["entry"].get("min_atr_multiple")
        if min_atr_mult:
            min_move = min_atr_mult * cost_scenario.round_trip_total
            candidates["pass_atr"] = candidates["atr_pct"] >= min_move
            candidates = candidates[candidates["pass_atr"] == True]

        # Build entry log (max_positions per day, ranked by momentum)
        max_pos = int(cfg.get("risk", {}).get("max_positions", 3))
        entry_log = []
        for _date, day_entries in candidates.groupby("date", sort=True):
            day_entries = day_entries.sort_values("mom_rank_pct", ascending=False)
            for _, row in day_entries.head(max_pos).iterrows():
                entry_log.append({
                    "date": row["date"], "ticker": row["ticker"],
                    "entry_price": float(row["close_usd_mep_adj"]),
                    "entry_close_usd": float(row["close_usd_mep_adj"]),
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
            "variant": vid, "label": vcfg["label"],
            "total_trades": total, "gross_wins": gross_wins, "net_wins": net_wins,
            "avg_gross_return": avg_gross, "avg_net_return": avg_net,
            "cumulative_gross_return": cum_gross, "cumulative_net_return": cum_net,
            "exit_reasons": trades["exit_reason"].value_counts().to_dict() if total > 0 else {},
            "trades": trades,
        }

    return results
