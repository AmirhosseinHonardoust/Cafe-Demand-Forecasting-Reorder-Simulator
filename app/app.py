import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run as run_pipeline  # noqa: E402

st.set_page_config(page_title="Café Forecasting + Reorder Simulator", layout="wide")
st.title("Café Demand Forecasting + Inventory Reorder Simulator")
st.caption("Baseline forecasting + reorder points + simulation-based stockout risk.")

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "cafe_sales.csv"
OUT_DIR = PROJECT_ROOT / "outputs"
FIG_DIR = PROJECT_ROOT / "reports" / "figures"

with st.sidebar:
    st.header("Pipeline")
    uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"])
    input_path = st.text_input("Or CSV path", value=str(DEFAULT_INPUT))

    horizon = st.slider("Forecast horizon (days)", 7, 60, 30, 1)
    backtest = st.slider("Backtest window (days)", 7, 60, 28, 1)

    st.divider()
    st.header("Inventory assumptions")
    lead_time = st.slider("Lead time (days)", 1, 14, 3, 1)
    service_level = st.slider("Service level", 0.80, 0.99, 0.95, 0.01)
    sim_runs = st.slider("Simulation runs per item", 50, 1000, 300, 50)

    run_btn = st.button("Run / Refresh")

effective_input = Path(input_path)
if uploaded is not None:
    tmp = PROJECT_ROOT / "data" / "raw" / "uploaded.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(uploaded.getbuffer())
    effective_input = tmp

if run_btn:
    with st.spinner("Running pipeline..."):
        run_pipeline(
            input_path=str(effective_input),
            out_dir=str(OUT_DIR),
            figures_dir=str(FIG_DIR),
            horizon_days=int(horizon),
            backtest_days=int(backtest),
            lead_time_days=int(lead_time),
            service_level=float(service_level),
            simulation_runs=int(sim_runs),
        )
    st.success("Done! Outputs regenerated.")

daily_path = OUT_DIR / "daily_item_demand.csv"
fc_path = OUT_DIR / "forecast_next_30d.csv"
policy_path = OUT_DIR / "reorder_policy.csv"
sim_path = OUT_DIR / "simulation_summary.csv"

if not daily_path.exists():
    st.info("Run the pipeline from the sidebar to generate outputs.")
    st.stop()

daily = pd.read_csv(daily_path)
daily["date"] = pd.to_datetime(daily["date"])
items = sorted(daily["item"].unique().tolist())

forecast = pd.read_csv(fc_path) if fc_path.exists() else pd.DataFrame()
if not forecast.empty:
    forecast["date"] = pd.to_datetime(forecast["date"])

policy = pd.read_csv(policy_path) if policy_path.exists() else pd.DataFrame()
sim = pd.read_csv(sim_path) if sim_path.exists() else pd.DataFrame()

tab_overview, tab_item, tab_inventory, tab_notes = st.tabs(["Overview", "Item Explorer", "Inventory Policy", "Notes"])

with tab_overview:
    c1, c2, c3 = st.columns(3)
    c1.metric("Days covered", int(daily["date"].nunique()))
    c2.metric("Items", int(daily["item"].nunique()))
    c3.metric("Total revenue", round(float(daily["revenue"].sum()), 2))

    st.subheader("Revenue ranking by item")
    rev = daily.groupby("item")["revenue"].sum().sort_values(ascending=False).reset_index()
    st.plotly_chart(px.bar(rev, x="item", y="revenue"), width="stretch")

    bt_path = OUT_DIR / "backtest_scores.csv"
    st.subheader("Backtest summary")
    if bt_path.exists():
        bt = pd.read_csv(bt_path)
        avg = bt.groupby("model")["mae"].mean().sort_values().reset_index()
        st.plotly_chart(px.bar(avg, x="model", y="mae"), width="stretch")
    else:
        st.info("Backtest results not found. Run pipeline.")

with tab_item:
    item = st.selectbox("Select item", items)
    hist = daily[daily["item"] == item].sort_values("date")

    st.subheader("Historical daily demand")
    st.plotly_chart(px.line(hist, x="date", y="demand_qty", title=f"Daily demand — {item}"), width="stretch")

    st.subheader("History + forecast")
    if not forecast.empty:
        fc = forecast[forecast["item"] == item].sort_values("date")
        comb = pd.concat([
            hist[["date", "demand_qty"]].rename(columns={"demand_qty": "qty"}).assign(kind="history"),
            fc[["date", "forecast_qty"]].rename(columns={"forecast_qty": "qty"}).assign(kind="forecast"),
        ], ignore_index=True)
        st.plotly_chart(px.line(comb, x="date", y="qty", color="kind", title=f"{item}"), width="stretch")
    else:
        st.info("Forecast not found. Run pipeline.")

with tab_inventory:
    if policy.empty or sim.empty:
        st.info("Inventory outputs not found. Run pipeline.")
    else:
        st.subheader("Policy table (top by ROP)")
        st.dataframe(policy.head(30), width="stretch", hide_index=True)

        st.subheader("Stockout risk (simulation)")
        st.dataframe(sim.head(30), width="stretch", hide_index=True)

        st.subheader("Explain a single item policy")
        item2 = st.selectbox("Pick item", sorted(policy["item"].unique().tolist()))
        p = policy[policy["item"] == item2].iloc[0].to_dict()
        s = sim[sim["item"] == item2].iloc[0].to_dict() if (sim["item"] == item2).any() else {}

        col1, col2, col3 = st.columns(3)
        col1.metric("Mean daily demand (μ)", round(float(p["mu_daily_demand"]), 2))
        col2.metric("Std daily demand (σ)", round(float(p["sigma_daily_demand"]), 2))
        col3.metric("Service level", f'{float(p["service_level"])*100:.0f}%')

        col4, col5, col6 = st.columns(3)
        col4.metric("Safety stock", round(float(p["safety_stock_units"]), 2))
        col5.metric("Reorder point (ROP)", round(float(p["reorder_point_units"]), 2))
        col6.metric("Order-up-to (S)", round(float(p["order_up_to_units"]), 2))

        if s:
            st.caption("Simulation estimates (under assumed variability):")
            col7, col8, col9 = st.columns(3)
            col7.metric("Avg stockout day rate", f'{float(s["avg_stockout_day_rate"]):.1f}%')
            col8.metric("Avg on-hand", round(float(s["avg_onhand_units"]), 2))
            col9.metric("Avg unmet demand", round(float(s["avg_unmet_demand_units"]), 2))

with tab_notes:
    st.markdown(
        """
### Decision safety notes
- Forecasts are baseline models: explainable, fast, and often surprisingly strong.
- Inventory outputs depend on assumptions (lead time, service level, demand variability).
- Without cost data, this repo focuses on reorder rules and risk estimates, not “optimal” ordering.

### Next upgrades
- Add cost-based optimization (holding vs stockout vs ordering cost).
- Add richer time-series models after baselines.
- Add supplier constraints and item-specific lead times.
        """.strip()
    )
