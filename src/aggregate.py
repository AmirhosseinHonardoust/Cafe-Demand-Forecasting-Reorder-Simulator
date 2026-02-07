from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class AggregateConfig:
    fill_missing_days: bool = True


def make_daily_item_series(txn: pd.DataFrame, cfg: AggregateConfig = AggregateConfig()) -> pd.DataFrame:
    """
    Continuous daily time series per item (zero-filled missing days).
    Columns: date, item, demand_qty, revenue, txn_count
    """
    daily = txn.groupby(["date", "item"], observed=False).agg(
        demand_qty=("quantity", "sum"),
        revenue=("total_spent", "sum"),
        txn_count=("txn_id", "nunique"),
    ).reset_index()

    daily["date"] = pd.to_datetime(daily["date"])

    if not cfg.fill_missing_days:
        return daily.sort_values(["item", "date"])

    all_dates = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    items = sorted(daily["item"].unique().tolist())

    idx = pd.MultiIndex.from_product([all_dates, items], names=["date", "item"])
    full = daily.set_index(["date", "item"]).reindex(idx).reset_index()

    full["demand_qty"] = full["demand_qty"].fillna(0.0)
    full["revenue"] = full["revenue"].fillna(0.0)
    full["txn_count"] = full["txn_count"].fillna(0).astype(int)

    return full.sort_values(["item", "date"])
