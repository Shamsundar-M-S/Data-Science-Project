import os
import json
from typing import Dict, Any

def generate_phase5_report(output_dir: str, session_id: str, metadata: Dict[str, Any]) -> str:
    """
    Generate the static Phase 5 HTML report for F1 Race Outcome Prediction.
    """
    report_path = os.path.join(output_dir, f"phase5_report_{session_id}.html")
    
    is_prediction_only = metadata.get("is_prediction_only", False)
    status_text = "PREDICTION-ONLY RACE" if is_prediction_only else "COMPLETED RACE"
    status_class = "status-prediction-only" if is_prediction_only else "status-completed"
    
    predictions = metadata.get("predictions", [])
    val_summary = metadata.get("validation_summary", {})
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1 Phase 5 — Race Outcome Predictive Analytics</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --accent: #ef4444;
            --accent-green: #22c55e;
            --accent-yellow: #eab308;
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
            margin-bottom: 2.5rem;
            border-bottom: 2px solid var(--border);
            padding-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        h1 {{
            font-size: 2.3rem;
            color: var(--text-primary);
            margin-bottom: 0.3rem;
        }}
        
        .session-id {{
            color: var(--accent);
            font-family: monospace;
            font-size: 1.1rem;
        }}
        
        .status-badge {{
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .status-completed {{
            background-color: rgba(34, 197, 94, 0.2);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
        }}
        
        .status-prediction-only {{
            background-color: rgba(234, 179, 8, 0.2);
            color: var(--accent-yellow);
            border: 1px solid var(--accent-yellow);
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
            font-size: 1.6rem;
            margin-bottom: 1.2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }}
        
        .timing-banner {{
            background: #1e1b4b;
            border-left: 4px solid #6366f1;
            padding: 1.25rem;
            border-radius: 6px;
            margin-bottom: 2rem;
        }}

        .timing-banner p {{
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .metric-card {{
            background: var(--bg-color);
            padding: 1.25rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent);
        }}

        .metric-subtext {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.2rem;
        }}
        
        .metric-label {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
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

        table.pred-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            font-size: 0.95rem;
        }}

        table.pred-table th, table.pred-table td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        table.pred-table th {{
            background-color: var(--bg-color);
            color: var(--text-secondary);
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
        }}

        table.pred-table tr:hover {{
            background-color: rgba(255, 255, 255, 0.03);
        }}

        .delta-pos {{ color: var(--accent-green); font-weight: bold; }}
        .delta-neg {{ color: var(--accent); font-weight: bold; }}
        .delta-zero {{ color: var(--text-secondary); }}

        .sci-warning {{
            background: #2a1b1b;
            border-left: 4px solid var(--accent);
            padding: 1.25rem;
            border-radius: 6px;
            margin-bottom: 2rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>F1 Phase 5 — Race Outcome Predictive Analytics</h1>
                <div class="session-id">{session_id}</div>
            </div>
            <div class="status-badge {status_class}">{status_text}</div>
        </header>

        <div class="timing-banner">
            <h3 style="color: #818cf8; margin-bottom: 0.2rem;">Prediction Time Horizon</h3>
            <p><strong>Strict Pre-Race Setting:</strong> Conceptual prediction is performed <em>after Qualifying</em> and <em>before the Sunday Race Start</em>. Only strictly pre-race telemetry and historical statistics are utilized. No post-race data, in-race weather, or future lap times are included.</p>
        </div>
"""

    if is_prediction_only:
        html_content += """
        <div class="sci-warning">
            <h3 style="color: var(--accent-yellow); margin-bottom: 0.4rem;">Actual Result: Not Available — Prediction Only</h3>
            <p>This session represents an upcoming or uncompleted race. Predicted finishing positions are generated using pre-race features. Actual race results and post-race evaluation metrics are not computed.</p>
        </div>
        """

    # Performance Metrics Section
    html_content += f"""
        <div class="section">
            <h2>Model Performance & Temporal Validation</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Model Race MAE</div>
                    <div class="metric-value">{val_summary.get('model_mae', 'N/A')}</div>
                    <div class="metric-subtext">Baseline Grid: {val_summary.get('grid_mae', 'N/A')} | Champ: {val_summary.get('champ_mae', 'N/A')}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Spearman Rank Corr</div>
                    <div class="metric-value">{val_summary.get('spearman_corr', 'N/A')}</div>
                    <div class="metric-subtext">Race-level rank correlation</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Podium Top-3 Overlap</div>
                    <div class="metric-value">{val_summary.get('top3_overlap_pct', 'N/A')}</div>
                    <div class="metric-subtext">Predicted vs Actual Top 3</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Validation Method</div>
                    <div class="metric-value" style="font-size:1.2rem; margin-top:0.3rem;">Expanding Window</div>
                    <div class="metric-subtext">{val_summary.get('val_races_count', 0)} temporal validation races</div>
                </div>
            </div>
        </div>
    """

    # Predicted Finishing Order Table
    html_content += """
        <div class="section">
            <h2>Predicted Finishing Order</h2>
            <table class="pred-table">
                <thead>
                    <tr>
                        <th>Pred Rank</th>
                        <th>Driver</th>
                        <th>Constructor</th>
                        <th>Grid Pos</th>
                        <th>Pred Pos Value</th>
                        <th>Actual Pos</th>
                        <th>Position Change</th>
                    </tr>
                </thead>
                <tbody>
    """

    for i, p in enumerate(predictions, start=1):
        driver = p.get("driver_id", "DRV")
        team = p.get("constructor_id", "Team")
        grid_p = p.get("grid_position", "N/A")
        pred_val = f"{p.get('predicted_pos_val', 0.0):.2f}"
        
        if is_prediction_only or pd_isna(p.get("actual_pos")):
            act_str = "Not Available — Prediction Only"
            delta_str = "N/A"
            delta_class = "delta-zero"
        else:
            act_p = int(p.get("actual_pos"))
            act_str = str(act_p)
            diff = grid_p - act_p if isinstance(grid_p, (int, float)) else 0
            if diff > 0:
                delta_str = f"+{diff}"
                delta_class = "delta-pos"
            elif diff < 0:
                delta_str = str(diff)
                delta_class = "delta-neg"
            else:
                delta_str = "0"
                delta_class = "delta-zero"

        html_content += f"""
                    <tr>
                        <td><strong>P{i}</strong></td>
                        <td><strong>{driver}</strong></td>
                        <td>{team}</td>
                        <td>{grid_p}</td>
                        <td>{pred_val}</td>
                        <td>{act_str}</td>
                        <td class="{delta_class}">{delta_str}</td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>
    """

    # Visualizations Section
    html_content += """
        <div class="section">
            <h2>Visualizations & Feature Importance</h2>
            <div class="chart-container">
                <img src="phase5_predicted_vs_actual.png" alt="Predicted vs Actual Finishing Order">
            </div>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">
                <em>Comparison of starting grid, model predictions, and actual finishing positions across the field.</em>
            </p>
            <div class="chart-container">
                <img src="phase5_feature_importance.png" alt="Permutation Feature Importance">
            </div>
            <p style="color: var(--text-secondary);">
                <em>Permutation feature importances evaluated on held-out temporal validation races. Indicates relative impact of pre-race predictors.</em>
            </p>
        </div>

        <div class="section">
            <h2>Methodology & Scientific Integrity</h2>
            <p style="color: var(--text-secondary); margin-bottom: 0.75rem;">
                <strong>Primary Model:</strong> <code>HistGradientBoostingRegressor</code> (max_iter=100, max_depth=5, min_samples_leaf=10, random_state=42).
            </p>
            <p style="color: var(--text-secondary); margin-bottom: 0.75rem;">
                <strong>Locked Features:</strong> Sunday Grid Position, Qualifying Delta %, Driver 5-Race Rolling Average Finish (strict shift), Team 5-Race Rolling Average Points (strict shift), Pre-Race Championship Position, Driver ID, Constructor ID, Circuit ID.
            </p>
            <p style="color: var(--text-secondary);">
                <strong>Leakage Controls:</strong> Strictly enforces chronological expanding window temporal validation. Target race results never enter feature vector construction. Unknown categories handled safely via integer categorical encoding.
            </p>
        </div>
    </div>
</body>
</html>
    """

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return report_path


def pd_isna(val) -> bool:
    if val is None:
        return True
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return True
    except Exception:
        pass
    return False
