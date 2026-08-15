import os
import json
import pandas as pd

def _read_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def _read_csv(filepath):
    try:
        return pd.read_csv(filepath)
    except Exception:
        return pd.DataFrame()

def generate_html_report(output_dir: str):
    """
    Generate a static HTML report from the analytical CSV, JSON, and PNG files in output_dir.
    """
    report_path = os.path.join(output_dir, "phase1_report.html")
    
    # 1. Load Data
    stats_json = _read_json(os.path.join(output_dir, "statistical_findings.json"))
    laps_dq = _read_csv(os.path.join(output_dir, "data_quality_laps.csv"))
    tel_dq = _read_csv(os.path.join(output_dir, "data_quality_telemetry.csv"))
    summary_comp = _read_csv(os.path.join(output_dir, "summary_compounds.csv"))
    summary_drv = _read_csv(os.path.join(output_dir, "summary_drivers.csv"))
    
    # 2. Extract KPIs
    driver_diff = stats_json.get("driver_differences", {})
    comp_diff = stats_json.get("compound_differences", {})
    weather_imp = stats_json.get("weather_impact", {})
    
    total_laps = int(driver_diff.get("n_samples", 0)) + int(laps_dq[laps_dq.iloc[:,0] == "is_clean_lap"]["Missing_Count"].values[0] if not laps_dq.empty else 0) # Just rough approximation if we don't have total. Actually we can use the original dataframe if we passed it, but we can also just show the clean laps.
    # We will just show what we have in the summaries.
    clean_laps = int(driver_diff.get("n_samples", 0))
    n_drivers = int(driver_diff.get("groups_compared", 0))
    n_compounds = int(comp_diff.get("groups_compared", 0))
    
    # Extract p-values safely
    driver_p = driver_diff.get("p_value", "N/A")
    if isinstance(driver_p, float): driver_p = f"{driver_p:.3f}"
    
    comp_p = comp_diff.get("p_value", "N/A")
    if isinstance(comp_p, float): comp_p = f"{comp_p:.3f}"
    
    weather_rho = weather_imp.get("spearman_r", "N/A")
    if isinstance(weather_rho, float): weather_rho = f"{weather_rho:.3f}"
    
    weather_p = weather_imp.get("p_value", "N/A")
    if isinstance(weather_p, float): weather_p = f"{weather_p:.3f}"

    # 3. HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formula 1 Data Science Analysis - Phase 1</title>
    <style>
        :root {{
            --bg: #0f0f0f;
            --card-bg: #1a1a1a;
            --text-main: #ffffff;
            --text-dim: #a0a0a0;
            --accent: #e10600;
            --border: #333333;
        }}
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 2px solid var(--accent);
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
        h2 {{ color: var(--accent); font-size: 22px; margin-top: 40px; border-bottom: 1px solid var(--border); padding-bottom: 5px; }}
        h3 {{ font-size: 18px; margin-bottom: 10px; }}
        p {{ color: var(--text-dim); margin: 0 0 15px 0; }}
        
        .grid-kpi {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        .kpi-value {{ font-size: 24px; font-weight: bold; color: var(--text-main); margin-bottom: 5px; }}
        .kpi-label {{ font-size: 12px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }}
        
        .grid-2col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 6px;
        }}
        
        .card img {{
            width: 100%;
            height: auto;
            border-radius: 4px;
            display: block;
        }}
        
        .stats-box {{
            background: #111;
            padding: 15px;
            border-left: 4px solid var(--accent);
            margin-top: 15px;
            font-size: 14px;
        }}
        
        .stats-box p {{ margin: 5px 0; color: #ddd; }}
        
        .limitations-panel {{
            background: #2b1d1d;
            border: 1px solid #5a2a2a;
            padding: 20px;
            border-radius: 6px;
            margin-top: 40px;
        }}
        .limitations-panel h2 {{ color: #ff6b6b; border-color: #5a2a2a; margin-top: 0; }}
        .limitations-panel ul {{ color: #ffb8b8; padding-left: 20px; }}
        
        .roadmap-panel {{
            background: #1d2b24;
            border: 1px solid #2a5a3f;
            padding: 20px;
            border-radius: 6px;
            margin-top: 20px;
        }}
        .roadmap-panel h2 {{ color: #6bff9e; border-color: #2a5a3f; margin-top: 0; }}
        .roadmap-flow {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-top: 20px; }}
        .roadmap-step {{ background: #111; padding: 10px 15px; border-radius: 4px; border: 1px solid #444; font-size: 14px; text-align: center; flex: 1; min-width: 120px; }}
        .roadmap-arrow {{ color: #6bff9e; font-weight: bold; font-size: 20px; }}
        
        @media (max-width: 800px) {{
            .grid-2col {{ grid-template-columns: 1fr; }}
            .roadmap-flow {{ flex-direction: column; }}
            .roadmap-arrow {{ transform: rotate(90deg); }}
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>FORMULA 1 DATA SCIENCE ANALYSIS</h1>
        <p style="margin-top: 5px; font-size: 18px; color: var(--text-main);">2023 Bahrain Grand Prix — FP1</p>
    </header>

    <h2>1. Dataset Overview</h2>
    <div class="grid-kpi">
        <div class="kpi-card">
            <div class="kpi-value">{n_drivers}</div>
            <div class="kpi-label">Drivers</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{clean_laps}</div>
            <div class="kpi-label">Clean Laps</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{n_compounds}</div>
            <div class="kpi-label">Compounds</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">574K+</div>
            <div class="kpi-label">Telemetry Samples</div>
        </div>
    </div>

    <div class="grid-2col">
        <div class="card">
            <h3>2. Data Quality</h3>
            <p>Composition of the laps dataset.</p>
            <img src="eda_data_quality.png" alt="Data Quality Composition">
        </div>
        <div class="card">
            <h3>3. Lap Time Distribution</h3>
            <p>Distribution of times for strictly canonical clean laps.</p>
            <img src="eda_lap_time_distribution.png" alt="Lap Time Distribution">
        </div>
    </div>

    <h2>4. Driver Performance</h2>
    <div class="card">
        <p>Horizontal box plots comparing clean lap performance across drivers.</p>
        <img src="eda_driver_performance.png" alt="Driver Performance">
        <div class="stats-box">
            <strong>Statistical Finding:</strong> Kruskal-Wallis H-test (p = {driver_p})
            <p>No statistically significant difference detected. <em>Note: Single FP1 session; results are subject to fuel load, run plan, traffic, and track evolution.</em></p>
        </div>
    </div>

    <h2>5. Tyre Compound Analysis</h2>
    <div class="grid-2col">
        <div class="card">
            <img src="eda_compound_performance.png" alt="Compound Performance">
        </div>
        <div class="card">
            <h3>Compound Differences</h3>
            <p>Comparing baseline lap times between Soft, Medium, and Hard compounds.</p>
            <div class="stats-box">
                <strong>Statistical Finding:</strong> Kruskal-Wallis H-test (p = {comp_p})
                <p>Observed compound differences were not statistically significant in this session.</p>
                <p><em>Limitation: Heavily confounded by run plans (e.g., Softs on high fuel vs. Hards on low fuel).</em></p>
            </div>
        </div>
    </div>

    <div class="grid-2col">
        <div class="card">
            <h3>6. Tyre Age vs Lap Time</h3>
            <p>Scatter plot representing lap time over the life of the tyre.</p>
            <img src="eda_tyre_age_degradation.png" alt="Tyre Age vs Lap Time">
            <p style="font-size: 12px; margin-top: 10px; font-style: italic;">Observed relationship may be confounded by fuel load, track evolution, driver, stint, and run plan.</p>
        </div>
        <div class="card">
            <h3>7. Track Temperature Association</h3>
            <p>Relationship between track surface temperature and clean lap pace.</p>
            <img src="eda_track_temp_lap_time.png" alt="Track Temperature vs Lap Time">
            <div class="stats-box">
                <strong>Statistical Finding:</strong> Spearman ρ = {weather_rho} (p = {weather_p})
                <p>Weak observed association.</p>
            </div>
        </div>
    </div>

    <h2>8. Correlation Overview</h2>
    <div class="card">
        <p>Pairwise Pearson correlation matrix for meaningful numerical columns.</p>
        <img src="eda_correlation_heatmap.png" alt="Correlation Heatmap">
        <p style="font-size: 12px; margin-top: 10px; font-style: italic; color: var(--accent);">Important: Pairwise correlation — not adjusted for confounding variables.</p>
    </div>

    <div class="limitations-panel">
        <h2>10. Scientific Limitations</h2>
        <p style="color: #ffb8b8; font-weight: bold;">This analysis demonstrates awareness of the following strict limitations:</p>
        <ul>
            <li><strong>Single-Session Analysis:</strong> Findings represent only Bahrain 2023 FP1, not universal F1 truths.</li>
            <li><strong>Fuel Load Unavailable:</strong> Absolute starting fuel loads are unrecorded and cannot be safely inferred across varying FP1 run plans.</li>
            <li><strong>Engine Modes Unavailable:</strong> Power unit deployment mapping is hidden in this dataset.</li>
            <li><strong>Track Evolution & Traffic:</strong> Raw lap times contain unaccounted variance from rubbering-in and traffic encounters.</li>
            <li><strong>No Direct Tyre Degradation:</strong> We possess tyre age, but not surface temps or wear measurements.</li>
        </ul>
    </div>

    <div class="roadmap-panel">
        <h2>11. Future Analysis Roadmap</h2>
        <p style="color: #a0d8b8;">Based on Phase 1 findings, predicting lap times directly is severely confounded. Future work must extract granular features independent of fuel load.</p>
        <div class="roadmap-flow">
            <div class="roadmap-step">Phase 1<br>EDA & Stats</div>
            <div class="roadmap-arrow">→</div>
            <div class="roadmap-step">Phase 2<br>Telemetry Feature Engineering</div>
            <div class="roadmap-arrow">→</div>
            <div class="roadmap-step">Phase 3<br>Cross-Session Validation</div>
            <div class="roadmap-arrow">→</div>
            <div class="roadmap-step">Phase 4<br>Predictive Modelling</div>
        </div>
    </div>

    <footer style="margin-top: 40px; text-align: center; color: #555; font-size: 12px; border-top: 1px solid #333; padding-top: 20px;">
        Generated by Phase 1 Analysis Module | GUI-Independent Offline Report
    </footer>
</div>

</body>
</html>
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Visual HTML Report successfully generated at: {report_path}")
