from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_none_"]
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, divider]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return lines


def write_benchmark_report(benchmarks: pd.DataFrame, target_path: Path, panel_stats: dict[str, Any]) -> None:
    lines = [
        "# 02 Benchmarks",
        "",
        "## Equal-weight buy-and-hold portfolio",
        "",
        f"- Benchmark window: `{panel_stats['start']}` \u2192 `{panel_stats['end']}`",
        f"- Tickers: `{', '.join(panel_stats['tickers'])}`",
        f"- Total trading days: `{len(benchmarks)}`",
        "",
        "### Final cumulative returns",
        "",
    ]
    if not benchmarks.empty:
        last = benchmarks.iloc[-1]
        lines.append(f"- **ARS (nominal):** `{last['cum_ret_ars']:.4f}`")
        lines.append(f"- **USD MEP (real):** `{last['cum_ret_usd']:.4f}`")
        lines.append("")
        lines.append("### Annualized returns")
        years = len(benchmarks) / 252
        ars_ann = last["cum_ret_ars"] ** (1 / years) - 1 if years > 0 else 0.0
        usd_ann = last["cum_ret_usd"] ** (1 / years) - 1 if years > 0 else 0.0
        lines.append(f"- **ARS (annualized):** `{ars_ann:.4f}`")
        lines.append(f"- **USD MEP (annualized):** `{usd_ann:.4f}`")
        lines.append("")
        lines.append("### Per-ticker final close")
        ticker_data = panel_stats.get("last_close", [])
        cols = [("ticker", "Ticker"), ("close_ars", "Close ARS"), ("close_usd_mep", "Close USD MEP")]
        lines.extend(_markdown_table(ticker_data, cols))
    else:
        lines.append("_No benchmark data generated._")
    lines.append("")
    lines.append("## Date range summary")
    cols = [("date", "Date"), ("ret_ars", "Daily ret ARS"), ("ret_usd", "Daily ret USD"),
            ("cum_ret_ars", "Cum ret ARS"), ("cum_ret_usd", "Cum ret USD")]
    rows = benchmarks.tail(10).to_dict(orient="records") if not benchmarks.empty else []
    lines.extend(_markdown_table(rows, cols))
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_signal_report(signals: pd.DataFrame, target_path: Path) -> None:
    signals_in = signals[signals["entry_signal"] == 1].copy()
    lines = [
        "# 03 Pullback Signals",
        "",
        f"- Total rows analyzed: `{len(signals)}`",
        f"- Entry signals generated: `{len(signals_in)}`",
        "",
        "### Signal breakdown by ticker",
        "",
    ]
    if not signals_in.empty:
        breakdown = signals_in.groupby("ticker").agg(signals=("entry_signal", "count")).reset_index().sort_values("signals", ascending=False)
        lines.extend(_markdown_table(breakdown.to_dict(orient="records"), [("ticker", "Ticker"), ("signals", "Signals")]))
    else:
        lines.append("_No signals generated._")
    lines.extend(["", "### Latest signal events", ""])
    if len(signals_in) > 0:
        latest = signals_in.tail(20).to_dict(orient="records")
        cols = [("date", "Date"), ("ticker", "Ticker"), ("close_usd_mep_adj", "Close USD"),
                ("in_uptrend", "Uptrend"), ("high_momentum", "High Mom"), ("in_pullback", "Pullback"), ("entry_signal", "Entry")]
        lines.extend(_markdown_table(latest, cols))
    else:
        lines.append("_No signals in period._")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_confirmation_report(signals: pd.DataFrame, target_path: Path) -> None:
    entries = signals[signals["entry_signal"] == 1].copy()
    lines = [
        "# 04 Entry Confirmation",
        "",
        f"- Total entry signals (after confirmation): `{len(entries)}`",
        "",
        "### Confirmation method",
        "",
        "- Close must cross above previous day's high after pullback",
        "- Only one entry per ticker per day",
        "- No position sizing (done in portfolio phase)",
        "",
        "### Entry signal dates by ticker",
        "",
    ]
    if not entries.empty:
        by_ticker = entries.groupby("ticker").agg(first_entry=("date","min"), last_entry=("date","max"), total_entries=("date","count")).reset_index().sort_values("total_entries", ascending=False)
        lines.extend(_markdown_table(by_ticker.to_dict(orient="records"), [("ticker","Ticker"),("total_entries","Entries"),("first_entry","First"),("last_entry","Last")]))
        lines.extend(["", "### Top 30 entry dates"])
        top = entries.tail(30).to_dict(orient="records")
        cols = [("date","Date"),("ticker","Ticker"),("close_usd_mep_adj","Close USD"),("rsi2","RSI2"),("momentum_126d","Mom 126d")]
        lines.extend(_markdown_table(top, cols))
    else:
        lines.append("_No confirmed entries._")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_exit_report(exit_df: pd.DataFrame, target_path: Path) -> None:
    lines = [
        "# 05 Exit Rules",
        "",
        "### Exit conditions",
        "",
        "- **Primary:** close above SMA(5) after entry",
        "- **Max hold:** 15 calendar days (forced exit)",
        "",
        f"- Total trades: `{len(exit_df)}`",
        "",
        "### Exit reason breakdown",
        "",
    ]
    if not exit_df.empty:
        reasons = exit_df["exit_reason"].value_counts().reset_index()
        reasons.columns = ["reason", "count"]
        lines.extend(_markdown_table(reasons.to_dict(orient="records"), [("reason","Exit Reason"),("count","Trades")]))
        lines.extend(["", "### Holding days distribution", ""])
        hd = exit_df["holding_days"].describe().reset_index()
        hd.columns = ["stat", "value"]
        for _, r in hd.iterrows():
            lines.append(f"- {r['stat']}: `{r['value']:.1f}`")
        lines.extend(["", "### Last 20 exits", ""])
        tail = exit_df.tail(20).to_dict(orient="records")
        cols = [("date","Entry Date"),("ticker","Ticker"),("exit_date","Exit Date"),
                ("exit_reason","Reason"),("holding_days","Days"),("entry_price","Entry $"),("exit_price","Exit $")]
        lines.extend(_markdown_table(tail, cols))
    else:
        lines.append("_No trades closed._")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_portfolio_report(
    scenarios: dict[str, Any],
    trades: pd.DataFrame,
    target_path: Path,
) -> None:
    lines = [
        "# 06 Portfolio Results",
        "",
        "## Cost scenarios",
        "",
    ]
    for sc_name, sc_data in sorted(scenarios.items()):
        lines.extend([
            f"### {sc_data['scenario_name']} ({sc_data['round_trip_cost']*100:.1f}% rt)",
            "",
            f"- Total trades: `{sc_data['total_trades']}`",
            f"- Gross win rate: `{sc_data['win_rate_gross']:.1%}`",
            f"- Net win rate: `{sc_data['win_rate_net']:.1%}`",
            f"- Avg gross return: `{sc_data['avg_gross_return']:.4f}`",
            f"- Avg net return: `{sc_data['avg_net_return']:.4f}`",
            f"- Cumulative gross return: `{sc_data['cumulative_gross_return']:.4f}`",
            f"- Cumulative net return: `{sc_data['cumulative_net_return']:.4f}`",
            "",
        ])
    lines.append("## All trades (base scenario)")
    lines.append("")
    base = trades[trades["cost_scenario"] == "base"].copy() if not trades.empty else pd.DataFrame()
    if not base.empty:
        cols = [("entry_date","Entry"),("ticker","Ticker"),("exit_date","Exit"),("exit_reason","Reason"),
                ("holding_days","Days"),("gross_return","Gross"),("net_return","Net")]
        lines.extend(_markdown_table(base.to_dict(orient="records"), cols))
    else:
        lines.append("_No trades recorded._")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_walkforward_report(results: list[dict[str, Any]], target_path: Path) -> None:
    lines = ["# 07 Walk-Forward Evaluation", ""]
    if not results:
        lines.append("_No walk-forward results._")
    else:
        for r in results:
            lines.append(f"### Window: {r['window']}")
            lines.append(f"- Trades: `{r.get('total_trades', '?')}`")
            lines.append(f"- Avg net return: `{r.get('avg_net_return', '?')}`")
            lines.append(f"- Net win rate: `{r.get('win_rate_net', '?')}`")
            lines.append("")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_decision(
    benchmarks: pd.DataFrame,
    portfolio_results: dict[str, Any],
    target_path: Path,
) -> None:
    lines = [
        "# FINAL DECISION",
        "",
        "## Summary",
        "",
    ]
    bench_cum = float(benchmarks.iloc[-1]["cum_ret_usd"]) if not benchmarks.empty else 0.0
    lines.append(f"- Benchmark (equal-weight buy & hold) USD MEP: `{bench_cum:.4f}`")
    scenarios = portfolio_results.get("scenarios", {})
    base = scenarios.get("base", {})
    if base:
        strat_cum = base.get("cumulative_net_return", 0.0)
        lines.append(f"- Strategy net (base cost 1.4% rt): `{strat_cum:.4f}`")
        lines.append(f"- Trades: `{base.get('total_trades', 0)}`")
        lines.append(f"- Net win rate: `{base.get('win_rate_net', 0.0):.1%}`")
        lines.append("")
        # Decision logic
        if strat_cum > bench_cum and base.get("win_rate_net", 0) > 0.4:
            decision = "APPROVED_FOR_PAPER"
        elif strat_cum > 0:
            decision = "REQUIRES_MORE_RESEARCH"
        else:
            decision = "REJECTED"
        lines.append(f"## Decision: {decision}")
        lines.append("")
        if decision == "APPROVED_FOR_PAPER":
            lines.append("Strategy clears base costs and beats buy-and-hold. Proceed to paper trading.")
        elif decision == "REQUIRES_MORE_RESEARCH":
            lines.append("Strategy is positive net but does not clearly beat benchmark. Refine parameters or wait for more data before paper trading.")
        else:
            lines.append("Strategy fails to generate positive net returns. Consider rejecting or reworking the approach.")
    lines.append("")
    lines.append("### Cost scenario stress test")
    for sc_name, sc_data in sorted(scenarios.items()):
        cum = sc_data.get("cumulative_net_return", 0.0)
        lines.append(f"- {sc_name} ({sc_data.get('round_trip_cost', 0)*100:.1f}% rt): net cum `{cum:.4f}`")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
