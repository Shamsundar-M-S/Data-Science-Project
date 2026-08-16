import os
import json

def generate_phase3_report(output_dir: str, session_id: str, metrics: dict):
    """Generate the static Phase 3 HTML report."""
    report_path = os.path.join(output_dir, f"phase3_report_{session_id}.html")
    
    status = metrics.get('status', 'error')
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1 Phase 3 - Advanced Data Science / Modeling</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --accent: #ef4444;
            --accent-hover: #dc2626;
            --border: #334155;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        
        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            margin-bottom: 3rem;
            border-bottom: 2px solid var(--border);
            padding-bottom: 1rem;
        }}
        
        h1 {{
            font-size: 2.5rem;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }}
        
        .session-id {{
            color: var(--accent);
            font-family: monospace;
            font-size: 1.2rem;
        }}
        
        .section {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        
        h2 {{
            color: var(--text-primary);
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }}
        
        .chart-container {{
            width: 100%;
            overflow: hidden;
            border-radius: 8px;
            background: #fff;
            margin-bottom: 1.5rem;
        }}
        
        .chart-container img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .metric-card {{
            background: var(--bg-color);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent);
        }}
        
        .metric-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .error-state {{
            background: #7f1d1d;
            border-left: 4px solid var(--accent);
            padding: 1.5rem;
            border-radius: 4px;
            margin-bottom: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>F1 Phase 3 - Lap-Time Explanatory Modeling & Telemetry Feature Importance</h1>
            <div class="session-id">{session_id}</div>
        </header>

        <div class="section" style="border-left: 4px solid var(--accent); background-color: #2a1b1b;">
            <h2 style="color: var(--accent); margin-bottom: 0.5rem; font-size: 1.4rem;">Scientific Interpretation Warning</h2>
            <p><strong>This model uses telemetry-derived characteristics observed during the completed lap. It is an explanatory/contemporaneous model and should not be interpreted as a pre-lap forecasting system.</strong></p>
            <p style="margin-top: 0.5rem; color: var(--text-secondary);">The research objective is to determine to what extent telemetry characteristics and context variables from a completed clean lap explain variation in that lap's recorded time. Observed association does not establish causation.</p>
        </div>

"""

    if status == 'insufficient_data':
        html_content += f"""
        <div class="error-state">
            <h3>Insufficient Data</h3>
            <p>This session only contains {metrics.get('n_samples', 0)} clean laps. A minimum of 10 samples is required to perform robust K-Fold Cross Validation for Machine Learning. Phase 3 has gracefully degraded.</p>
        </div>
        """
    else:
        # Success state
        rf_r2 = f"{metrics.get('rf_r2', 0):.3f}"
        rf_rmse = f"{metrics.get('rf_rmse', 0):.3f}s"
        dummy_r2 = f"{metrics.get('dummy_r2', 0):.3f}"
        dummy_rmse = f"{metrics.get('dummy_rmse', 0):.3f}s"
        n_samples = metrics.get('n_samples', 0)
        
        html_content += f"""
        <div class="section">
            <h2>Model Performance (LapTime_s)</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Clean Laps Evaluated</div>
                    <div class="metric-value">{n_samples}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Random Forest R²</div>
                    <div class="metric-value">{rf_r2}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Random Forest RMSE</div>
                    <div class="metric-value">{rf_rmse}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Baseline (Mean) RMSE</div>
                    <div class="metric-value">{dummy_rmse}</div>
                </div>
            </div>
            
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">
                <em>5-fold cross-validation was used to estimate out-of-sample model performance across completed clean laps within the selected session. R² indicates the proportion of lap time variance explained strictly by the observed telemetry features (speed, throttle, brake, drs, tyre) and conditions during those laps.</em>
            </p>
        </div>
        
        <div class="section">
            <h2>Prediction Diagnostics</h2>
            <div class="chart-container">
                <img src="phase3_pred_vs_actual.png" alt="Prediction vs Actual">
            </div>
            <div class="chart-container">
                <img src="phase3_residuals.png" alt="Residual Distribution">
            </div>
        </div>
        
        <div class="section">
            <h2>Feature Importances</h2>
            <div class="chart-container">
                <img src="phase3_feature_importance.png" alt="Feature Importances">
            </div>
            <p style="color: var(--text-secondary);">
                <em>Random Forest impurity-based feature importance indicates the relative contribution of the feature to the model's predictive behavior. These represent how strongly each telemetry input corresponds to variations in the final lap time for this specific session, but do not imply causation.</em>
            </p>
        </div>
        """

    html_content += """
    </div>
</body>
</html>
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
