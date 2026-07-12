from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np
import pandas as pd

from .costs import CostScenario
from .exits import compute_exits
from .indicators import atr
from .portfolio import simulate_portfolio
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
    """Return ATR(14) as fraction of close."""
    tickers = panel["ticker"].unique()
    atr_pct = pd.Series(np.nan, index=panel.index)
    for t in tickers:
        mask = panel["ticker"] == t
        sub = panel.loc[mask].sort_values("date")
        raw_atr = atr(sub["high_ars_raw"], sub["low_ars_raw"], sub["close_ars_raw"], period=14)
        price = sub["close_ars_raw"].replace(0, np.nan)
        atr_pct.loc[mask] = (raw_atr / price).values
    return atr_pct


def _run_variant_core(
    panel: pd.DataFrame, base_config: dict[str, Any],
    vcfg: dict[str, Any], cost_scenario: CostScenario,
) -> dict[str, Any]:
    """Run one variant and return trade-level results (compat with old code)."""
    cfg = deepcopy(base_config)
    pullback = cfg.setdefault("pullback", {})
    confirmation = cfg.setdefault("confirmation", {})
    exit_cfg = cfg.setdefault("exit", {})
    # Entry config
    if vcfg["entry"].get("use_pullback", True):
        pullback.update({"type": "RSI2", "threshold": base_config.get("pullback", {}).get("threshold", 10)})
    else:
        pullback.update({"type": "none", "threshold": 0})
    if vcfg["entry"].get("use_confirmation", True):
        confirmation["type"] = base_config.get("confirmation", {}).get("type", "close_above_previous_high")
    else:
        confirmation["type"] = "none"
    for k, v in vcfg["exit"].items():
        exit_cfg[k] = v
    cfg["costs"] = {"scenarios": {"base": cost_scenario.round_trip_total}}
    return cfg, pullback, confirmation, exit_cfg


def _result_for_variant(
    panel: pd.DataFrame, cfg: dict[str, Any], vcfg: dict[str, Any],
    cost_scenario: CostScenario, vid: str, label: str,
) -> dict[str, Any]:
    """Run the full simulation for a variant and return metrics dict."""
    signals = compute_signals(panel, cfg)
    if vcfg["entry"].get("use_pullback", True):
        candidates = signals[signals["entry_signal"] == 1].copy()
    else:
        candidates = signals[signals["high_momentum"] == 1].copy()
        candidates = candidates.sort_values(["date", "mom_rank_pct"], ascending=[True, False])
        candidates = candidates.groupby("date").head(1)
    if candidates.empty:
        return {"variant": vid, "label": label, "total_trades": 0}

    min_atr_mult = vcfg["entry"].get("min_atr_multiple")
    if min_atr_mult and "atr_pct" in panel.columns:
        min_move = min_atr_mult * cost_scenario.round_trip_total
        candidates["pass_atr"] = candidates["atr_pct"] >= min_move
        candidates = candidates[candidates["pass_atr"] == True]

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
        return {"variant": vid, "label": label, "total_trades": 0}

    exit_df = compute_exits(entry_df, panel, cfg)
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
        gross_wins = net_wins = 0; avg_gross = avg_net = cum_gross = cum_net = 0.0
    return {
        "variant": vid, "label": label, "total_trades": total,
        "gross_wins": gross_wins, "net_wins": net_wins,
        "avg_gross_return": avg_gross, "avg_net_return": avg_net,
        "cumulative_gross_return": cum_gross, "cumulative_net_return": cum_net,
        "exit_reasons": trades["exit_reason"].value_counts().to_dict() if total > 0 else {},
        "trades": trades,
    }


def run_attribution(panel: pd.DataFrame, base_config: dict[str, Any], cost_scenario: CostScenario | None = None) -> dict[str, Any]:
    """Run all 5 attribution variants."""
    panel = panel.copy().sort_values(["ticker", "date"])
    if cost_scenario is None:
        cost_scenario = CostScenario(name="base", round_trip_total=0.014, one_way=0.007)
    panel["atr_pct"] = _compute_atr_pct(panel)
    results = {}
    for vid, vcfg in VARIANTS.items():
        cfg, _, _, _ = _run_variant_core(panel, base_config, vcfg, cost_scenario)
        results[vid] = _result_for_variant(panel, cfg, vcfg, cost_scenario, vid, vcfg["label"])
    return results


