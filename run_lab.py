from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lab_momentum_pullback.adjustments import execute_data_audit
from lab_momentum_pullback.config_loader import REQUIRED_DIRS, run_check
from lab_momentum_pullback.data_loader import load_price_data
from lab_momentum_pullback.mep import load_canonical_mep
from lab_momentum_pullback.portfolio import simulate_portfolio
from lab_momentum_pullback.reporting import (
    write_attribution_report,
    write_benchmark_report,
    write_confirmation_report,
    write_exit_report,
    write_final_decision,
    write_portfolio_report,
    write_signal_report,
    write_walkforward_report,
)
from lab_momentum_pullback.attribution import run_attribution
from lab_momentum_pullback.signals import compute_benchmarks, compute_signals

def _load_panel() -> tuple:
    from lab_momentum_pullback.adjustments import execute_data_audit
    audit = execute_data_audit(load_price_data("argentina"), load_canonical_mep("argentina"))
    if not audit.ok or not audit.included_tickers:
        raise RuntimeError("data_audit must pass before downstream phases")
    panel = pd.read_csv(ROOT / audit.panel_path)
    config = load_price_data("argentina").config
    return panel, config, audit


def _run_portfolio() -> tuple:
    panel, config, audit = _load_panel()
    config["costs"] = config.get("costs", {})
    result = simulate_portfolio(panel, config)
    return panel, config, audit, result


