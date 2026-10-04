# Formula 1 Data Science & Telemetry Analytics Platform

A comprehensive Python pipeline for acquiring, cleaning, analyzing, and visualizing Formula 1 race telemetry.

This project is a dedicated Data Science and analytics platform. Its primary focus is robust telemetry processing, exploratory data analysis (EDA), statistical evaluation, feature engineering, lap-time explanatory modeling, strategy analytics, race outcome prediction, and reproducible graphical reporting.

Visualization is a **core project requirement**: the platform is visualization-first in its user-facing output. Analytical results are presented through interactive, session-specific graphical HTML reports containing KPI summaries, EDA plots, feature distributions, scatter plots, correlation matrices, model diagnostics, feature importance, tyre degradation trends, stint analysis, driver pace, compound analysis, strategy visualizations, and race outcome prediction charts.

---

## Project Architecture & Data Flow

The pipeline processes raw F1 telemetry through a strict multi-phase architecture. Each phase builds upon the outputs of the previous phase to ensure reproducibility and temporal integrity.

The data flow is structured as follows:

**FastF1**  
    ↓  
**Session Selection**  
    ↓  
**Phase 0:** Data Extraction & Clean Analytical Dataset  
    ↓  
**Session-specific Parquet datasets**  
    ↓  
**Phase 1:** EDA + Statistics  
    ↓  
**Phase 2:** Telemetry Feature Engineering  
    ↓  
**Phase 3:** Explanatory Modeling  
    ↓  
**Phase 4:** Tyre / Stint / Strategy Analysis  
    ↓  
**Phase 5:** Race Outcome Prediction & Historical Database  
    ↓  
**HTML Reports**  
    ↓  
**Localhost HTTP Server**  
    ↓  
**Automatic Browser Opening**  

---

## Multi-Session / Multi-Race Architecture

The project is **not restricted to a single hardcoded race**. The architecture supports multiple seasons, multiple events, and multiple sessions.

Users interactively select the desired Session, which generates a canonical **`session_id`** (e.g., `2026_09_British_Grand_Prix_Race`, `2023_01_Bahrain_Grand_Prix_Practice_1`).

The selected session dictates the entire pipeline:
- Session-specific data is completely isolated.
- **Phases 0–4** process only the selected session's lap and telemetry data. No cross-session data leakage occurs within these phases.
- **Phase 5** intentionally uses historical race data from prior sessions. Historical features (rolling averages, championship standings) are constructed using strictly chronological, shifted computations so that a race's own results never enter its own feature vector. Temporal validation follows an expanding-window protocol over chronologically ordered races.

---

## Outputs

The project strictly separates analytical datasets from generated reports.

**`analytics_data/`**  
Contains session-specific Parquet datasets:
- `{session_id}_laps.parquet`
- `{session_id}_telemetry.parquet`
- `{session_id}_features.parquet`
- `historical_races.parquet` — persistent historical race database (Phase 5)

**`analytics_output/`**  
Contains session-specific HTML and PNG visualization assets, isolated in a dedicated subdirectory:
- `analytics_output/{session_id}/`
  - `phase1_report_{session_id}.html`
  - `phase2_report_{session_id}.html`
  - `phase3_report_{session_id}.html`
  - `phase4_report_{session_id}.html`
  - `phase5_report_{session_id}.html`
  - Associated PNG assets (e.g., `phase5_predicted_vs_actual.png`, `phase5_feature_importance.png`)

---

## Quick Start

### Requirements
- Python 3.10, 3.11, or 3.12
- Dependencies from `requirements.txt`:
  - `fastf1`
  - `pandas`
  - `matplotlib`
  - `numpy`
  - `arcade`
  - `pyside6`
  - `questionary`
  - `rich`
  - `scipy`
  - `pyarrow>=14.0.0`
  - `seaborn>=0.13.0`
  - `scikit-learn`

### Installation & Execution

```bash
# 1. Clone the repository and navigate to the project directory
git clone https://github.com/Shamsundar-M-S/Data-Science-Project.git
cd Data-Science-Project

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the interactive analysis pipeline
python -m src.analysis.cli_runner
```

### CLI User Experience

