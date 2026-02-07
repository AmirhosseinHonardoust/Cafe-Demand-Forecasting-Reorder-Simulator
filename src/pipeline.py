from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from src.io import read_csv, write_csv, write_json
from src.clean import clean_transactions, CleanConfig
from src.aggregate import make_daily_item_series, AggregateConfig
from src.forecast import run_forecasting, ForecastConfig
from src.inventory import compute_rop_policy, simulate_policy, InventoryConfig
from src.reporting import fig_item_revenue_ranking, fig_backtest_summary, fig_forecast_examples, fig_rop_vs_demand


def run(
    input_path: str,
    out_dir: str = "outputs",
    figures_dir: str = "reports/figures",
    horizon_days: int = 30,
    backtest_days: int = 28,
    lead_time_days: int = 3,
    service_level: float = 0.95,
    simulation_runs: int = 300,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    fig_dir = Path(figures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    raw = read_csv(input_path)
    txn = clean_transactions(raw, CleanConfig(drop_items=("unknown", "error")))

    daily = make_daily_item_series(txn, AggregateConfig(fill_missing_days=True))

    # Save processed copy
    proc_path = Path("data/processed/daily_item_demand.csv")
    proc_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(proc_path, index=False)

    fcfg = ForecastConfig(horizon_days=horizon_days, backtest_days=backtest_days)
    backtest, selection, forecast_next = run_forecasting(daily, fcfg)

    icfg = InventoryConfig(
        lead_time_days=lead_time_days,
        service_level=service_level,
        simulation_runs=simulation_runs,
    )
    policy = compute_rop_policy(daily, forecast_next, icfg)
    sim = simulate_policy(forecast_next, policy, icfg)

    write_csv(daily, out_dir / "daily_item_demand.csv")
    write_csv(backtest, out_dir / "backtest_scores.csv")
    write_csv(selection, out_dir / "item_model_selection.csv")
    write_csv(forecast_next, out_dir / "forecast_next_30d.csv")
    write_csv(policy, out_dir / "reorder_policy.csv")
    write_csv(sim, out_dir / "simulation_summary.csv")

    meta = {
        "horizon_days": horizon_days,
        "backtest_days": backtest_days,
        "lead_time_days": lead_time_days,
        "service_level": service_level,
        "simulation_runs": simulation_runs,
        "n_txn_rows": int(len(txn)),
        "n_days": int(pd.to_datetime(daily["date"]).nunique()),
        "n_items": int(daily["item"].nunique()),
    }
    write_json(meta, out_dir / "run_metadata.json")

    # figures
    fig_item_revenue_ranking(daily, fig_dir / "item_revenue_ranking.png")
    fig_backtest_summary(backtest, fig_dir / "backtest_summary.png")
    fig_forecast_examples(daily, forecast_next, fig_dir / "forecast_examples.png", top_n=4)
    fig_rop_vs_demand(policy, fig_dir / "rop_vs_demand.png")

    return {"out_dir": str(out_dir), "figures_dir": str(fig_dir), **meta}


def main() -> None:
    parser = argparse.ArgumentParser(description="Café demand forecasting + reorder simulation pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV (cafe sales)")
    parser.add_argument("--out", default="outputs", help="Output directory")
    parser.add_argument("--figures", default="reports/figures", help="Figures directory")
    parser.add_argument("--horizon", type=int, default=30, help="Forecast horizon (days)")
    parser.add_argument("--backtest", type=int, default=28, help="Backtest window (days)")
    parser.add_argument("--lead-time", type=int, default=3, help="Lead time (days)")
    parser.add_argument("--service-level", type=float, default=0.95, help="Service level (0-1)")
    parser.add_argument("--sim-runs", type=int, default=300, help="Simulation runs per item")
    args = parser.parse_args()

    res = run(
        input_path=args.input,
        out_dir=args.out,
        figures_dir=args.figures,
        horizon_days=args.horizon,
        backtest_days=args.backtest,
        lead_time_days=args.lead_time,
        service_level=args.service_level,
        simulation_runs=args.sim_runs,
    )

    print("\nDone! Forecasts + inventory policy created.", flush=True)
    print(f"Outputs folder: {res['out_dir']}", flush=True)
    print(f"Figures folder: {res['figures_dir']}", flush=True)
    print(f"Transactions used: {res['n_txn_rows']}", flush=True)
    print(f"Days covered: {res['n_days']}", flush=True)
    print(f"Items: {res['n_items']}\n", flush=True)


if __name__ == "__main__":
    main()
