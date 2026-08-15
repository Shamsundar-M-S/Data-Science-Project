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

def run_phase1_analysis(laps_file: str, tel_file: str, output_dir: str):
    """
    Execute the Phase 1 EDA and Statistical analysis pipeline.
    """
    print(f"Starting Phase 1 Analysis...")
    print(f"Loading data from {laps_file} and {tel_file}...")
    
    if not os.path.exists(laps_file) or not os.path.exists(tel_file):
        print("Data files not found. Ensure Phase 0 exports exist.")
        return
        
    df_laps = pd.read_parquet(laps_file)
    df_tel = pd.read_parquet(tel_file)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Data Quality
    print("1. Generating Data Quality Profiles...")
    profiles = generate_data_quality_profile(df_laps, df_tel)
    for name, prof in profiles.items():
        # Clean up types before saving to CSV
        prof_copy = prof.copy()
        prof_copy["Dtype"] = prof_copy["Dtype"].astype(str)
        prof_copy.to_csv(os.path.join(output_dir, f"data_quality_{name}.csv"))
        
    # 2. Descriptive Summaries
    print("2. Generating Descriptive Summaries...")
    driver_stats, compound_stats = generate_descriptive_summaries(df_laps)
    driver_stats.to_csv(os.path.join(output_dir, "summary_drivers.csv"), index=False)
    compound_stats.to_csv(os.path.join(output_dir, "summary_compounds.csv"), index=False)
    
    # 3. EDA Plots
    print("3. Generating EDA Visualizations...")
    plot_lap_time_distribution(df_laps, output_dir)
    plot_driver_performance(df_laps, output_dir)
    plot_compound_performance(df_laps, output_dir)
    plot_tyre_age_vs_lap_time(df_laps, output_dir)
    plot_data_quality(df_laps, output_dir)
    plot_track_temp_vs_lap_time(df_laps, output_dir)
    plot_correlation_heatmap(df_laps, output_dir)
    
    # 4. Statistical Analysis
    print("4. Calculating Statistics...")
    correlations = calculate_correlations(df_laps)
    if not correlations["pearson"].empty:
        correlations["pearson"].to_csv(os.path.join(output_dir, "correlation_pearson.csv"))
        correlations["spearman"].to_csv(os.path.join(output_dir, "correlation_spearman.csv"))
        
    weather = analyze_weather_impact(df_laps)
    driver_diff = compare_group_differences(df_laps, "Driver")
    compound_diff = compare_group_differences(df_laps, "Compound")
    
    # Save statistical findings
    stats_findings = {
        "weather_impact": weather,
        "driver_differences": driver_diff,
        "compound_differences": compound_diff
    }
    
    with open(os.path.join(output_dir, "statistical_findings.json"), "w") as f:
        json.dump(stats_findings, f, indent=4)
        
    print("5. Generating Visual HTML Report...")
    generate_html_report(output_dir)
        
    print(f"Phase 1 Analysis complete. Results saved to {output_dir}")


if __name__ == "__main__":
    LAPS_PATH = "analytics_data/2023_01_Bahrain_Grand_Prix_Practice_1_laps.parquet"
    TEL_PATH = "analytics_data/2023_01_Bahrain_Grand_Prix_Practice_1_telemetry.parquet"
    OUTPUT_DIR = "analytics_output"
    
    run_phase1_analysis(LAPS_PATH, TEL_PATH, OUTPUT_DIR)
