import os
import pandas as pd

def generate_phase2_report(output_dir: str, session_metadata: dict, session_id: str):
    """Generate the static Phase 2 HTML report."""
    report_path = os.path.join(output_dir, f"phase2_report_{session_id}.html")
    # Features are still written to analytics_data, so we read from there. Wait, no.
    # The caller passed session_output_dir.
    # We need to read from analytics_data/session_id_features.parquet
    # Let's pass the features_path dynamically, or just reconstruct it.
    parent_dir = os.path.dirname(output_dir) # this is analytics_output
    data_dir = "analytics_data"
    features_path = os.path.join(data_dir, f"{session_id}_features.parquet")
    
    # Load feature dataset for KPI extraction
    if os.path.exists(features_path):
        df_feat = pd.read_parquet(features_path)
        total_laps = len(df_feat)
        clean_laps = df_feat["is_clean_lap"].sum()
        drivers = df_feat["Driver"].nunique()
        total_features = df_feat.shape[1] - 7  # Exclude metadata columns
        tel_samples = df_feat["telemetry_sample_count"].sum()
    else:
        total_laps = clean_laps = drivers = total_features = tel_samples = 0
        
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1 Phase 2 - Telemetry Feature Engineering</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --text-color: #f8fafc;
            --muted-color: #94a3b8;
            --accent-color: #38bdf8;
            --border-color: #334155;
            --warning-color: #f59e0b;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{ color: var(--text-color); }}
        h1 {{ border-bottom: 2px solid var(--accent-color); padding-bottom: 10px; margin-bottom: 30px; }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .kpi-card {{
            background-color: var(--surface-color);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .kpi-value {{ font-size: 2rem; font-weight: bold; color: var(--accent-color); margin-bottom: 5px; }}
        .kpi-label {{ font-size: 0.9rem; color: var(--muted-color); text-transform: uppercase; letter-spacing: 1px; }}
        .section {{ margin-bottom: 50px; background-color: var(--surface-color); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); }}
        .plot-container {{ text-align: center; margin: 20px 0; overflow: hidden; }}
        .plot-img {{ max-width: 100%; height: auto; border-radius: 4px; border: 1px solid var(--border-color); }}
        .flex-row {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
        .flex-item {{ flex: 1 1 450px; text-align: center; }}
        .alert {{
            padding: 15px; border-radius: 6px; margin: 20px 0;
            background-color: rgba(245, 158, 11, 0.1); border-left: 4px solid var(--warning-color);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="session-header">
            <h2>FORMULA 1 DATA SCIENCE ANALYSIS</h2>
            <h1>{session_metadata.get('season', '')} {session_metadata.get('event', '')}</h1>
            <h3>{session_metadata.get('session_type', '')}</h3>
        </div>
        
        <h2>Phase 2: Telemetry Feature Engineering</h2>
        <p style="color: var(--muted-color); margin-top: -10px; margin-bottom: 30px;">ID: {session_id}</p>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value">{total_laps}</div>
                <div class="kpi-label">Total Laps</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{clean_laps}</div>
                <div class="kpi-label">Clean Laps Analysed</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{drivers}</div>
                <div class="kpi-label">Drivers</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{total_features}</div>
                <div class="kpi-label">Engineered Features</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{tel_samples:,}</div>
                <div class="kpi-label">Telemetry Samples</div>
            </div>
        </div>

        <div class="alert">
            <strong>Scientific Limitations:</strong> This analysis evaluates a single F1 practice session. Essential confounding variables such as Fuel Load, Engine Modes, and Traffic are unavailable. All relationships displayed below are observed correlations and do not imply strict causation.
        </div>

        <div class="section">
            <h2>Speed Profile</h2>
            <div class="flex-row">
                <div class="flex-item"><img src="dist_speed_mean.png" class="plot-img" alt="Speed Distributions"></div>
                <div class="flex-item"><img src="scatter_speed_mean_vs_laptime.png" class="plot-img" alt="Speed vs Lap Time"></div>
            </div>
        </div>

        <div class="section">
            <h2>Throttle Profile</h2>
            <div class="flex-row">
                <div class="flex-item"><img src="dist_throttle_full_pct.png" class="plot-img" alt="Throttle Distributions"></div>
                <div class="flex-item"><img src="scatter_throttle_full_pct_vs_laptime.png" class="plot-img" alt="Throttle vs Lap Time"></div>
            </div>
        </div>

        <div class="section">
            <h2>Braking Profile</h2>
            <p style="color: var(--muted-color); font-size: 0.9em; text-align: center;">Braking events denote continuous blocks of Brake=True telemetry samples.</p>
            <div class="flex-row">
                <div class="flex-item"><img src="dist_brake_active_pct.png" class="plot-img" alt="Braking Distributions"></div>
                <div class="flex-item"><img src="scatter_brake_active_pct_vs_laptime.png" class="plot-img" alt="Braking vs Lap Time"></div>
            </div>
        </div>

        <div class="section">
            <h2>DRS & Gear Profile</h2>
            <div class="flex-row">
                <div class="flex-item"><img src="dist_drs_active_pct.png" class="plot-img" alt="DRS Profile"></div>
                <div class="flex-item"><img src="dist_gear_mean.png" class="plot-img" alt="Gear Profile"></div>
            </div>
        </div>

        <div class="section">
            <h2>Feature Correlation Matrix</h2>
            <div class="plot-container">
                <img src="feature_correlation.png" class="plot-img" alt="Correlation Heatmap">
            </div>
        </div>

    </div>
</body>
</html>
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
