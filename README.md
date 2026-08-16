# Formula 1 Data Science & Telemetry Analytics Platform

A comprehensive Python pipeline for acquiring, cleaning, analyzing, and visualizing Formula 1 race telemetry.

This project is a dedicated Data Science and analytics platform. Its primary focus is robust telemetry processing, exploratory data analysis (EDA), statistical evaluation, feature engineering, lap-time explanatory modeling, strategy analytics, and reproducible graphical reporting.

Visualization is a **core project requirement**: the platform is visualization-first in its user-facing output. Analytical results are presented through interactive, session-specific graphical HTML reports containing KPI summaries, EDA plots, feature distributions, scatter plots, correlation matrices, model diagnostics, feature importance, tyre degradation trends, stint analysis, driver pace, compound analysis, and strategy visualizations.

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
- Phase 1, 2, 3, and 4 logic processes only that specific session.
- No cross-session data leakage occurs.

---

## Outputs

The project strictly separates analytical datasets from generated reports.

**`analytics_data/`**  
Contains session-specific Parquet datasets:
- `{session_id}_laps.parquet`
- `{session_id}_telemetry.parquet`
- `{session_id}_features.parquet`

**`analytics_output/`**  
Contains session-specific HTML and PNG visualization assets, isolated in a dedicated subdirectory:
- `analytics_output/{session_id}/`
  - `phase1_report_{session_id}.html`
  - `phase2_report_{session_id}.html`
  - `phase3_report_{session_id}.html`
  - `phase4_report_{session_id}.html`
  - Associated PNG assets

---

## Quick Start

### Requirements
- Python 3.12.10
- Virtual environment (`venv312`)
- Dependencies (from `requirements.txt`):
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

```powershell
# 1. Clone the repository and navigate to the project directory
cd "C:\Data Science Project"

# 2. Activate the virtual environment
.\venv312\Scripts\activate

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
11. The localhost report server starts (so relative PNG assets render safely).
12. The browser automatically opens the generated report (no manual file navigation required).
13. The server remains alive until `Ctrl+C` is pressed.

---

## Phase 0 — Data Science Foundation

Phase 0 abstracts FastF1 acquisition into a clean data foundation. It relies on local caching and session isolation to output standard lap data and telemetry data as Parquet files.

### The Clean Lap Source of Truth
Phase 0 introduces a centralized, mathematically rigorous definition of a "clean lap" via the `is_clean_lap` boolean flag. This ensures that laps affected by pit-lane activity (in-laps, out-laps) or Safety Cars/Virtual Safety Cars are universally excluded from pace analysis. This flag serves as the project-wide source of truth for clean-lap filtering.

---

## Phase 1 — Exploratory Data Analysis & Statistics

Phase 1 provides comprehensive, non-parametric evaluation of the lap data.

**Descriptive Analysis:**
- Data quality profiling
- Lap-time distributions
- Driver performance
- Tyre compound performance
- Tyre age relationships
- Track temperature relationships

**Statistical Analysis:**
Formula 1 data is rarely normally distributed. Phase 1 embraces robust methods:
- **Kruskal-Wallis H-test** and **effect size** for group differences.
- **Spearman** and **Pearson** correlations for continuous variables.

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

Phase 3 builds a `RandomForestRegressor` against a `DummyRegressor` baseline to predict the target `LapTime_s` for clean laps (`is_clean_lap == True`). It uses K-Fold Cross Validation and evaluates RMSE and R².

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

**Scientific Framing:** Tyre degradation is presented purely as **observational** (observed lap-time evolution). The calculated slope is not "pure tyre degradation" because it is heavily confounded by factors such as fuel burn-off and track evolution. Furthermore, strategy timeline analysis has session-specific semantics and gracefully adapts depending on whether the session is a Race or not.

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

---

## Robustness

The codebase includes several active robustness mechanisms:
- Cached-session detection
- Strict session isolation
- Missing telemetry and insufficient data handling
- Degenerate KDE fallback (to standard histograms if distributions lack variance)
- Missing/NaN handling
- Graceful model fallback
- Non-Race strategy handling
- Relative HTML asset paths delivered via a browser-safe localhost server

---

## Testing

The project uses `pytest` to protect analytical logic. At the time of the final diagnostic, the test suite result was:
- 123 tests passed
- 0 failed
- 0 skipped
- 21 warnings (third-party deprecations)

The tests cover feature engineering, braking-event logic, KDE robustness, report generation, report assets, Phase 3 modeling, Phase 4 strategy, multi-session behavior, and E2E flows.

---

## Project Structure

```
C:\Data Science Project\
├── analytics_data/         # Generated Parquet datasets
├── analytics_output/       # Generated HTML/PNG reports (git ignored)
├── docs/                   # Additional documentation
├── src/                    # Source Code
│   ├── analysis/           # Phase 0-4 Analytical Logic
│   ├── lib/                # Shared utilities
│   ├── gui/                # (Deprecated/Legacy UI)
│   ├── f1_data.py          # FastF1 handlers
│   └── main.py             # (Legacy entry point)
├── tests/                  # Pytest suite
│   ├── analysis/
│   └── lib/
├── requirements.txt
├── .gitignore
└── README.md               # This file
```
