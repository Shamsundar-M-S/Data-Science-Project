import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.analysis.strategy import (
    analyze_tyre_degradation,
    analyze_stints,
    analyze_driver_pace,
    analyze_strategy_timeline
)
from src.analysis.plot_style import setup_plot_style, save_plot, get_compound_palette
from src.analysis.report_phase4 import generate_phase4_report


def run_phase4(session_id: str, data_dir: str = "analytics_data", output_dir: str = "analytics_output"):
    """
    Phase 4: Advanced Performance & Strategy Analysis
    """
    laps_path = os.path.join(data_dir, f"{session_id}_laps.parquet")
    session_out_dir = os.path.join(output_dir, session_id)
    os.makedirs(session_out_dir, exist_ok=True)
    
    if not os.path.exists(laps_path):
        print(f"Laps file {laps_path} not found. Skipping Phase 4.")
        return
        
    df_laps = pd.read_parquet(laps_path)
    
    # Run analytical modules
    df_deg = analyze_tyre_degradation(df_laps)
    df_stints = analyze_stints(df_laps)
    df_pace = analyze_driver_pace(df_laps)
    df_timeline = analyze_strategy_timeline(df_laps)
    
    session_type = df_laps['session_type'].iloc[0] if not df_laps.empty and 'session_type' in df_laps.columns else 'Unknown'
    
    metadata = {
        'status': 'success',
        'session_type': session_type,
        'has_degradation': not df_deg.empty,
        'has_stints': not df_stints.empty,
        'has_pace': not df_pace.empty,
        'has_timeline': not df_timeline.empty and 'Race' in session_type,
        'total_laps': len(df_laps),
        'clean_laps': df_laps['is_clean_lap'].sum() if 'is_clean_lap' in df_laps.columns else 0,
        'compounds': df_laps['Compound'].dropna().unique().tolist() if 'Compound' in df_laps.columns else []
    }
    
    # Generate Visualizations
    setup_plot_style()
    _plot_tyre_degradation(df_deg, session_out_dir)
    _plot_stint_pace(df_stints, df_pace, session_out_dir)
    _plot_driver_pace(df_pace, session_out_dir)
    _plot_compound_performance(df_pace, session_out_dir)
    _plot_strategy_timeline(df_timeline, session_out_dir, session_type)
    
    # Generate HTML
    generate_phase4_report(session_out_dir, session_id, metadata)
    print(f"Phase 4 complete. Results saved to {session_out_dir}")


def _plot_tyre_degradation(df_deg: pd.DataFrame, out_dir: str):
    fig_path = os.path.join(out_dir, "phase4_tyre_degradation.png")
    if df_deg.empty:
        return
        
    fig = plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_deg, x='tyre_life_start', y='degradation_s_per_lap', hue='Compound', palette=get_compound_palette(df_deg['Compound'].unique()), s=100)
    plt.axhline(0, color='gray', linestyle='--')
    plt.title("Estimated Tyre Degradation per Stint")
    plt.xlabel("Stint Start Tyre Life")
    plt.ylabel("Observed Degradation (seconds per lap)")
    save_plot(fig, out_dir, "phase4_tyre_degradation.png")

def _plot_stint_pace(df_stints: pd.DataFrame, df_pace: pd.DataFrame, out_dir: str):
    fig_path = os.path.join(out_dir, "phase4_stint_pace.png")
    if df_pace.empty or df_stints.empty:
        return
        
    fig = plt.figure(figsize=(10, 6))
    
    # To avoid spaghetti, we just plot top 5 drivers by clean laps
    top_drivers = df_pace['Driver'].value_counts().nlargest(5).index
    df_sub = df_pace[df_pace['Driver'].isin(top_drivers)]
    
    sns.lineplot(data=df_sub, x='TyreLife', y='LapTime_s', hue='Compound', style='Driver', palette=get_compound_palette(df_sub['Compound'].unique()), markers=True, dashes=False)
    plt.title("Stint Pace Evolution (Top 5 Drivers)")
    plt.xlabel("Tyre Life")
    plt.ylabel("Lap Time (s)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    save_plot(fig, out_dir, "phase4_stint_pace.png")

def _plot_driver_pace(df_pace: pd.DataFrame, out_dir: str):
    fig_path = os.path.join(out_dir, "phase4_driver_pace.png")
    if df_pace.empty:
        return
        
    fig = plt.figure(figsize=(12, 6))
    # Rolling median pace to reduce clutter
    df_roll = df_pace.groupby(['LapNumber'])['LapTime_s'].median().reset_index()
    sns.lineplot(data=df_roll, x='LapNumber', y='LapTime_s', color='white', label='Field Median')
    sns.scatterplot(data=df_pace, x='LapNumber', y='LapTime_s', hue='Compound', palette=get_compound_palette(df_pace['Compound'].unique()), alpha=0.5, s=20)
    plt.title("Session Pace Evolution")
    plt.xlabel("Lap Number")
    plt.ylabel("Lap Time (s)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    save_plot(fig, out_dir, "phase4_driver_pace.png")

def _plot_compound_performance(df_pace: pd.DataFrame, out_dir: str):
    fig_path = os.path.join(out_dir, "phase4_compound_performance.png")
    if df_pace.empty:
        return
        
    fig = plt.figure(figsize=(8, 6))
    sns.violinplot(data=df_pace, x='Compound', y='LapTime_s', palette=get_compound_palette(df_pace['Compound'].unique()), inner="quartile")
    plt.title("Clean Lap Time Distribution by Compound")
    plt.xlabel("Compound")
    plt.ylabel("Lap Time (s)")
    save_plot(fig, out_dir, "phase4_compound_performance.png")

def _plot_strategy_timeline(df_timeline: pd.DataFrame, out_dir: str, session_type: str):
    fig_path = os.path.join(out_dir, "phase4_strategy_timeline.png")
    if df_timeline.empty or 'Race' not in session_type:
        return
        
    fig = plt.figure(figsize=(12, 8))
    drivers = df_timeline['Driver'].unique()
    
    # Get palette for all compounds in the timeline
    palette = get_compound_palette(df_timeline['Compound'].unique())
    
    for i, driver in enumerate(drivers):
        driver_stints = df_timeline[df_timeline['Driver'] == driver]
        for _, row in driver_stints.iterrows():
            compound = row['Compound']
            color = palette.get(compound, '#9ca3af')
            plt.barh(i, row['end_lap'] - row['start_lap'] + 1, left=row['start_lap'], color=color, edgecolor='black', height=0.6)
            
    plt.yticks(range(len(drivers)), drivers)
    plt.title("Race Strategy Timeline")
    plt.xlabel("Lap Number")
    plt.ylabel("Driver")
    save_plot(fig, out_dir, "phase4_strategy_timeline.png")