When running the CLI, the workflow is:
1. Select Season
2. Select Event
3. Select Session
4. The system checks whether the selected session already exists locally.
5. If cached, the local Parquet data is reused.
6. If not cached, the FastF1 acquisition pipeline obtains the selected session (Phase 0).
7. Phase 1 executes.
8. Phase 2 executes.
9. Phase 3 executes.
10. Phase 4 executes.
11. Phase 5 executes.
12. The localhost report server starts (so relative PNG assets render safely).
13. The browser automatically opens the highest-numbered phase report (no manual file navigation required). All phase reports are listed and accessible.
14. The server remains alive until `Ctrl+C` is pressed.

**Note:** All five phases execute for every session type (Practice, Qualifying, Race). Phase 5 always runs, though its predictions are most meaningful for Race sessions where grid positions and finishing positions are available.

---

## Phase 0 — Data Science Foundation

Phase 0 abstracts FastF1 acquisition into a clean data foundation. It relies on local caching and session isolation to output standard lap data and telemetry data as Parquet files.

### The Clean Lap Source of Truth
Phase 0 introduces a centralized, mathematically rigorous definition of a "clean lap" via the `is_clean_lap` boolean flag. This ensures that laps affected by pit-lane activity (in-laps, out-laps) or Safety Cars/Virtual Safety Cars are universally excluded from pace analysis. This flag serves as the project-wide source of truth for clean-lap filtering.

---

## Phase 1 — Exploratory Data Analysis & Statistics

Phase 1 provides comprehensive statistical evaluation of the lap data using both parametric and non-parametric methods.

**Descriptive Analysis:**
- Data quality profiling
- Lap-time distributions
- Driver performance
- Tyre compound performance
- Tyre age relationships
- Track temperature relationships

**Statistical Analysis:**
Formula 1 data is rarely normally distributed. Phase 1 uses robust methods alongside standard correlation:
- **Kruskal-Wallis H-test** and **effect size (ε²)** for group differences.
- **Spearman** rank correlation for monotonic associations.
- **Pearson** correlation for linear relationships.
- **Weather impact analysis** via Spearman correlation with explicit insufficient-variation guards.

*Note: The project explicitly emphasizes association/correlation and avoids overstating statistical significance or claiming causation.*

---

## Phase 2 — Telemetry Feature Engineering

Phase 2 engineers high-frequency telemetry into structured, per-lap features.

**Engineered Features:**
- `speed_max`, `speed_mean`, `speed_std`
- `throttle_mean`, `throttle_full_pct`
- `brake_active_pct`, `brake_events_count`
- `drs_active_pct`
- `gear_mean`, `gear_max`, `gear_8_pct`
- `telemetry_sample_count`, `distance_span`

**Temporal Isolation:**
These features are calculated at the lap level using telemetry from the corresponding lap. Temporal isolation is absolute: Lap N telemetry generates Lap N features. (Lap N + Lap N+1 telemetry is never allowed to leak into Lap N features).

---

## Phase 3 — Explanatory Modeling

**Objective:** Lap-Time Explanatory Modeling & Telemetry Feature Importance.

Phase 3 builds a `RandomForestRegressor` (n_estimators=100, max_depth=10, random_state=42) against a `DummyRegressor` (mean strategy) baseline to predict the target `LapTime_s` for clean laps (`is_clean_lap == True`). It uses K-Fold Cross Validation (up to 5 folds) and evaluates RMSE and R².

**Features:** `speed_mean`, `throttle_full_pct`, `brake_active_pct`, `drs_active_pct`, `TyreLife`, plus one-hot encoded `Compound`.

**Scientific Framing (Crucial):**
This model is **NOT** for "predicting future lap times", "forecasting the next lap", or establishing the "causal impact of telemetry variables."

Because the telemetry features are contemporaneous with the lap-time target, the model is strictly intended for explanatory analysis, extracting feature importance, and understanding variance.

*Methodological Limitation:* Ordinary K-Fold CV can place laps from the same driver/stint into both training and validation sets, which may produce optimistic performance estimates due to autocorrelation. This is a known limitation of the explanatory setup.

---

## Phase 4 — Performance & Strategy Analysis

Phase 4 executes advanced Data Science on:
1. Tyre degradation
2. Stint pace
3. Driver pace
4. Compound performance
5. Strategy timeline

