<p align="center">
  <h1 align="center">Café Demand Forecasting + Inventory Reorder Simulator </h1>
    <p align="center">
<div align="center"> 

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Wrangling-yellow)
![Forecasting](https://img.shields.io/badge/Forecasting-Baselines%20%2B%20Backtesting-purple)
![Inventory](https://img.shields.io/badge/Inventory-ROP%20%2B%20Safety%20Stock-orange)
![Simulation](https://img.shields.io/badge/Simulation-Monte%20Carlo-8A2BE2)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75)
![License](https://img.shields.io/badge/License-MIT-green)

</div>
    
A portfolio-grade analytics project that turns café transactions into **(1) item-level demand forecasts** and **(2) an inventory reorder policy** (Reorder Point + Safety Stock), then validates the policy with a **Monte Carlo stockout-risk simulation**.

This repo is built around a real decision:

> **“For each item, when should I reorder (ROP), how much should I target (Order-up-to), and what stockout risk am I accepting?”**

---

## Dataset (Source + Thanks)

This project uses the Kaggle dataset:

- **Cafe Sales Dataset (Clean)** by **aramelheni**
- Dataset URL: https://www.kaggle.com/datasets/aramelheni/cafe-sales-dataset-clean

Thanks to the author and Kaggle for making the data publicly available.

---

## Table of contents

- [What this project delivers](#what-this-project-delivers)
- [Dashboard tour (with screenshots)](#dashboard-tour-with-screenshots)
- [How it works (end-to-end)](#how-it-works-end-to-end)
- [Figures explained (analysis outputs)](#figures-explained-analysis-outputs)
- [Quickstart](#quickstart)
- [CLI options](#cli-options)
- [Outputs](#outputs)
- [Project structure](#project-structure)
- [Decision safety + limitations](#decision-safety--limitations)
- [Next upgrades](#next-upgrades)

---

## What this project delivers

### 1) Clean, decision-ready daily demand per item
Raw data is transaction-level (each row = one purchase event). Inventory decisions need a **daily** signal.

This repo creates:
- **Daily demand (units)** per item
- **Daily revenue** per item
- **Zero-filled missing days** so each item becomes a continuous time series (no “holes”)

### 2) Forecasting you can explain (and defend)
Instead of jumping to complex models, we start with **strong baselines** that many real businesses use because they’re:
- simple,
- stable,
- fast,
- easy to communicate.

We backtest multiple baseline models and choose the best per item.

### 3) Inventory reorder logic from the forecast
Forecasts are translated into:
- **Safety Stock**
- **Reorder Point (ROP)**
- **Order-up-to level (S)**

So the output is not “a forecast chart”, but an actionable reorder policy.

### 4) Simulation-based risk estimate
Inventory decisions are probabilistic. Even a “good” policy can stock out if demand spikes.

We simulate demand variability and inventory updates to estimate:
- stockout-day rate (%)
- average inventory on-hand
- unmet demand (lost sales proxy)

---

## Dashboard tour (with screenshots)

### A) Overview tab (health check + prioritization)

<img width="1883" height="922" alt="Screenshot 2026-02-07 at 20-48-26 Café Forecasting Reorder Simulator" src="https://github.com/user-attachments/assets/7a17bdd3-30be-4b66-92b8-7cbd690f204d" />

**What you’re seeing**
- **Days covered / Items / Total revenue**: sanity-check the dataset size and total business footprint.
- **Revenue ranking by item**: quickly identifies which items matter most financially.
- **Backtest summary**: compares forecasting baselines on your data, not in theory.

**Why it matters**
This tab answers: *“Is the dataset valid, what’s worth focusing on, and which forecasting approach is behaving best overall?”*

---

### B) Item Explorer tab (history + forecast per item)

<img width="1894" height="925" alt="Screenshot 2026-02-07 at 20-52-30 Café Forecasting Reorder Simulator" src="https://github.com/user-attachments/assets/340e33d6-81f1-47be-aaf3-d60f1a369452" />

**What you’re seeing**
- **Historical daily demand**: raw behavior (including spikes and noisy days).
- **History + forecast**:
  - “history” line = observed demand
  - “forecast” line = next-horizon baseline forecast

**How to interpret**
- If demand is mostly stable, a moving average/EWMA baseline can be strong.
- If demand is weekly-patterned (weekday/weekend differences), seasonal naïve often wins.
- Large spikes should trigger a “data and operations” question: promotion? bulk purchase? data entry?

**Why it matters**
This tab answers: *“What does normal demand look like for this item, and what is the next-month expectation?”*

---

### C) Inventory Policy tab (ROP table + risk + item-level explanation)

<img width="1887" height="936" alt="Screenshot 2026-02-07 at 20-53-10 Café Forecasting Reorder Simulator" src="https://github.com/user-attachments/assets/77f09082-6bae-411f-ad2b-1af66a028173" />

This is the decision tab. It is intentionally practical.

#### 1) Policy table (top by ROP)
Columns you’ll see:
- **μ (mu_daily_demand)**: mean daily demand (units/day)
- **σ (sigma_daily_demand)**: demand variability
- **Service level**: target probability of no stockout during lead time
- **z**: the z-score equivalent of that service level
- **Lead time (days)**: supplier delay window
- **Safety stock**: buffer inventory for variability
- **ROP**: reorder when inventory drops below this
- **Order-up-to (S)**: target inventory level after ordering

**Interpretation rule**
- Higher μ → higher ROP (more demand to cover during lead time)
- Higher σ or higher service level → higher safety stock → higher ROP

#### 2) Stockout risk (simulation)
This table shows simulated outcomes under variability:
- **avg_stockout_day_rate**: % of days with stockout
- **avg_onhand_units**: average inventory you carry
- **avg_unmet_demand_units**: expected demand you fail to serve (lost sales proxy)

**What “good” looks like**
- Low stockout-day rate *with* a reasonable on-hand level.
- If you want lower risk, raise service level or reduce lead time (if operationally possible).

#### 3) Explain a single item policy (human-readable breakdown)
This section translates formulas into story:
- “This item sells μ/day with σ variability.”
- “With lead time L and service level SL, you need safety stock.”
- “Therefore reorder at ROP and refill to S.”

---

### D) Notes tab (decision safety + next upgrades)

<img width="1020" height="636" alt="Screenshot 2026-02-07 at 20-53-25 Café Forecasting Reorder Simulator" src="https://github.com/user-attachments/assets/e11e5ea5-0a30-4ab7-890c-65c722869369" />

This tab is the ethics/engineering discipline of analytics:
- Forecasts are **models**, not truth.
- Inventory is **assumption-sensitive** (lead time + variability + service level).
- Without cost data, we avoid claiming “optimal” ordering.

---

## How it works (end-to-end)

### Step 1 | Clean the transaction schema
We standardize columns and types:
- parse dates
- coerce quantities and totals to numeric
- normalize item labels (case/whitespace)
- drop invalid rows safely

### Step 2 | Aggregate into daily demand series
Inventory is decided daily (or at least reviewed daily/weekly).

We compute per **date × item**:
- demand_qty = sum(quantity)
- revenue = sum(total_spent)
- txn_count = number of transactions

Then we **fill missing days with 0** so every item has a continuous timeline:
- This is essential for forecasting and backtesting.
- Otherwise, “missing day” might be mistaken as “missing data” rather than “zero sales”.

### Step 3 | Forecasting baselines (fast, explainable)
We run a small, defendable model zoo per item:

1) **Seasonal naïve (weekly)**  
   “Next Monday ≈ last Monday.”

2) **Moving average (7-day)**  
   Forecast = mean of last 7 days.

3) **EWMA (exponential smoothing)**  
   Weighted mean where recent days matter more (stable and responsive).

### Step 4 | Backtesting (how we decide the best model)
Backtesting tests models on data they haven’t “seen”.

- hold out the last N days (default 28)
- fit baseline using prior days
- predict the held-out days
- compute metrics:
  - MAE (mean absolute error)
  - RMSE (root mean squared error)
  - MAPE (percentage error when actual > 0)

**Model selection rule**
- pick the model with **lowest MAE** per item (simple + robust)

### Step 5 | Inventory policy (ROP + Safety Stock)
For each item we estimate:
- μ = mean daily demand
- σ = standard deviation of daily demand

Given:
- lead time L (days)
- service level SL (e.g., 0.95)
- z = z-score for SL

We compute:
- Safety Stock ≈ z × σ × sqrt(L)
- ROP ≈ μ × L + Safety Stock

**Meaning**
- μ × L covers expected demand during lead time
- safety stock covers uncertainty during lead time

### Step 6 | Simulation (risk isn’t a single number)
Even if ROP is correct “on average”, randomness causes stockouts.

We simulate many runs:
- daily demand sampled from a distribution around μ, σ
- inventory updates daily
- if inventory ≤ ROP → order up to S
- order arrives after lead time L

Outputs:
- stockout-day probability
- unmet demand
- average inventory held

---

## Figures explained (analysis outputs)

> These are the figures generated by the pipeline and used in analysis + README.

### 1) Backtest summary (Average MAE by model)

<img width="1024" height="768" alt="backtest_summary" src="https://github.com/user-attachments/assets/12bb3af1-6419-4d54-8fb2-fe982c4ae661" />

**What it shows**
- Each bar = average MAE across items for that model.
- Lower MAE = better accuracy.

**How to read it**
- If Moving Average wins, your demand is mostly stable.
- If Seasonal Naïve wins, your demand is strongly weekly-patterned.
- If EWMA wins, demand shifts slowly and recent behavior matters most.

**Why it matters**
This chart tells you whether a “simple” method is already excellent (often true), and prevents over-engineering.

---

### 2) Forecast examples (Top revenue items)

<img width="1600" height="960" alt="forecast_examples" src="https://github.com/user-attachments/assets/437efa7e-9954-4557-a416-de66cd11ac9c" />

**What it shows**
- Multiple top items plotted together:
  - solid = historical demand
  - dashed = forecast horizon

**What to watch**
- **Spikes**: single-day events can dominate perception. Investigate whether they’re real (bulk purchase, promotion) or data artifacts.
- **Noise vs signal**: if demand is mostly low and spiky, inventory should be conservative and service-level assumptions matter more.

**Why it matters**
This is the bridge from “forecasting metrics” to “human trust”: you can see whether the forecast feels reasonable.

---

### 3) Total revenue by item (prioritization)

<img width="1024" height="768" alt="item_revenue_ranking" src="https://github.com/user-attachments/assets/8abf6555-4e52-44d1-8940-a32db24bbb5e" />

**What it shows**
- Total revenue contribution per item over the full dataset.

**How to use it**
- High-revenue items:
  - forecast and inventory policy matter more (financial impact)
  - service level may be worth increasing
- Low-revenue items:
  - may tolerate higher stockout risk if holding cost is high
  - or might be discontinued depending on business logic

**Why it matters**
This prevents “equal effort for unequal impact.”

---

### 4) ROP vs Mean Daily Demand (top items)

<img width="1600" height="800" alt="rop_vs_demand" src="https://github.com/user-attachments/assets/a15c20d1-79a4-463f-870c-ecab5377d222" />

**What it shows**
- x-axis: mean daily demand (μ)
- y-axis: reorder point (ROP)
- labels: item names

**Interpretation**
- ROP increases with μ (more demand to cover lead time).
- ROP increases with σ and service level (more safety stock).
- Two items with similar μ can have different ROP if one is more volatile.

**Why it matters**
This chart is a quick audit:
- If an item’s ROP looks “too high”, check σ or lead time assumptions.
- If ROP looks “too low”, expect stockouts in simulation.

---

## Quickstart

### 1) Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
````

### 2) Run the pipeline

```bash
python -m src.pipeline --input data/raw/cafe_sales.csv
```

### 3) Run the dashboard

```bash
streamlit run app/app.py
```

---

## CLI options

```bash
python -m src.pipeline \
  --input data/raw/cafe_sales.csv \
  --out outputs \
  --figures reports/figures \
  --horizon 30 \
  --backtest 28 \
  --lead-time 3 \
  --service-level 0.95 \
  --sim-runs 300
```

**Guidance**

* Increase `--service-level` if stockouts are expensive.
* Increase `--lead-time` to reflect slow suppliers (ROP will increase).
* Increase `--sim-runs` for more stable risk estimates.

---

## Outputs

After running the pipeline, check:

* `outputs/daily_item_demand.csv`
  Clean daily series (date × item) with demand and revenue.

* `outputs/backtest_scores.csv`
  Item-level metrics per model.

* `outputs/item_model_selection.csv`
  Best model per item (lowest MAE).

* `outputs/forecast_next_30d.csv`
  Next-horizon daily quantity forecasts.

* `outputs/reorder_policy.csv`
  Inventory policy per item (safety stock, ROP, S).

* `outputs/simulation_summary.csv`
  Stockout-day risk and unmet demand estimates.

* `reports/figures/*.png`
  Shareable charts used above.

---

## Project structure

```text
cafe-demand-forecasting-reorder-simulator/
  app/
    app.py                      # Streamlit dashboard
  data/
    raw/
      cafe_sales.csv
    processed/
      daily_item_demand.csv
  outputs/
    *.csv + run_metadata.json
  reports/
    figures/
      backtest_summary.png
      forecast_examples.png
      item_revenue_ranking.png
      rop_vs_demand.png
    figures/ui/
      dashboard_overview.png
      dashboard_item_explorer.png
      dashboard_inventory_policy.png
      dashboard_notes.png
  src/
    clean.py
    aggregate.py
    forecast.py
    inventory.py
    reporting.py
    pipeline.py
  README.md
  requirements.txt
  LICENSE
```

---

## Decision safety + limitations

* **Baselines are intentional**: they are strong, explainable, and fast.
* **Inventory math is assumption-sensitive**:

  * lead time, service level, and variability drive ROP.
* **Without cost data**, we avoid claiming “optimal” inventory:

  * true optimization needs holding cost, stockout cost, order cost.
* **Spikes matter**:

  * one promotional day can inflate σ and raise ROP.
  * consider spike handling if you know “event days”.

---

## Next upgrades

If you want to push this from “portfolio-grade” to “production-grade”:

1. **Cost-based optimization**
   Add holding vs stockout vs order cost and recommend service levels.

2. **Item-specific lead times**
   Different suppliers → different reorder behavior.

3. **Promotion/event tagging**
   Separate “normal demand” from “event demand”.

4. **Richer time-series models (after baselines)**
   Prophet / SARIMAX / LightGBM features, etc. (only if baselines are not enough)

5. **Data quality checks**

   * outlier audit
   * missing-day audit
   * duplicate transaction detection
