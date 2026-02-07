from __future__ import annotations

from dataclasses import dataclass
from statistics import NormalDist
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class InventoryConfig:
    lead_time_days: int = 3
    review_period_days: int = 1
    service_level: float = 0.95
    simulation_runs: int = 300
    random_seed: int = 42
    demand_sigma_floor: float = 0.25


def compute_rop_policy(daily: pd.DataFrame, forecast_next: pd.DataFrame, cfg: InventoryConfig) -> pd.DataFrame:
    items = sorted(daily["item"].unique().tolist())
    z = float(NormalDist().inv_cdf(cfg.service_level))
    rows = []

    for item in items:
        f = forecast_next[forecast_next["item"] == item]["forecast_qty"]
        if len(f) >= 7:
            mu = float(f.mean())
            sigma = float(f.std(ddof=0))
        else:
            s = daily[daily["item"] == item]["demand_qty"]
            mu = float(s.tail(30).mean()) if len(s) else 0.0
            sigma = float(s.tail(30).std(ddof=0)) if len(s) else 0.0

        sigma = max(sigma, cfg.demand_sigma_floor)

        L = max(1, int(cfg.lead_time_days))
        R = max(1, int(cfg.review_period_days))

        safety_stock = z * sigma * np.sqrt(L)
        rop = mu * L + safety_stock
        order_up_to = mu * (L + R) + safety_stock

        rows.append({
            "item": item,
            "mu_daily_demand": mu,
            "sigma_daily_demand": sigma,
            "service_level": cfg.service_level,
            "z": z,
            "lead_time_days": L,
            "review_period_days": R,
            "safety_stock_units": float(safety_stock),
            "reorder_point_units": float(rop),
            "order_up_to_units": float(order_up_to),
        })

    return pd.DataFrame(rows).sort_values("reorder_point_units", ascending=False)


def simulate_policy(forecast_next: pd.DataFrame, policy: pd.DataFrame, cfg: InventoryConfig, initial_inventory_units: float = 0.0) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.random_seed)
    items = sorted(policy["item"].unique().tolist())
    horizon_dates = sorted(pd.to_datetime(forecast_next["date"]).unique().tolist())
    horizon = len(horizon_dates)

    summaries = []

    for item in items:
        pol = policy[policy["item"] == item].iloc[0]
        mu = float(pol["mu_daily_demand"])
        sigma = float(pol["sigma_daily_demand"])
        L = int(pol["lead_time_days"])
        rop = float(pol["reorder_point_units"])
        S = float(pol["order_up_to_units"])

        stockout_rates = []
        avg_onhand = []
        unmet_list = []

        for _ in range(int(cfg.simulation_runs)):
            inv = float(initial_inventory_units if initial_inventory_units > 0 else S)
            pipeline = []  # list of (arrival_day, qty)

            unmet = 0.0
            onhand_sum = 0.0
            stockout_days = 0

            for t in range(horizon):
                if pipeline:
                    arriving = [q for (day, q) in pipeline if day == t]
                    if arriving:
                        inv += sum(arriving)
                    pipeline = [(day, q) for (day, q) in pipeline if day != t]

                demand = float(rng.normal(mu, sigma))
                if demand < 0:
                    demand = 0.0

                if inv >= demand:
                    inv -= demand
                else:
                    unmet += (demand - inv)
                    inv = 0.0
                    stockout_days += 1

                onhand_sum += inv

                if inv <= rop:
                    order_qty = max(0.0, S - inv)
                    if order_qty > 0:
                        pipeline.append((t + L, order_qty))

            stockout_rates.append(stockout_days / max(1, horizon))
            avg_onhand.append(onhand_sum / max(1, horizon))
            unmet_list.append(unmet)

        summaries.append({
            "item": item,
            "horizon_days": horizon,
            "simulation_runs": int(cfg.simulation_runs),
            "avg_stockout_day_rate": float(np.mean(stockout_rates) * 100.0),
            "avg_onhand_units": float(np.mean(avg_onhand)),
            "avg_unmet_demand_units": float(np.mean(unmet_list)),
        })

    return pd.DataFrame(summaries).sort_values("avg_stockout_day_rate", ascending=False)