**Scientific Framing:** Tyre degradation is presented purely as **observational** (observed lap-time evolution). The calculated slope is not "pure tyre degradation" because it is heavily confounded by factors such as fuel burn-off and track evolution. Furthermore, strategy timeline analysis has session-specific semantics and gracefully adapts depending on whether the session is a Race or not (strategy timeline visualizations are generated only for Race sessions).

---

## Phase 5 — Race Outcome Prediction

**Objective:** Pre-race prediction of final finishing position using historical data and pre-race features.

**Prediction Timing:** Conceptually, the prediction is performed *after Qualifying* and *before the Sunday Race start*. Only pre-race information is utilized — no in-race data, pit-stop timing, weather changes, or lap times from the target race are included in the feature vector.

### Observation Unit & Target
- **Observation unit:** Driver × Race
- **Primary target:** Finishing position (continuous regression value, ranked to produce predicted order)

### Features
**Numeric features:**
- `grid_position` — Sunday starting grid position
- `qualifying_delta_pct` — percentage gap from pole time
- `driver_rolling_avg_finish` — driver's mean finishing position over last 5 completed races (strictly prior)
- `team_rolling_avg_points` — constructor's mean points per race over last 5 completed races (strictly prior)
- `championship_position` — driver's championship standing from accumulated points in the current season prior to this race

**Categorical features:**
- `driver_id`, `constructor_id`, `circuit_id`
- Encoded using `OrdinalEncoder` with `handle_unknown="use_encoded_value"` and `unknown_value=-1`

### Model
- **Primary model:** `HistGradientBoostingRegressor` (max_iter=100, max_depth=5, min_samples_leaf=10, random_state=42, with `categorical_features` specified)
- **Baselines:**
  - Grid Position MAE (predicting finish = grid)
  - Championship Position MAE (predicting finish = championship standing)

### Validation
- **Expanding-window temporal validation:** The historical race set is ordered chronologically. The last ~30% of races (minimum 2) serve as validation races. For each validation race, the model is trained on all chronologically preceding races and evaluated on the held-out race.
- **Metrics:** MAE, Spearman rank correlation, and Top-3 (podium) overlap percentage, averaged across validation races.
- **Permutation feature importance** is computed on validation-set data during temporal validation folds.

### Historical Database
Phase 5 relies on a persistent historical race database stored at `analytics_data/historical_races.parquet`.

- **Schema:** season, round, event_name, circuit_id, driver_id, constructor_id, grid_position, qualifying_time, pole_time, qualifying_delta_pct, finishing_position, points, status.
- **Persistence:** Saved in Parquet format. New race observations are incrementally added; existing records with matching (season, round, driver_id) are replaced to prevent duplication.
- **Default initialization:** If the database does not exist on first run, a baseline dataset covering 3 seasons (2022–2024) with 12 rounds per season for 20 drivers is generated using plausible simulated data. This ensures Phase 5 has sufficient historical data even on fresh installations.
- **Historical feature construction** uses strictly shifted (prior-only) computations. A race's own finishing position, points, or results never enter its own feature vector.

### Reports & Visualizations
Phase 5 generates:
- `phase5_report_{session_id}.html` — HTML report with model metrics, predicted finishing order table, methodology description, and embedded visualizations
- `phase5_predicted_vs_actual.png` — starting grid vs predicted rank (and actual finish for completed races)
- `phase5_feature_importance.png` — permutation feature importance bar chart

The report distinguishes between **completed races** (with actual vs predicted comparison and race-specific metrics) and **prediction-only races** (where actual results are not yet available).

### Scientific Limitations (Phase 5)
- **Default historical data** is synthetically generated; it represents plausible but not real F1 race results. Predictions improve as more real sessions are ingested.
- **Grid position and qualifying delta** are extracted from session lap data. The availability and accuracy of these fields depends on the FastF1 data for the selected session.
- **Championship position** is derived from accumulated points in the database for the current season prior to the race. For the first round of a season (or if no prior data exists), the fallback is the driver's grid position or a default value of 10.
- **Rolling averages** use the last 5 races. For drivers with fewer than 5 prior completed races, the average is computed over whatever history is available; if no history exists, grid position or a default of 10.0 is used.
- **Temporal validation** is performed over the historical races in the database. The quality and realism of validation metrics depend on the historical data available.
- **The model is a regression on finishing position** — it does not model DNFs, race incidents, safety cars, weather changes, or strategic decisions during the race.
- Results should not be described as "genuinely predictive" without careful evaluation of validation metrics on real historical data.

