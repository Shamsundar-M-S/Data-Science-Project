import os
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.analysis.plot_style import setup_plot_style, save_plot, get_compound_palette


def generate_data_quality_profile(df_laps: pd.DataFrame, df_tel: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Generate a data quality profile detailing missingness, unique counts, and basic stats.
    """
    profiles = {}
    
    for name, df in [("laps", df_laps), ("telemetry", df_tel)]:
        if df.empty:
            continue
            
        summary = pd.DataFrame({
            "Missing_Count": df.isna().sum(),
            "Missing_Pct": (df.isna().sum() / len(df)) * 100,
            "Unique_Count": df.nunique(),
            "Dtype": df.dtypes
        })
        
        # Add numeric summaries where applicable
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        stats = df[numeric_cols].agg(["min", "max", "mean", "median", "std"]).T
        
        summary = summary.join(stats)
        profiles[name] = summary
        
    return profiles


def generate_descriptive_summaries(df_laps: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate descriptive statistics for drivers and compounds based on clean laps.
    """
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    
    if clean_laps.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    # Driver Summary
    driver_stats = clean_laps.groupby("Driver").agg(
        Clean_Laps=("LapNumber", "count"),
        Min_LapTime_s=("LapTime_s", "min"),
        Median_LapTime_s=("LapTime_s", "median"),
        Mean_LapTime_s=("LapTime_s", "mean"),
        Std_LapTime_s=("LapTime_s", "std")
    ).reset_index()
    
    # Sort by median lap time
    driver_stats = driver_stats.sort_values("Median_LapTime_s")
    
    # Compound Summary
    compound_stats = clean_laps.groupby("Compound").agg(
        Clean_Laps=("LapNumber", "count"),
        Min_LapTime_s=("LapTime_s", "min"),
        Median_LapTime_s=("LapTime_s", "median"),
        Mean_LapTime_s=("LapTime_s", "mean"),
        Std_LapTime_s=("LapTime_s", "std")
    ).reset_index()
    
    compound_stats = compound_stats.sort_values("Median_LapTime_s")
    
    return driver_stats, compound_stats





def plot_lap_time_distribution(df_laps: pd.DataFrame, output_dir: str):
    """Plot the distribution of lap times for clean laps."""
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    if clean_laps.empty or "LapTime_s" not in clean_laps.columns:
        return
        
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.histplot(data=clean_laps, x="LapTime_s", kde=True, ax=ax, color="steelblue")
    
    ax.set_title("Clean Lap Time Distribution", fontsize=14)
    ax.set_xlabel("Lap Time (Seconds)")
    ax.set_ylabel("Frequency")
    
    # Add textual notes about multimodality or skew
    ax.text(0.95, 0.95, f"n = {len(clean_laps)} clean laps", 
            transform=ax.transAxes, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
            
    save_plot(fig, output_dir, "eda_lap_time_distribution.png")


def plot_driver_performance(df_laps: pd.DataFrame, output_dir: str):
    """Box plot of lap times per driver, sorted by median."""
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    if clean_laps.empty or "LapTime_s" not in clean_laps.columns:
        return
        
    # Order drivers by median lap time
    medians = clean_laps.groupby("Driver")["LapTime_s"].median().sort_values()
    
    fig, ax = plt.subplots(figsize=(16, 8))
    sns.boxplot(data=clean_laps, x="Driver", y="LapTime_s", order=medians.index, ax=ax, palette="viridis")
    
    ax.set_title("Clean Lap Performance by Driver", fontsize=14)
    ax.set_xlabel("Driver")
    ax.set_ylabel("Lap Time (Seconds)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    
    save_plot(fig, output_dir, "eda_driver_performance.png")


def plot_compound_performance(df_laps: pd.DataFrame, output_dir: str):
    """Box plot of lap times by tyre compound."""
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    clean_laps = clean_laps.dropna(subset=["Compound"])
    if clean_laps.empty or "LapTime_s" not in clean_laps.columns:
        return
        
    # Order by median
    medians = clean_laps.groupby("Compound")["LapTime_s"].median().sort_values()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.boxplot(data=clean_laps, x="Compound", y="LapTime_s", order=medians.index, ax=ax, palette=get_compound_palette(clean_laps["Compound"].unique()))
    
    ax.set_title("Clean Lap Performance by Tyre Compound", fontsize=14)
    ax.set_xlabel("Tyre Compound")
    ax.set_ylabel("Lap Time (Seconds)")
    
    save_plot(fig, output_dir, "eda_compound_performance.png")


def plot_tyre_age_vs_lap_time(df_laps: pd.DataFrame, output_dir: str):
    """Scatter plot of Tyre Age vs Lap Time with trendlines per compound."""
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    clean_laps = clean_laps.dropna(subset=["Compound"])
    
    if clean_laps.empty or "LapTime_s" not in clean_laps.columns or "TyreLife" not in clean_laps.columns:
        return
        
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # lmplot creates its own figure, so use regplot in a loop or scatterplot
    sns.scatterplot(data=clean_laps, x="TyreLife", y="LapTime_s", hue="Compound", style="Compound", alpha=0.7, ax=ax, palette=get_compound_palette(clean_laps["Compound"].unique()))
    
    # Add simple trendlines
    for comp in clean_laps["Compound"].unique():
        sub = clean_laps[clean_laps["Compound"] == comp].dropna(subset=["TyreLife", "LapTime_s"])
        if len(sub) > 2:
            sns.regplot(data=sub, x="TyreLife", y="LapTime_s", scatter=False, ax=ax, label=f"{comp} Trend")
            
    ax.set_title("Tyre Age vs Clean Lap Time", fontsize=14)
    ax.set_xlabel("Tyre Age (Laps)")
    ax.set_ylabel("Lap Time (Seconds)")
    
    # Move legend out
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
             
    save_plot(fig, output_dir, "eda_tyre_age_degradation.png")


def plot_data_quality(df_laps: pd.DataFrame, output_dir: str):
    """Plot data quality overview: clean vs excluded laps."""
    if df_laps.empty or "is_clean_lap" not in df_laps.columns:
        return
        
    fig, ax = plt.subplots(figsize=(8, 8))
    counts = df_laps["is_clean_lap"].value_counts()
    
    # Ensure True/False keys exist for mapping
    labels = []
    sizes = []
    colors = []
    if True in counts.index:
        labels.append(f"Clean Laps ({counts[True]})")
        sizes.append(counts[True])
        colors.append("mediumseagreen")
    if False in counts.index:
        labels.append(f"Excluded Laps ({counts[False]})")
        sizes.append(counts[False])
        colors.append("tomato")
        
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'white'})
    ax.set_title("Dataset Lap Composition", fontsize=14)
    
    save_plot(fig, output_dir, "eda_data_quality.png")


def plot_track_temp_vs_lap_time(df_laps: pd.DataFrame, output_dir: str):
    """Scatter plot of Track Temperature vs Lap Time."""
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    
    if clean_laps.empty or "TrackTemp" not in clean_laps.columns or "LapTime_s" not in clean_laps.columns:
        return
        
    subset = clean_laps.dropna(subset=["TrackTemp", "LapTime_s"])
    if subset.empty:
        return
        
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.scatterplot(data=subset, x="TrackTemp", y="LapTime_s", ax=ax, color="darkorange", alpha=0.7)
    sns.regplot(data=subset, x="TrackTemp", y="LapTime_s", scatter=False, ax=ax, color="dimgrey", line_kws={"linestyle": "--"})
    
    ax.set_title("Track Temperature vs Clean Lap Time", fontsize=14)
    ax.set_xlabel("Track Temperature (°C)")
    ax.set_ylabel("Lap Time (Seconds)")
             
    save_plot(fig, output_dir, "eda_track_temp_lap_time.png")


def plot_correlation_heatmap(df_laps: pd.DataFrame, output_dir: str):
    """Plot pairwise Pearson correlation heatmap for numeric columns."""
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    
    variables = ["LapTime_s", "TyreLife", "TrackTemp", "AirTemp", "SpeedST", "SpeedFL"]
    existing_vars = [v for v in variables if v in clean_laps.columns]
    
    if len(existing_vars) < 2:
        return
        
    corr = clean_laps[existing_vars].corr(method="pearson")
    
    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, fmt=".2f", 
                square=True, linewidths=.5, cbar_kws={"shrink": .8}, ax=ax, annot_kws={"size": 12})
                
    ax.set_title("Pairwise Pearson Correlation Matrix", fontsize=16)
             
    # Ensure tick labels are rotated properly to avoid clipping
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=12)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=12)
    
    save_plot(fig, output_dir, "eda_correlation_heatmap.png")

