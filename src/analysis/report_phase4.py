import os
import json

def generate_phase4_report(output_dir: str, session_id: str, metadata: dict):
    """Generate the static Phase 4 HTML report."""
    report_path = os.path.join(output_dir, f"phase4_report_{session_id}.html")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F1 Phase 4 - Advanced Performance & Strategy Analysis</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --accent: #ef4444;
            --accent-hover: #dc2626;
            --border: #334155;
            --chart-bg: #1e293b;
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
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
        
        .warning-state {{
            background: #422006;
            border-left: 4px solid #f59e0b;
            padding: 1.5rem;
            border-radius: 4px;
            margin-bottom: 2rem;
        }}
        
        .sci-warning {{
            background: #2a1b1b;
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
            <h1>F1 Phase 4 - Advanced Performance & Strategy</h1>
            <div class="session-id">{session_id} ({metadata.get('session_type', 'Unknown')})</div>
        </header>

        <div class="sci-warning">
            <h2 style="color: var(--accent); margin-bottom: 0.5rem; font-size: 1.4rem; border:none;">Scientific Interpretation Warning</h2>
            <p><strong>This analysis explores observed lap-time evolution across tyre life, stints, compounds, and session progression.</strong></p>
            <p style="margin-top: 0.5rem; color: var(--text-secondary);">It is an observational Data Science analysis. Observed associations (e.g., pace dropping over tyre life) do not establish pure causal degradation, as factors like fuel load burn-off, track evolution, and driver run plans heavily confound the results. Do not automatically interpret these trends as pure tyre degradation.</p>
        </div>
        
        <div class="section">
            <h2>Session Overview</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Laps</div>
                    <div class="metric-value">{metadata.get('total_laps', 0)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Clean Laps</div>
                    <div class="metric-value">{metadata.get('clean_laps', 0)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Compounds Used</div>
                    <div class="metric-value">{len(metadata.get('compounds', []))}</div>
                </div>
            </div>
        </div>
"""

    if metadata.get('has_timeline'):
        html_content += """
        <div class="section">
            <h2>Strategy Timeline</h2>
            <div class="chart-container">
                <img src="phase4_strategy_timeline.png" alt="Strategy Timeline">
            </div>
            <p style="color: var(--text-secondary);">
                <em>Displays compound usage over the race. Pit stops correspond to compound transitions. Note: Strategy timeline is generated specifically for Race sessions.</em>
            </p>
        </div>
        """
    else:
        html_content += """
        <div class="section">
            <h2>Strategy Timeline</h2>
            <div class="warning-state">
                <p>Strategy timeline is not applicable or insufficiently supported for this session type (e.g., Practice/Qualifying).</p>
            </div>
        </div>
        """

    if metadata.get('has_stints') and metadata.get('has_pace'):
        html_content += """
        <div class="section">
            <h2>Stint & Pace Analysis</h2>
            <div class="chart-container">
                <img src="phase4_stint_pace.png" alt="Stint Pace Evolution">
            </div>
            <p style="color: var(--text-secondary);">
                <em>Observed stint pace evolution for top drivers. Note how lap times fluctuate based on compound choice and tyre life.</em>
            </p>
            <div class="chart-container" style="margin-top:2rem;">
                <img src="phase4_driver_pace.png" alt="Driver Pace Evolution">
            </div>
            <p style="color: var(--text-secondary);">
                <em>Session-wide pace evolution compared against the field median. Outliers represent traffic, mistakes, or varying fuel loads.</em>
            </p>
        </div>
        """
    else:
        html_content += """
        <div class="section">
            <h2>Stint & Pace Analysis</h2>
            <div class="warning-state">
                <p>Insufficient clean lap data to generate meaningful stint and pace analysis.</p>
            </div>
        </div>
        """

    if metadata.get('has_degradation'):
        html_content += """
        <div class="section">
            <h2>Tyre Degradation Analysis</h2>
            <div class="chart-container">
                <img src="phase4_tyre_degradation.png" alt="Tyre Degradation">
            </div>
            <p style="color: var(--text-secondary);">
                <em>Estimated observed degradation per stint (seconds per additional tyre-life lap) plotted against the starting tyre life of the stint. Note: Negative values might appear due to fuel-burn out-pacing tyre wear, or track evolution.</em>
            </p>
        </div>
        """
    else:
        html_content += """
        <div class="section">
            <h2>Tyre Degradation Analysis</h2>
            <div class="warning-state">
                <p>Tyre degradation estimate unavailable: fewer than 3 valid tyre-life observations per group were available, or zero variance encountered.</p>
            </div>
        </div>
        """

    html_content += """
        <div class="section">
            <h2>Compound Performance</h2>
            <div class="chart-container">
                <img src="phase4_compound_performance.png" alt="Compound Performance">
            </div>
            <p style="color: var(--text-secondary);">
                <em>Distribution of clean lap times by compound. Unlike Phase 1, this contextually builds upon stint data, although direct comparisons remain confounded by fuel loads.</em>
            </p>
        </div>
    </div>
</body>
</html>
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
