import os
import json
import pandas as pd

from src.analysis.eda import (
    generate_data_quality_profile,
    generate_descriptive_summaries,
    plot_lap_time_distribution,
    plot_driver_performance,
    plot_compound_performance,
    plot_tyre_age_vs_lap_time,
    plot_data_quality,
    plot_track_temp_vs_lap_time,
    plot_correlation_heatmap
)
from src.analysis.statistics import (
    calculate_correlations,
    analyze_weather_impact,
    compare_group_differences
)
from src.analysis.report import generate_html_report

def run_phase1_analysis(session_id: str, data_dir: str, output_dir: str):
    """
    Execute the Phase 1 EDA and Statistical analysis pipeline.
    """
    laps_file = os.path.join(data_dir, f"{session_id}_laps.parquet")
    tel_file = os.path.join(data_dir, f"{session_id}_telemetry.parquet")
    
    print(f"Starting Phase 1 Analysis for {session_id}...")
    print(f"Loading data from {laps_file} and {tel_file}...")
    
    if not os.path.exists(laps_file) or not os.path.exists(tel_file):
        print("Data files not found. Ensure Phase 0 exports exist.")
        return
        
    df_laps = pd.read_parquet(laps_file)
    df_tel = pd.read_parquet(tel_file)
    
    # Extract metadata for the report
    session_metadata = {}
    if not df_laps.empty:
        session_metadata = {
            "season": str(df_laps["season"].iloc[0]) if "season" in df_laps else "Unknown",
            "event": str(df_laps["event"].iloc[0]) if "event" in df_laps else "Unknown",
            "session_type": str(df_laps["session_type"].iloc[0]) if "session_type" in df_laps else "Unknown"
        }
        
    # Isolate outputs into a session-specific folder within output_dir
    session_output_dir = os.path.join(output_dir, session_id)
    os.makedirs(session_output_dir, exist_ok=True)
    
    # 1. Data Quality
    print("1. Generating Data Quality Profiles...")
    profiles = generate_data_quality_profile(df_laps, df_tel)
    for name, prof in profiles.items():
        # Clean up types before saving to CSV
        prof_copy = prof.copy()
        prof_copy["Dtype"] = prof_copy["Dtype"].astype(str)
        prof_copy.to_csv(os.path.join(session_output_dir, f"data_quality_{name}.csv"))
        
    # 2. Descriptive Summaries
    print("2. Generating Descriptive Summaries...")
    driver_stats, compound_stats = generate_descriptive_summaries(df_laps)
    driver_stats.to_csv(os.path.join(session_output_dir, "summary_drivers.csv"), index=False)
    compound_stats.to_csv(os.path.join(session_output_dir, "summary_compounds.csv"), index=False)
    
    # 3. EDA Plots
    print("3. Generating EDA Visualizations...")
    plot_lap_time_distribution(df_laps, session_output_dir)
    plot_driver_performance(df_laps, session_output_dir)
    plot_compound_performance(df_laps, session_output_dir)
    plot_tyre_age_vs_lap_time(df_laps, session_output_dir)
    plot_data_quality(df_laps, session_output_dir)
    plot_track_temp_vs_lap_time(df_laps, session_output_dir)
    plot_correlation_heatmap(df_laps, session_output_dir)
    
    # 4. Statistical Analysis
    print("4. Calculating Statistics...")
    correlations = calculate_correlations(df_laps)
    if not correlations["pearson"].empty:
        correlations["pearson"].to_csv(os.path.join(session_output_dir, "correlation_pearson.csv"))
        correlations["spearman"].to_csv(os.path.join(session_output_dir, "correlation_spearman.csv"))
        
    weather = analyze_weather_impact(df_laps)
    driver_diff = compare_group_differences(df_laps, "Driver")
    compound_diff = compare_group_differences(df_laps, "Compound")
    
    # Save statistical findings
    stats_findings = {
        "weather_impact": weather,
        "driver_differences": driver_diff,
        "compound_differences": compound_diff
    }
    
    with open(os.path.join(session_output_dir, "statistical_findings.json"), "w") as f:
        json.dump(stats_findings, f, indent=4)
        
    print("5. Generating Visual HTML Report...")
    generate_html_report(session_output_dir, session_metadata, session_id)
        
    print(f"Phase 1 Analysis complete. Results saved to {session_output_dir}")


if __name__ == "__main__":
    SESSION = "2023_01_Bahrain_Grand_Prix_Practice_1"
    DATA_DIR = "analytics_data"
    OUTPUT_DIR = "analytics_output"
    
    run_phase1_analysis(SESSION, DATA_DIR, OUTPUT_DIR)
