from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class CleanConfig:
    drop_items: tuple[str, ...] = ("unknown", "error")


def clean_transactions(df: pd.DataFrame, cfg: CleanConfig = CleanConfig()) -> pd.DataFrame:
    out = df.copy()

    required = ["Transaction ID", "Item", "Quantity", "Price Per Unit", "Total Spent", "Transaction Date"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out["item"] = out["Item"].astype(str).str.strip().str.lower()
    out["txn_id"] = out["Transaction ID"].astype(str)

    out["date"] = pd.to_datetime(out["Transaction Date"], errors="coerce")
    out["quantity"] = pd.to_numeric(out["Quantity"], errors="coerce").fillna(0.0)
    out["price_per_unit"] = pd.to_numeric(out["Price Per Unit"], errors="coerce")
    out["total_spent"] = pd.to_numeric(out["Total Spent"], errors="coerce")

    out = out.dropna(subset=["date", "item"])
    out = out[out["quantity"] >= 0]

    if cfg.drop_items:
        out = out[~out["item"].isin(cfg.drop_items)]

    return out[["txn_id", "item", "date", "quantity", "price_per_unit", "total_spent"]].sort_values(["date", "item"])