def run_incremental(panel: pd.DataFrame, base_config: dict[str, Any], cost_scenario: CostScenario | None = None) -> list[dict[str, Any]]:
    """Incremental attribution M0-M4: each step adds exactly one component.

    M0 = Trend + basic entry + trailing ATR
    M1 = M0 + momentum percentile
    M2 = M1 + RSI2 pullback
    M3 = M2 + close-above-previous-high confirmation
    M4 = M3 + ATR filter
    """
    panel = panel.copy().sort_values(["ticker", "date"])
    if cost_scenario is None:
        cost_scenario = CostScenario(name="base", round_trip_total=0.014, one_way=0.007)
    panel["atr_pct"] = _compute_atr_pct(panel)

    models = [
        {"id": "M0", "label": "Trend + basic entry + trailing ATR",
         "use_pb": False, "use_conf": False, "use_mom": False, "atr_mult": None},
        {"id": "M1", "label": "M0 + momentum percentile",
         "use_pb": False, "use_conf": False, "use_mom": True, "atr_mult": None},
        {"id": "M2", "label": "M1 + RSI2 pullback",
         "use_pb": True, "use_conf": False, "use_mom": True, "atr_mult": None},
        {"id": "M3", "label": "M2 + close-above-prev-high confirmation",
         "use_pb": True, "use_conf": True, "use_mom": True, "atr_mult": None},
        {"id": "M4", "label": "M3 + ATR filter 2.5x",
         "use_pb": True, "use_conf": True, "use_mom": True, "atr_mult": 2.5},
    ]

    results = []
    for m in models:
        vcfg = {
            "entry": {"use_pullback": m["use_pb"], "use_confirmation": m["use_conf"], "min_atr_multiple": m["atr_mult"]},
            "exit": {"type": "trailing_stop_atr", "trailing_stop_atr": 2.5, "atr_period": 14, "max_holding_days": 60, "min_holding_days": 3},
            "portfolio": {},
        }
        if not m["use_mom"]:
            # Override signals: skip momentum filter
            cfg, _, _, _ = _run_variant_core(panel, base_config, vcfg, cost_scenario)
            cfg["momentum"]["min_percentile"] = 0.0  # include all
        else:
            cfg, _, _, _ = _run_variant_core(panel, base_config, vcfg, cost_scenario)

        res = _result_for_variant(panel, cfg, vcfg, cost_scenario, m["id"], m["label"])
        res["model_id"] = m["id"]
        res["model_label"] = m["label"]
        results.append(res)

    # Add delta metrics between consecutive models
    prev = None
    for r in results:
        if prev:
            r["delta_trades"] = r["total_trades"] - prev["total_trades"]
            r["delta_cum_net"] = r["cumulative_net_return"] - prev["cumulative_net_return"]
            r["delta_cum_gross"] = r["cumulative_gross_return"] - prev["cumulative_gross_return"]
        else:
            r["delta_trades"] = r["total_trades"]
            r["delta_cum_net"] = r["cumulative_net_return"]
            r["delta_cum_gross"] = r["cumulative_gross_return"]
        prev = r

    return results


def run_atr_robustness(panel: pd.DataFrame, base_config: dict[str, Any], cost_scenario: CostScenario | None = None) -> list[dict[str, Any]]:
    """Test trailing ATR at multiples 2.0, 2.5, 3.0, 3.5, 4.0."""
    panel = panel.copy().sort_values(["ticker", "date"])
    if cost_scenario is None:
        cost_scenario = CostScenario(name="base", round_trip_total=0.014, one_way=0.007)
    panel["atr_pct"] = _compute_atr_pct(panel)

    results = []
    for mult in [2.0, 2.5, 3.0, 3.5, 4.0]:
        vcfg = {
            "entry": {"use_pullback": True, "use_confirmation": True, "min_atr_multiple": 2.5},
            "exit": {"type": "trailing_stop_atr", "trailing_stop_atr": mult, "atr_period": 14, "max_holding_days": 60, "min_holding_days": 3},
            "portfolio": {},
        }
        cfg, _, _, _ = _run_variant_core(panel, base_config, vcfg, cost_scenario)
        label = f"ATR {mult}x"
        res = _result_for_variant(panel, cfg, vcfg, cost_scenario, f"ATR_{mult}", label)
        res["atr_multiple"] = mult
        results.append(res)
    return results


def run_walkforward_variant(
    panel: pd.DataFrame, base_config: dict[str, Any], vcfg: dict[str, Any],
    cost_scenario: CostScenario | None = None,
) -> list[dict[str, Any]]:
    """Walk-forward for any variant config, returning windowed results."""
    panel = panel.copy().sort_values(["ticker", "date"])
    if cost_scenario is None:
        cost_scenario = CostScenario(name="base", round_trip_total=0.014, one_way=0.007)
    panel["atr_pct"] = _compute_atr_pct(panel)

    cfg, _, _, _ = _run_variant_core(panel, base_config, vcfg, cost_scenario)
    cfg["costs"] = {"scenarios": {"base": cost_scenario.round_trip_total}}

    dates = sorted(panel["date"].unique())
    mid = len(dates) // 2
    windows = [
        ("first_half_2021_2023", dates[0], dates[mid]),
        ("second_half_2023_2026", dates[mid + 1], dates[-1]),
        ("full", dates[0], dates[-1]),
    ]
    results = []
    for tag, start, end in windows:
        sub = panel[(panel["date"] >= start) & (panel["date"] <= end)]
        res = _result_for_variant(sub, cfg, vcfg, cost_scenario, tag, tag)
        results.append({
            "window": tag, "start": str(start), "end": str(end),
            "total_trades": res["total_trades"],
            "avg_net_return": res["avg_net_return"],
            "cumulative_gross_return": res["cumulative_gross_return"],
            "cumulative_net_return": res["cumulative_net_return"],
            "gross_wins": res.get("gross_wins", 0),
            "net_wins": res.get("net_wins", 0),
        })
    return results
