from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .costs import apply_entry_cost, apply_exit_cost, CostScenario, load_cost_scenarios
from .exits import compute_exits
from .signals import compute_signals


def _build_equity_curve(
    entry_df: pd.DataFrame,
    exit_df: pd.DataFrame,
    panel: pd.DataFrame,
    config: dict[str, Any],
    cost_scenario: CostScenario,
) -> pd.DataFrame:
    """Build daily equity curve with proper capital accounting.

    Returns DataFrame with columns: date, nav, cash, exposure, positions, returns, dd.
    """
    initial_capital = float(config.get("liquidity", {}).get("capital_scales_usd_mep", [10000])[0])
    max_positions = int(config.get("risk", {}).get("max_positions", 3))
    position_size = initial_capital / max_positions

    dates = sorted(panel["date"].unique())
    tickers = panel["ticker"].unique()

    # Build price lookup per ticker: date -> close_usd_mep_adj
    price_lookup = {}
    for t in tickers:
        t_data = panel[panel["ticker"] == t][["date", "close_usd_mep_adj"]].copy()
        price_lookup[t] = dict(zip(t_data["date"], t_data["close_usd_mep_adj"]))

    # Create entry/exit lookup
    entries = {}
    for _, r in entry_df.iterrows():
        entries[(r["ticker"], r["date"])] = float(r["entry_price"])
    exits = {}
    for _, r in exit_df.iterrows():
        exits[(r["ticker"], r["exit_date"])] = {"date": r["exit_date"], "price": float(r["exit_price"])}

    nav = initial_capital
    cash = initial_capital
    positions: dict[str, dict] = {}  # ticker -> {"shares": float, "entry_price": float, "entry_date": str}

    rows = []
    for d in dates:
        day_equity = 0.0
        # Process entries for this day
        entries_today = entry_df[entry_df["date"] == d]
        for _, er in entries_today.iterrows():
            t = er["ticker"]
            if len(positions) >= max_positions:
                continue
            if t in positions:
                continue
            if cash < position_size * (1.0 + cost_scenario.one_way):
                continue
            entry_px = float(er["entry_price"])
            cost = entry_px * cost_scenario.one_way
            shares = (position_size - cost) / entry_px
            cash -= position_size
            positions[t] = {"shares": shares, "entry_price": entry_px, "entry_date": d}

        # Process exits for this day
        for t in list(positions.keys()):
            ex = exits.get((t, d))
            if ex:
                exit_px = ex["price"]
                sh = positions[t]["shares"]
                proceeds = sh * exit_px * (1.0 - cost_scenario.one_way)
                cash += proceeds
                del positions[t]

        # Mark to market
        position_value = 0.0
        for t, pos in list(positions.items()):
            px = price_lookup[t].get(d, pos["entry_price"])
            position_value += pos["shares"] * px

        nav = cash + position_value
        exposure = position_value / nav if nav > 0 else 0.0

        rows.append({
            "date": d,
            "nav": nav,
            "cash": cash,
            "exposure": exposure,
            "positions": len(positions),
        })

    eq = pd.DataFrame(rows)
    eq["return"] = eq["nav"].pct_change(fill_method=None).fillna(0.0)
    rolling_max = eq["nav"].cummax()
    eq["drawdown"] = (eq["nav"] - rolling_max) / rolling_max
    eq["drawdown"] = eq["drawdown"].fillna(0.0)
    return eq