def main() -> int:
    ps = ["data_audit", "benchmarks", "pullback_signals", "entry_confirmation",
          "exit_rules", "portfolio_results", "walkforward", "attribution", "final_decision"]
    parser = argparse.ArgumentParser(description="Momentum pullback lab entrypoint")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--phase", choices=ps, help="Run a specific lab phase")
    args = parser.parse_args()
    if not args.check and not args.phase:
        parser.print_help(); return 0

    result = run_check()
    if args.check:
        payload = {"ok": result.ok, "missing_paths": result.missing_paths, "validation_errors": result.validation_errors,
                   "required_directories": [str(p.relative_to(ROOT)) for p in REQUIRED_DIRS], "loaded_configs": sorted(result.loaded.keys())}
        print(json.dumps(payload, indent=2))
        if not args.phase: return 0 if result.ok else 1
    if not result.ok:
        print(json.dumps({"ok": False, "stage": "config_check", "validation_errors": result.validation_errors, "missing_paths": result.missing_paths}, indent=2))
        return 1

    # --- data_audit ---
    if args.phase == "data_audit":
        audit = execute_data_audit(load_price_data("argentina"), load_canonical_mep("argentina"))
        payload = {"ok": audit.ok, "stage": "data_audit", "analysis_start": audit.analysis_start, "analysis_end": audit.analysis_end,
                   "included_tickers": audit.included_tickers, "excluded_tickers": audit.excluded_tickers,
                   "critical_failures": audit.critical_failures, "warnings": audit.warnings, "report_path": audit.report_path,
                   "summary_path": audit.summary_path, "panel_path": audit.panel_path, "tradable_path": audit.tradable_path}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if audit.ok else 1

    # --- benchmarks ---
    if args.phase == "benchmarks":
        panel, config, audit = _load_panel()
        benchmarks = compute_benchmarks(panel, config)
        lc = panel.groupby("ticker").last()[["close_ars_raw","close_usd_mep_adj"]].reset_index().rename(columns={"close_ars_raw":"close_ars","close_usd_mep_adj":"close_usd_mep"})
        ps = {"start": audit.analysis_start, "end": audit.analysis_end, "tickers": sorted(panel["ticker"].unique()), "last_close": lc.to_dict(orient="records")}
        target = ROOT / "results" / "02_benchmarks.md"
        write_benchmark_report(benchmarks, target, ps)
        print(json.dumps({"ok": True, "stage": "benchmarks", "benchmark_days": len(benchmarks), "tickers": sorted(panel["ticker"].unique()),
                          "report_path": str(target), "final_cum_ret_ars": float(benchmarks.iloc[-1]["cum_ret_ars"]),
                          "final_cum_ret_usd": float(benchmarks.iloc[-1]["cum_ret_usd"])}, indent=2))
        return 0

    # --- pullback_signals ---
    if args.phase == "pullback_signals":
        panel, config, audit = _load_panel()
        signals = compute_signals(panel, config)
        target = ROOT / "results" / "03_pullback_signals.md"
        write_signal_report(signals, target)
        print(json.dumps({"ok": True, "stage": "pullback_signals", "total_rows": len(signals),
                          "total_signals": int(signals["entry_signal"].sum()), "report_path": str(target)}, indent=2))
        return 0

    # --- entry_confirmation ---
    if args.phase == "entry_confirmation":
        panel, config, audit = _load_panel()
        signals = compute_signals(panel, config)
        target = ROOT / "results" / "04_entry_confirmation.md"
        write_confirmation_report(signals, target)
        entries = signals[signals["entry_signal"] == 1]
        print(json.dumps({"ok": True, "stage": "entry_confirmation", "total_signals": int(entries["entry_signal"].sum()),
                          "entry_tickers": sorted(entries["ticker"].unique().tolist()), "report_path": str(target)}, indent=2))
        return 0

    # --- exit_rules ---
    if args.phase == "exit_rules":
        panel, config, audit, port = _run_portfolio()
        target = ROOT / "results" / "05_exit_rules.md"
        write_exit_report(port["exit_log"], target)
        print(json.dumps({"ok": True, "stage": "exit_rules", "total_trades": len(port["exit_log"]),
                          "exit_reasons": port["exit_log"]["exit_reason"].value_counts().to_dict() if not port["exit_log"].empty else {},
                          "report_path": str(target)}, indent=2))
        return 0

    # --- portfolio_results ---
    if args.phase == "portfolio_results":
        panel, config, audit, port = _run_portfolio()
        target = ROOT / "results" / "06_portfolio_results.md"
        write_portfolio_report(port["scenarios"], port["trades"], target)
        print(json.dumps({"ok": True, "stage": "portfolio_results", "scenarios": port["scenarios"],
                          "total_trades_by_scenario": {k: v["total_trades"] for k, v in port["scenarios"].items()},
                          "report_path": str(target)}, indent=2))
        return 0

    # --- walkforward ---
    if args.phase == "walkforward":
        panel, config, audit, port = _run_portfolio()
        target = ROOT / "results" / "07_walkforward.md"
        wf_results = []
        panel["date"] = pd.to_datetime(panel["date"])
        dates = sorted(panel["date"].unique())
        train_end_idx = len(dates) // 2
        for window_tag, start, end in [("first_half", dates[0], dates[train_end_idx]),
                                        ("second_half", dates[train_end_idx+1], dates[-1]),
                                        ("full", dates[0], dates[-1])]:
            sub = panel[(panel["date"] >= start) & (panel["date"] <= end)]
            if len(sub) < 500: continue
            sub_cfg = dict(config)
            sub_cfg["costs"] = config.get("costs", {})
            sub_port = simulate_portfolio(sub, sub_cfg)
            sc = sub_port.get("scenarios", {}).get("base", {})
            wf_results.append({"window": window_tag, "start": str(start.date()), "end": str(end.date()),
                               "total_trades": sc.get("total_trades", 0),
                               "avg_net_return": sc.get("avg_net_return", 0.0),
                               "win_rate_net": sc.get("win_rate_net", 0.0),
                               "cumulative_net_return": sc.get("cumulative_net_return", 0.0)})
        write_walkforward_report(wf_results, target)
        print(json.dumps({"ok": True, "stage": "walkforward", "windows": wf_results, "report_path": str(target)}, indent=2))
        return 0

    # --- attribution ---
    if args.phase == "attribution":
        panel, config, audit = _load_panel()
        config["costs"] = config.get("costs", {})
        variants = run_attribution(panel, config)
        benchmarks = compute_benchmarks(panel, config)
        target = ROOT / "results" / "09_attribution.md"
        write_attribution_report(variants, benchmarks, target)
        summary = {vid: {"label": v["label"], "total_trades": v["total_trades"],
                          "cum_net": v["cumulative_net_return"],
                          "cum_gross": v["cumulative_gross_return"]}
                   for vid, v in variants.items()}
        print(json.dumps({"ok": True, "stage": "attribution", "variants": summary,
                          "report_path": str(target)}, indent=2))
        return 0

    # --- final_decision ---
    if args.phase == "final_decision":
        panel, config, audit = _load_panel()
        config["costs"] = config.get("costs", {})
        port = simulate_portfolio(panel, config)
        benchmarks = compute_benchmarks(panel, config)
        target = ROOT / "results" / "FINAL_DECISION.md"
        write_final_decision(benchmarks, port, target)
        base = port["scenarios"].get("base", {})
        bench_cum = float(benchmarks.iloc[-1]["cum_ret_usd"]) if not benchmarks.empty else 0.0
        strat_cum = base.get("cumulative_net_return", 0.0)
        print(json.dumps({"ok": True, "stage": "final_decision", "benchmark_cum_usd": bench_cum,
                          "strategy_cum_usd": strat_cum, "scenarios": port["scenarios"],
                          "report_path": str(target)}, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
