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
    lines = ["# 02 Benchmarks", "", "## Equal-weight buy-and-hold portfolio", "",
             f"- Benchmark window: `{panel_stats['start']}` \u2192 `{panel_stats['end']}`",
             f"- Tickers: `{', '.join(panel_stats['tickers'])}`",
             f"- Total trading days: `{len(benchmarks)}`", "",
             "### Final cumulative returns", ""]
    if not benchmarks.empty:
        last = benchmarks.iloc[-1]
        lines.append(f"- **ARS (nominal):** `{last['cum_ret_ars']:.4f}`")
        lines.append(f"- **USD MEP (real):** `{last['cum_ret_usd']:.4f}`")
        lines.append(""); lines.append("### Annualized returns")
        years = len(benchmarks) / 252
        ars_ann = last["cum_ret_ars"] ** (1 / years) - 1 if years > 0 else 0.0
        usd_ann = last["cum_ret_usd"] ** (1 / years) - 1 if years > 0 else 0.0
        lines.append(f"- **ARS (annualized):** `{ars_ann:.4f}`")
        lines.append(f"- **USD MEP (annualized):** `{usd_ann:.4f}`")
        lines.append(""); lines.append("### Per-ticker final close")
        cols = [("ticker", "Ticker"), ("close_ars", "Close ARS"), ("close_usd_mep", "Close USD MEP")]
        lines.extend(_markdown_table(panel_stats.get("last_close", []), cols))
    else:
        lines.append("_No benchmark data generated._")
    lines.append(""); lines.append("## Date range summary")
    cols = [("date","Date"),("ret_ars","Daily ret ARS"),("ret_usd","Daily ret USD"),
            ("cum_ret_ars","Cum ret ARS"),("cum_ret_usd","Cum ret USD")]
    rows = benchmarks.tail(10).to_dict(orient="records") if not benchmarks.empty else []
    lines.extend(_markdown_table(rows, cols))
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_signal_report(signals: pd.DataFrame, target_path: Path) -> None:
    s = signals[signals["entry_signal"] == 1].copy()
    lines = ["# 03 Pullback Signals", "", f"- Total rows analyzed: `{len(signals)}`",
             f"- Entry signals generated: `{len(s)}`", "", "### Signal breakdown by ticker", ""]
    if not s.empty:
        brk = s.groupby("ticker").agg(signals=("entry_signal","count")).reset_index().sort_values("signals", ascending=False)
        lines.extend(_markdown_table(brk.to_dict(orient="records"), [("ticker","Ticker"),("signals","Signals")]))
    else:
        lines.append("_No signals generated._")
    lines.extend(["", "### Latest signal events", ""])
    if len(s) > 0:
        cols = [("date","Date"),("ticker","Ticker"),("close_usd_mep_adj","Close USD"),
                ("in_uptrend","Uptrend"),("high_momentum","High Mom"),("in_pullback","Pullback"),("entry_signal","Entry")]
        lines.extend(_markdown_table(s.tail(20).to_dict(orient="records"), cols))
    else:
        lines.append("_No signals in period._")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_confirmation_report(signals: pd.DataFrame, target_path: Path) -> None:
    s = signals[signals["entry_signal"] == 1].copy()
    lines = ["# 04 Entry Confirmation", "", f"- Total entry signals (after confirmation): `{len(s)}`", "",
             "### Confirmation method", "", "- Close must cross above previous day's high after pullback",
             "- Only one entry per ticker per day", "- No position sizing (done in portfolio phase)", "",
             "### Entry signal dates by ticker", ""]
    if not s.empty:
        bt = s.groupby("ticker").agg(first_entry=("date","min"),last_entry=("date","max"),total_entries=("date","count")).reset_index().sort_values("total_entries", ascending=False)
        lines.extend(_markdown_table(bt.to_dict(orient="records"), [("ticker","Ticker"),("total_entries","Entries"),("first_entry","First"),("last_entry","Last")]))
        lines.extend(["", "### Top 30 entry dates"])
        cols = [("date","Date"),("ticker","Ticker"),("close_usd_mep_adj","Close USD"),("rsi2","RSI2"),("momentum_126d","Mom 126d")]
        lines.extend(_markdown_table(s.tail(30).to_dict(orient="records"), cols))
    else:
        lines.append("_No confirmed entries._")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_exit_report(exit_df: pd.DataFrame, target_path: Path) -> None:
    lines = ["# 05 Exit Rules", "", "### Exit conditions", "", "- **Primary:** close above SMA(5) after entry",
             "- **Max hold:** 15 calendar days (forced exit)", "", f"- Total trades: `{len(exit_df)}`", "",
             "### Exit reason breakdown", ""]
    if not exit_df.empty:
        reasons = exit_df["exit_reason"].value_counts().reset_index()
        reasons.columns = ["reason","count"]
        lines.extend(_markdown_table(reasons.to_dict(orient="records"), [("reason","Exit Reason"),("count","Trades")]))
        lines.extend(["", "### Holding days distribution", ""])
        hd = exit_df["holding_days"].describe().reset_index()
        hd.columns = ["stat","value"]
        for _, r in hd.iterrows():
            lines.append(f"- {r['stat']}: `{r['value']:.1f}`")
        lines.extend(["", "### Last 20 exits", ""])
        cols = [("date","Entry Date"),("ticker","Ticker"),("exit_date","Exit Date"),("exit_reason","Reason"),
                ("holding_days","Days"),("entry_price","Entry $"),("exit_price","Exit $")]
        lines.extend(_markdown_table(exit_df.tail(20).to_dict(orient="records"), cols))
    else:
        lines.append("_No trades closed._")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_portfolio_report(scenarios: dict[str, Any], trades: pd.DataFrame, target_path: Path) -> None:
    lines = ["# 06 Portfolio Results", "", "## Cost scenarios", ""]
    for sc_name, sc_data in sorted(scenarios.items()):
        lines.extend([f"### {sc_name} ({sc_data.get('round_trip_cost',0)*100:.1f}% rt)", "",
                      f"- Total trades: `{sc_data.get('total_trades',0)}`",
                      f"- Gross win rate: `{sc_data.get('win_rate_gross',0):.1%}`",
                      f"- Net win rate: `{sc_data.get('win_rate_net',0):.1%}`",
                      f"- Avg gross return: `{sc_data.get('avg_gross_return',0):.4f}`",
                      f"- Avg net return: `{sc_data.get('avg_net_return',0):.4f}`",
                      f"- Cumulative gross return: `{sc_data.get('cumulative_gross_return',0):.4f}`",
                      f"- Cumulative net return: `{sc_data.get('cumulative_net_return',0):.4f}`",
                      f"- **Total return (NAV):** `{sc_data.get('total_return_pct',0):.4f}`",
                      f"- **CAGR:** `{sc_data.get('cagr',0):.4f}`",
                      f"- **Max drawdown:** `{sc_data.get('max_drawdown',0):.4f}`",
                      f"- **Annualized vol:** `{sc_data.get('annualized_volatility',0):.4f}`",
                      f"- **Avg exposure:** `{sc_data.get('avg_exposure',0):.2%}`",
                      f"- **Underwater days:** `{sc_data.get('underwater_days',0)}`",
                      f"- **Profit factor:** `{sc_data.get('profit_factor',0):.2f}`",
                      ""])
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
            lines.append(f"- Trades: `{r.get('total_trades','?')}`")
            lines.append(f"- Avg net return: `{r.get('avg_net_return','?')}`")
            lines.append(f"- Win rate net: `{r.get('win_rate_net','?')}`")
            lines.append(f"- Cum net return: `{r.get('cumulative_net_return','?')}`"); lines.append("")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_decision(benchmarks: pd.DataFrame, portfolio_results: dict[str, Any], target_path: Path) -> None:
    lines = ["# FINAL DECISION", "", "## Summary", ""]
    bench_cum = float(benchmarks.iloc[-1]["cum_ret_usd"]) if not benchmarks.empty else 0.0
    lines.append(f"- Benchmark (equal-weight buy & hold) USD MEP: `{bench_cum:.4f}`")
    base = portfolio_results.get("scenarios", {}).get("base", {})
    if base:
        strat_cum = base.get("cumulative_net_return", 0.0)
        strat_nav = base.get("total_return_pct", 0.0)
        cagr = base.get("cagr", 0.0)
        max_dd = base.get("max_drawdown", 0.0)
        lines.append(f"- Strategy net (base cost 1.4% rt): `{strat_cum:.4f}`")
        lines.append(f"- **NAV return:** `{strat_nav:.4f}`")
        lines.append(f"- **CAGR:** `{cagr:.4f}`")
        lines.append(f"- **Max DD:** `{max_dd:.4f}`")
        lines.append(f"- Trades: `{base.get('total_trades', 0)}`")
        lines.append(f"- Net win rate: `{base.get('win_rate_net', 0.0):.1%}`"); lines.append("")
        if strat_nav > bench_cum and base.get("win_rate_net", 0) > 0.4:
            decision = "APPROVED_FOR_PAPER"
        elif strat_cum > 0:
            decision = "REQUIRES_MORE_RESEARCH"
        else:
            decision = "REJECTED"
        lines.append(f"## Decision: {decision}"); lines.append("")
        if decision == "APPROVED_FOR_PAPER":
            lines.append("Strategy clears base costs and beats buy-and-hold. Proceed to paper trading.")
        elif decision == "REQUIRES_MORE_RESEARCH":
            lines.append("Strategy is positive net but does not clearly beat benchmark. Refine parameters or wait for more data before paper trading.")
        else:
            lines.append("Strategy fails to generate positive net returns. Consider rejecting or reworking the approach.")
    lines.append(""); lines.append("### Cost scenario stress test")
    for sc_name, sc_data in sorted(portfolio_results.get("scenarios", {}).items()):
        cum = sc_data.get("cumulative_net_return", 0.0)
        lines.append(f"- {sc_name} ({sc_data.get('round_trip_cost', 0)*100:.1f}% rt): net cum `{cum:.4f}`")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_attribution_report(variants: dict[str, Any], benchmarks: pd.DataFrame, target_path: Path) -> None:
    lines = ["# 09 Attribution Analysis", "", "## Benchmark", ""]
    if not benchmarks.empty:
        bench_cum = float(benchmarks.iloc[-1]["cum_ret_usd"])
        lines.append(f"- Equal-weight buy & hold USD MEP: `{bench_cum:.4f}`")
    lines.append(""); lines.append("## Variant comparison (all at base cost 1.4% rt)"); lines.append("")
    cols = [("variant","Var"),("label","Entry / Exit"),("total_trades","Trades"),("gross_wins","Gross W"),
            ("avg_gross_return","Avg Gross"),("cumulative_gross_return","Cum Gross"),
            ("cumulative_net_return","Cum Net"),("net_wins","Net W")]
    rows = []
    for vid in ["A","B","C","D","E"]:
        v = variants.get(vid, {})
        rows.append({"variant":vid,"label":v.get("label",""),"total_trades":v.get("total_trades",0),
                     "gross_wins":v.get("gross_wins",0),
                     "avg_gross_return":f'{v.get("avg_gross_return",0):.4f}',
                     "cumulative_gross_return":f'{v.get("cumulative_gross_return",0):.4f}',
                     "cumulative_net_return":f'{v.get("cumulative_net_return",0):.4f}',
                     "net_wins":v.get("net_wins",0)})
    lines.extend(_markdown_table(rows, cols))
    lines.extend(["", "## What the comparison tells us", "",
                  "- **A vs D**: isolates pullback + exit contribution (A has both, D has neither)",
                  "- **A vs B**: isolates exit method (SMA5 vs fixed 10d)",
                  "- **A vs C**: compares SMA5 exit vs trailing ATR stop",
                  "- **D alone**: answers whether momentum-only with rebalancing is viable",
                  "", "## Detailed exit breakdown", ""])
    for vid in ["A","B","C","D","E"]:
        v = variants.get(vid, {}); er = v.get("exit_reasons", {})
        if er:
            lines.append(f"### {vid} — {v.get('label', '')}")
            erows = [{"reason":k,"count":v2} for k,v2 in sorted(er.items(), key=lambda x: -x[1])]
            lines.extend(_markdown_table(erows, [("reason","Exit reason"),("count","Trades")]))
            lines.append("")
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
