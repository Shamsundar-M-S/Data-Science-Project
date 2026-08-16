# Formula 1 Data Science & Telemetry Analytics Platform

A comprehensive Python pipeline for acquiring, cleaning, analyzing, and visualizing Formula 1 race telemetry.

This project is a dedicated Data Science and analytics platform. Its primary focus is robust telemetry processing, exploratory data analysis (EDA), statistical evaluation, feature engineering, and reproducible graphical reporting. 

> **Note:** This is currently an analytical and feature-engineering project, not an active Machine Learning or predictive platform. Advanced ML, clustering, and forecasting are planned for a future Phase 3.

---

## Project Architecture

The pipeline processes raw F1 telemetry through a strict multi-phase architecture. Each phase builds upon the outputs of the previous phase to ensure reproducibility and temporal integrity:

**Raw FastF1 Data**  
↓  
**Phase 0:** Data Extraction & Clean Analytical Dataset  
↓  
**Phase 1:** EDA + Statistics  
↓  
**Phase 1:** Graphical Report  
↓  
**Phase 2:** Telemetry Feature Engineering  
↓  
**Phase 2:** Feature Dataset  
↓  
**Phase 2:** Graphical Report  
↓  
*(Future) Phase 3: Advanced Modeling / ML*

---

## Quick Start

### Requirements
- Python 3.12.10
- Virtual environment (`venv312`)

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

Upon executing the CLI runner, you will be prompted to select a **Season**, **Event**, and **Session**. The pipeline will automatically acquire data, process it through Phases 0–2, and launch a local HTTP server to display your interactive graphical reports.

---

## Multi-Session Architecture

The platform supports generic multi-session and multi-race analysis. You are not restricted to a single hardcoded race. 

Users interactively select the desired Session, which generates a canonical **`session_id`** (e.g., `2026_09_British_Grand_Prix_Race`, `2023_01_Bahrain_Grand_Prix_Practice_1`).

The selected session dictates the entire pipeline:
- `FastF1` dynamically fetches the correct data.
- Isolated Phase 0 datasets are generated.
- Phase 1 and Phase 2 logic processes only that specific session.
- Output graphical assets and HTML reports are sandboxed within `analytics_output/{session_id}/`.

**No cross-session data leakage occurs.**

### Local Cache Behavior
To ensure high performance and prevent unnecessary API limits:
1. The application checks whether the required Phase 0 analytical Parquet datasets already exist locally.
2. If they exist, the pipeline bypasses the FastF1 API and loads data directly from the local disk cache.
3. If they do not exist, the required session is fetched via FastF1, structured into Parquet files by Phase 0, and permanently cached for future runs.

---

## Phase 0 — Data Science Foundation

Phase 0 abstracts raw FastF1 acquisition into a clean, GUI-independent data foundation suitable for pure Pandas-based analytics.

It creates two primary, session-isolated Parquet datasets:
1. `{session_id}_laps.parquet`: High-level lap metadata and timings.
2. `{session_id}_telemetry.parquet`: High-frequency, flat time-series telemetry data (e.g., `Distance`, `Speed`, `nGear`, `Throttle`, `Brake`, `DRS`, `X`, `Y`, `SessionTime`).

### The Clean Lap Source of Truth
Phase 0 introduces a centralized, mathematically rigorous definition of a "clean lap" via the `is_clean_lap` boolean flag. This flag considers:
- Pit-lane activity (in-laps, out-laps).
- Laps affected by Safety Cars or Virtual Safety Cars.
- FastF1 telemetry accuracy indicators.

The `is_clean_lap` flag is universally utilized by Phase 1 and Phase 2 to filter out anomalous data points before performing sensitive statistical analyses.

---

## Phase 1 — Exploratory Data Analysis & Statistics

Phase 1 provides a comprehensive, non-parametric evaluation of the Phase 0 lap data.

**Data Quality:**
- Missing-value profiling and unique-value counts.
- Integrity checks for telemetry accuracy.

**Descriptive Analysis:**
- Lap-time distributions.
- Comparative driver performance evaluations.
- Tyre compound performance.
- Tyre age degradation profiling.

**Statistical Analysis:**
Formula 1 data is rarely normally distributed. Phase 1 actively embraces robust non-parametric tests:
- **Kruskal-Wallis H-test** for evaluating significant differences across groups (e.g., compound performance).
- **Spearman rank correlation** and **Pearson correlation** to identify associations between continuous variables (e.g., Track Temperature vs. Lap Time).

*(Note: These are observed associations. The pipeline explicitly acknowledges the absence of causal inference variables like Fuel Load and Engine Modes.)*

### Phase 1 Graphical Report
Phase 1 automatically compiles its EDA and statistical findings into a standalone HTML graphical report containing:
- Dataset overviews and data quality summaries.
- Box plots of tyre compound performance.
- Distribution curves of lap times.
- Linear regression models of tyre age vs lap time.
- Track temperature correlations.

---

## Phase 2 — Telemetry Feature Engineering

Phase 2 transforms the high-frequency telemetry matrices generated in Phase 0 into highly structured, per-lap analytical features. 

The resulting `{session_id}_features.parquet` dataset contains **one row per driver per lap**. Telemetry metrics are securely aggregated using strict temporal isolation: telemetry from Lap `N` is never allowed to leak into the calculation for Lap `N+1`.

### Engineered Feature Profiles
- **Speed:** `speed_max`, `speed_mean`, `speed_std`
- **Throttle:** `throttle_mean`, `throttle_full_pct`
- **Braking:** `brake_active_pct`, `brake_events_count` *(Calculates continuous braking event blocks rather than raw sample frames)*
- **DRS:** `drs_active_pct` *(Evaluates active states based on canonical thresholds)*
- **Gears:** `gear_mean`, `gear_max`, `gear_8_pct`
- **Quality Metrics:** `telemetry_sample_count`, `distance_span`

The feature dataset strictly retains required contextual metadata (`Driver`, `LapNumber`, `LapTime_s`, `Compound`, `TyreLife`, `TrackTemp`, `is_clean_lap`).

### Phase 2 Graphical Report
The engineered features are automatically visualized in a dedicated HTML report:
- **Distribution Visualizations:** Analyzes the spread of Speed, Throttle, Braking, DRS, and Gear usage across the grid.
- **Relationship Visualizations:** Scatter plots analyzing the direct effect of engineered features on lap times.
- **Correlation Matrix:** A heatmap evaluating collinearity among the engineered features.

#### Visualization Robustness
Real-world F1 data frequently contains degenerate distributions (e.g., drivers who never activated DRS during a rain-affected session, resulting in zero-variance arrays). The Phase 2 pipeline dynamically validates statistical viability before rendering plots. If Kernel Density Estimation (KDE) is mathematically unsafe (e.g., singular covariance matrices), the pipeline seamlessly disables KDE and falls back to rendering standard histograms. This guarantees that visual analysis never crashes and never drops valid data points.

---

## Graphical Report Delivery

The user experience terminates with a fully automated reporting flow:
1. Upon analysis completion, the CLI boots a native, dependency-free local HTTP server.
2. The server seamlessly maps to the output analytics directory.
3. The Phase 2 Graphical Report is automatically popped open in your default web browser.
4. Relative asset paths (PNGs, CSS) reliably resolve via `localhost`, completely bypassing restrictive `file://` protocol limitations.
5. The local server stays alive (`Ctrl+C` to quit), allowing the user ample time to interrogate the generated interactive HTML reports for both Phase 1 and Phase 2.
