from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def fig_item_revenue_ranking(daily: pd.DataFrame, out_path: Path) -> None:
    rev = daily.groupby("item", observed=False)["revenue"].sum().sort_values(ascending=False)
    plt.figure()
    rev.plot(kind="bar")
    plt.title("Total revenue by item")
    plt.xlabel("Item")
    plt.ylabel("Revenue (sum of Total Spent)")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=160)
    plt.close()


def fig_backtest_summary(backtest: pd.DataFrame, out_path: Path) -> None:
    if backtest.empty:
        return
    s = backtest.groupby("model", observed=False)["mae"].mean().sort_values()
    plt.figure()
    s.plot(kind="bar")
    plt.title("Backtest: average MAE by model (lower is better)")
    plt.xlabel("Model")
    plt.ylabel("Average MAE")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=160)
    plt.close()


def fig_forecast_examples(daily: pd.DataFrame, forecast_next: pd.DataFrame, out_path: Path, top_n: int = 4) -> None:
    rev = daily.groupby("item", observed=False)["revenue"].sum().sort_values(ascending=False)
    items = rev.head(top_n).index.tolist()

    plt.figure(figsize=(10, 6))
    for item in items:
        hist = daily[daily["item"] == item].sort_values("date")
        fc = forecast_next[forecast_next["item"] == item].sort_values("date")
        plt.plot(hist["date"], hist["demand_qty"], label=f"{item} (history)")
        plt.plot(fc["date"], fc["forecast_qty"], linestyle="--", label=f"{item} (forecast)")

    plt.title("Forecast examples (top revenue items)")
    plt.xlabel("Date")
    plt.ylabel("Daily demand (quantity)")
    plt.xticks(rotation=25)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=160)
    plt.close()


def fig_rop_vs_demand(policy: pd.DataFrame, out_path: Path) -> None:
    p = policy.sort_values("mu_daily_demand", ascending=False).head(15)
    plt.figure(figsize=(10, 5))
    plt.scatter(p["mu_daily_demand"], p["reorder_point_units"], s=45, alpha=0.8)
    for _, r in p.iterrows():
        plt.text(r["mu_daily_demand"], r["reorder_point_units"], str(r["item"]), fontsize=8)
    plt.title("Reorder point (ROP) vs mean daily demand (top items)")
    plt.xlabel("Mean daily demand (units)")
    plt.ylabel("Reorder point (units)")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=160)
    plt.close()