---

## Scientific Limitations

The project explicitly acknowledges the following real-world F1 limitations:
- Fuel load is not directly modeled or controlled.
- Fuel burn-off heavily influences lap time.
- Track evolution, traffic, and driver behavior influence lap time.
- Setup differences influence performance.
- Weather and track conditions can change mid-session.
- Telemetry-derived features are contemporaneous, not leading indicators.
- Repeated laps from the same driver/stint are not necessarily independent observations.
- Small sessions (e.g., interrupted practices) can produce unstable statistical estimates.
- Observed relationships should not automatically be interpreted as causal.
- Phase 5 historical features depend on data availability and the quality of the historical database.

---

## Robustness

The codebase includes several active robustness mechanisms:
- Cached-session detection
- Strict session isolation (Phases 0–4)
- Chronological feature construction with strict shifting (Phase 5)
- Missing telemetry and insufficient data handling
- Degenerate KDE fallback (to standard histograms if distributions lack variance)
- Missing/NaN handling throughout all phases
- Graceful model fallback (e.g., Phase 3 and Phase 5 skip modeling with insufficient samples)
- Non-Race strategy handling (Phase 4 strategy timeline only for Race sessions)
- Unknown categorical handling via `OrdinalEncoder` with `unknown_value=-1` (Phase 5)
- Incremental historical database updates with deduplication on (season, round, driver_id)
- Relative HTML asset paths delivered via a browser-safe localhost server

---

## Testing

The project uses `pytest` to protect analytical logic. CI is configured via GitHub Actions across Python 3.10, 3.11, and 3.12.

The current test suite result:
- **134 passed**
- **4 skipped** (optional `arcade` dependency not installed)
- **3 warnings** (third-party seaborn deprecation)

The tests cover feature engineering, braking-event logic, KDE robustness, report generation, report assets, Phase 3 modeling, Phase 4 strategy, Phase 5 modeling, historical database operations, temporal validation, categorical robustness, multi-session behavior, report server, and E2E flows.

---

## Project Structure

```
├── analytics_data/         # Generated Parquet datasets (git-ignored)
├── analytics_output/       # Generated HTML/PNG reports (git-ignored)
├── docs/                   # Additional documentation
├── src/                    # Source Code
│   ├── analysis/           # Phase 0-5 Analytical Logic
│   │   ├── cli_runner.py       # Interactive CLI entry point
│   │   ├── clean_laps.py       # Clean lap definition
│   │   ├── export.py           # Phase 0 data export
│   │   ├── eda.py              # Phase 1 EDA
│   │   ├── statistics.py       # Phase 1 statistics
│   │   ├── features.py         # Phase 2 feature engineering
│   │   ├── run_phase1.py       # Phase 1 runner
│   │   ├── run_phase2.py       # Phase 2 runner
│   │   ├── run_phase3.py       # Phase 3 runner
│   │   ├── run_phase4.py       # Phase 4 runner
│   │   ├── run_phase5.py       # Phase 5 runner
│   │   ├── historical_db.py    # Historical race database
│   │   ├── strategy.py         # Tyre & strategy analysis
│   │   ├── report.py           # Phase 1 HTML report
│   │   ├── report_phase2.py    # Phase 2 HTML report
│   │   ├── report_phase3.py    # Phase 3 HTML report
│   │   ├── report_phase4.py    # Phase 4 HTML report
│   │   ├── report_phase5.py    # Phase 5 HTML report
│   │   ├── report_server.py    # Localhost HTTP report server
│   │   └── plot_style.py       # Shared plot styling
│   ├── gui/                # GUI components
│   ├── insights/           # Insight windows
│   ├── lib/                # Shared utilities
│   ├── f1_data.py          # FastF1 handlers
│   └── main.py             # Legacy GUI entry point
├── tests/                  # Pytest suite
│   ├── analysis/           # Phase & module tests
│   └── lib/                # Utility tests
├── .github/workflows/      # CI configuration
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .gitignore
└── README.md               # This file
```