def _compute_metrics(eq: pd.DataFrame, trades_df: pd.DataFrame, initial_capital: float, cost_scenario: CostScenario) -> dict[str, Any]:
    """Compute portfolio metrics from equity curve."""
    total = len(trades_df)
    if total == 0 or eq.empty:
        return {"total_trades": 0}

    final_nav = float(eq["nav"].iloc[-1])
    days = len(eq)
    years = days / 252.0
    cagr = (final_nav / initial_capital) ** (1.0 / years) - 1.0 if years > 0 else 0.0
    max_dd = float(eq["drawdown"].min())
    avg_exp = float(eq["exposure"].mean())
    max_exp = float(eq["exposure"].max())
    vol = float(eq["return"].std() * math.sqrt(252)) if len(eq) > 1 else 0.0
    underwater_days = int((eq["drawdown"] < 0).sum())

    gross_ret = float(trades_df["gross_return"].sum())
    net_ret = float(trades_df["net_return"].sum())
    gross_wins = int((trades_df["gross_return"] > 0).sum())
    net_wins = int((trades_df["net_return"] > 0).sum())
    avg_gross = float(trades_df["gross_return"].mean()) if total > 0 else 0.0
    avg_net = float(trades_df["net_return"].mean()) if total > 0 else 0.0
    cum_gross = float((1.0 + trades_df["gross_return"]).prod() - 1.0) if total > 0 else 0.0
    cum_net = float((1.0 + trades_df["net_return"]).prod() - 1.0) if total > 0 else 0.0
    profit_factor = float(abs(trades_df.loc[trades_df["net_return"] > 0, "net_return"].sum() /
                               trades_df.loc[trades_df["net_return"] < 0, "net_return"].sum())
                          ) if (trades_df["net_return"] < 0).any() and (trades_df["net_return"] > 0).any() else 0.0

    return {
        "total_trades": total,
        "gross_wins": gross_wins,
        "net_wins": net_wins,
        "win_rate_gross": float(gross_wins / total) if total else 0.0,
        "win_rate_net": float(net_wins / total) if total else 0.0,
        "avg_gross_return": avg_gross,
        "avg_net_return": avg_net,
        "cumulative_gross_return": cum_gross,
        "cumulative_net_return": cum_net,
        "round_trip_cost": cost_scenario.round_trip_total,
        "initial_capital": initial_capital,
        "final_nav": final_nav,
        "total_return_pct": float(final_nav / initial_capital - 1.0),
        "cagr": cagr,
        "max_drawdown": max_dd,
        "annualized_volatility": vol,
        "avg_exposure": avg_exp,
        "max_exposure": max_exp,
        "underwater_days": underwater_days,
        "total_cost_paid": float(initial_capital * (1.0 - (1.0 + net_ret) / (1.0 + gross_ret))) if gross_ret != 0 else 0.0,
        "profit_factor": profit_factor,
    }


def simulate_portfolio(
    panel: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Full portfolio simulation with daily equity curve.

    Returns dict with entry_log, exit_log, trades, equity_curve, and metrics per scenario.
    """
    signals = compute_signals(panel, config)
    entries = signals[signals["entry_signal"] == 1].copy()
    if entries.empty:
        return {"entry_log": pd.DataFrame(), "exit_log": pd.DataFrame(),
                "trades": pd.DataFrame(), "equity_curve": pd.DataFrame(), "scenarios": {}}

    max_positions = int(config.get("risk", {}).get("max_positions", 3))
    entries = entries.sort_values(["date", "mom_rank_pct"], ascending=[True, False])
    entry_log = []
    for _date, day_entries in entries.groupby("date", sort=True):
        for _, row in day_entries.head(max_positions).iterrows():
            entry_log.append({
                "date": row["date"], "ticker": row["ticker"],
                "entry_price": row["close_usd_mep_adj"],
                "entry_close_usd": row["close_usd_mep_adj"],
                "momentum_126d": row.get("momentum_126d", 0.0),
                "rsi2": row.get("rsi2", None),
            })
    entry_df = pd.DataFrame(entry_log)
    exit_df = compute_exits(entry_df, panel, config)

    trades = pd.DataFrame()
    scenarios = {}
    cost_scenarios = load_cost_scenarios(config.get("costs", {})) or [
        CostScenario(name="base", round_trip_total=0.014, one_way=0.007)
    ]
    equity_curves = {}

    for sc in cost_scenarios:
        trade_rows = []
        for _, ex in exit_df.iterrows():
            entry_net = apply_entry_cost(float(ex["entry_price"]), sc)
            exit_net = apply_exit_cost(float(ex["exit_price"]), sc)
            gross_ret = float(ex["exit_price"]) / float(ex["entry_price"]) - 1.0
            net_ret = exit_net / entry_net - 1.0
            trade_rows.append({
                "entry_date": ex["date"], "exit_date": ex["exit_date"],
                "ticker": ex["ticker"], "holding_days": ex["holding_days"],
                "entry_price": float(ex["entry_price"]), "exit_price": float(ex["exit_price"]),
                "gross_return": gross_ret, "net_return": net_ret,
                "cost_scenario": sc.name, "exit_reason": ex["exit_reason"],
            })
        sc_trades = pd.DataFrame(trade_rows)

        eq = _build_equity_curve(entry_df, exit_df, panel, config, sc)
        initial_capital = float(config.get("liquidity", {}).get("capital_scales_usd_mep", [10000])[0])
        metrics = _compute_metrics(eq, sc_trades, initial_capital, sc)

        if trades.empty:
            trades = sc_trades.copy()
        else:
            trades = pd.concat([trades, sc_trades], ignore_index=True)
        equity_curves[sc.name] = eq
        scenarios[sc.name] = metrics

    return {
        "entry_log": entry_df,
        "exit_log": exit_df,
        "trades": trades,
        "equity_curves": equity_curves,
        "scenarios": scenarios,
    }
