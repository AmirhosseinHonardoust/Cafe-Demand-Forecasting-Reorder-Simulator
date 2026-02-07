from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastConfig:
    horizon_days: int = 30
    backtest_days: int = 28
    ma_window: int = 7
    ewma_alpha: float = 0.3
    seasonal_period: int = 7  # weekly


def _seasonal_naive(train: pd.Series, horizon: int, period: int = 7) -> np.ndarray:
    if len(train) < period:
        return np.repeat(train.iloc[-1] if len(train) else 0.0, horizon)
    last = train.iloc[-period:].to_numpy()
    reps = int(np.ceil(horizon / period))
    return np.tile(last, reps)[:horizon]


def _moving_average(train: pd.Series, horizon: int, window: int = 7) -> np.ndarray:
    w = min(window, max(1, len(train)))
    level = float(train.iloc[-w:].mean()) if len(train) else 0.0
    return np.repeat(level, horizon)


def _ewma_level(train: pd.Series, alpha: float = 0.3) -> float:
    if len(train) == 0:
        return 0.0
    level = float(train.iloc[0])
    for x in train.iloc[1:]:
        level = alpha * float(x) + (1 - alpha) * level
    return level


def _ewma_forecast(train: pd.Series, horizon: int, alpha: float = 0.3) -> np.ndarray:
    level = _ewma_level(train, alpha)
    return np.repeat(level, horizon)


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mask = y_true > 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0) if mask.any() else float("nan")
    return {"mae": mae, "rmse": rmse, "mape": mape}


def backtest_item(series: pd.Series, cfg: ForecastConfig) -> pd.DataFrame:
    n = len(series)
    if n <= 2:
        return pd.DataFrame([{"model": "moving_average_7d", "mae": float("nan"), "rmse": float("nan"), "mape": float("nan")}])

    test_n = min(cfg.backtest_days, max(1, n // 4)) if n > 10 else min(cfg.backtest_days, max(1, n - 1))
    train = series.iloc[:-test_n]
    test = series.iloc[-test_n:]

    rows = []

    pred = _seasonal_naive(train, test_n, cfg.seasonal_period)
    rows.append({"model": "seasonal_naive_weekly", **_metrics(test.to_numpy(), pred)})

    pred = _moving_average(train, test_n, cfg.ma_window)
    rows.append({"model": f"moving_average_{cfg.ma_window}d", **_metrics(test.to_numpy(), pred)})

    pred = _ewma_forecast(train, test_n, cfg.ewma_alpha)
    rows.append({"model": f"ewma_alpha_{cfg.ewma_alpha}", **_metrics(test.to_numpy(), pred)})

    return pd.DataFrame(rows).sort_values("mae")


def choose_model(scores: pd.DataFrame) -> str:
    scores2 = scores.dropna(subset=["mae"])
    if scores2.empty:
        return "moving_average_7d"
    return str(scores2.sort_values("mae").iloc[0]["model"])


def forecast_item(series: pd.Series, model_name: str, cfg: ForecastConfig) -> np.ndarray:
    h = cfg.horizon_days
    if model_name == "seasonal_naive_weekly":
        return _seasonal_naive(series, h, cfg.seasonal_period)
    if model_name.startswith("moving_average_"):
        return _moving_average(series, h, cfg.ma_window)
    if model_name.startswith("ewma_alpha_"):
        return _ewma_forecast(series, h, cfg.ewma_alpha)
    return _moving_average(series, h, cfg.ma_window)


def run_forecasting(daily: pd.DataFrame, cfg: ForecastConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    items = sorted(daily["item"].unique().tolist())

    backtest_all: List[pd.DataFrame] = []
    selection_rows = []
    forecast_frames = []

    for item in items:
        d = daily[daily["item"] == item].sort_values("date")
        series = pd.Series(d["demand_qty"].to_numpy(), index=pd.to_datetime(d["date"]))

        scores = backtest_item(series, cfg)
        scores.insert(0, "item", item)
        backtest_all.append(scores)

        best = choose_model(scores)
        selection_rows.append({"item": item, "best_model": best})

        fc = forecast_item(series, best, cfg)
        start = pd.to_datetime(d["date"].max()) + pd.Timedelta(days=1)
        dates = pd.date_range(start, periods=cfg.horizon_days, freq="D")
        forecast_frames.append(pd.DataFrame({"date": dates, "item": item, "forecast_qty": np.clip(fc, 0.0, None)}))

    backtest_scores = pd.concat(backtest_all, ignore_index=True) if backtest_all else pd.DataFrame()
    model_selection = pd.DataFrame(selection_rows)
    forecast_next = pd.concat(forecast_frames, ignore_index=True) if forecast_frames else pd.DataFrame()
    return backtest_scores, model_selection, forecast_next
