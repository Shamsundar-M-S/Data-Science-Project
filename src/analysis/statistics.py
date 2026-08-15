import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple


def calculate_correlations(df_laps: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Calculate Pearson and Spearman correlations for meaningful F1 variables.
    Returns a dictionary with 'pearson' and 'spearman' DataFrames.
    """
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    
    # Meaningful variables to correlate
    # Do not blindly correlate every numeric column
    variables = ["LapTime_s", "TyreLife", "TrackTemp", "AirTemp", "SpeedST"]
    
    # Filter only existing columns
    existing_vars = [v for v in variables if v in clean_laps.columns]
    
    if len(existing_vars) < 2 or clean_laps.empty:
        return {"pearson": pd.DataFrame(), "spearman": pd.DataFrame()}
        
    df_subset = clean_laps[existing_vars].dropna()
    
    if df_subset.empty:
        return {"pearson": pd.DataFrame(), "spearman": pd.DataFrame()}
        
    pearson_corr = df_subset.corr(method="pearson")
    spearman_corr = df_subset.corr(method="spearman")
    
    return {"pearson": pearson_corr, "spearman": spearman_corr}


def analyze_weather_impact(df_laps: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze the association between track temperature and lap performance.
    """
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    
    if clean_laps.empty or "TrackTemp" not in clean_laps.columns or "LapTime_s" not in clean_laps.columns:
        return {"status": "insufficient_data"}
        
    subset = clean_laps[["TrackTemp", "LapTime_s"]].dropna()
    
    if len(subset) < 10:
        return {"status": "insufficient_data"}
        
    # Check variation
    temp_std = subset["TrackTemp"].std()
    
    # If standard deviation is less than 0.5 degrees, we lack variation for inference
    if temp_std < 0.5:
        return {
            "status": "insufficient_variation",
            "message": "Insufficient variation in track temperature to support a strong inference.",
            "std": temp_std
        }
        
    # Calculate Spearman correlation since relationship may be non-linear
    spearman_r, p_value = stats.spearmanr(subset["TrackTemp"], subset["LapTime_s"])
    
    return {
        "status": "success",
        "spearman_r": spearman_r,
        "p_value": p_value,
        "n_samples": len(subset),
        "limitations": "May be confounded by tyre compound, track evolution, and driver/stint composition."
    }


def compare_group_differences(df_laps: pd.DataFrame, group_col: str, target_col: str = "LapTime_s") -> Dict[str, Any]:
    """
    Compare group differences using the Kruskal-Wallis non-parametric test.
    Useful for comparing Driver or Compound lap times.
    """
    clean_laps = df_laps[df_laps["is_clean_lap"] == True].copy()
    
    if clean_laps.empty or group_col not in clean_laps.columns or target_col not in clean_laps.columns:
        return {"status": "insufficient_data"}
        
    # Drop NAs
    subset = clean_laps[[group_col, target_col]].dropna()
    
    # Filter groups with fewer than 3 samples
    group_counts = subset[group_col].value_counts()
    valid_groups = group_counts[group_counts >= 3].index
    
    subset = subset[subset[group_col].isin(valid_groups)]
    
    if len(valid_groups) < 2:
        return {"status": "insufficient_groups"}
        
    groups = [subset[subset[group_col] == g][target_col].values for g in valid_groups]
    
    stat, p_value = stats.kruskal(*groups)
    
    # Calculate effect size (epsilon-squared)
    n = len(subset)
    k = len(valid_groups)
    epsilon_sq = stat / ((n**2 - 1) / (n + 1)) if n > 1 else 0
    
    # Calculate medians for effect difference
    medians = subset.groupby(group_col)[target_col].median()
    
    return {
        "status": "success",
        "test": "Kruskal-Wallis H-test",
        "statistic": stat,
        "p_value": p_value,
        "epsilon_squared": epsilon_sq,
        "n_samples": n,
        "groups_compared": len(valid_groups),
        "medians": medians.to_dict()
    }
