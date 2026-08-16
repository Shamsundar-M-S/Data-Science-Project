import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.analysis.features import engineer_lap_features

def _is_kde_safe(df: pd.DataFrame, x_col: str, hue_col: str = None) -> bool:
    """
    Determine if KDE can be safely plotted for a given feature.
    Scipy's gaussian_kde requires variance > 0 for each hue group.
    """
    valid_data = df.dropna(subset=[x_col])
    if valid_data.empty:
        return False
        
    if hue_col and hue_col in df.columns:
        # Check variance for each hue group independently
        for _, group in valid_data.groupby(hue_col):
            if len(group) <= 1 or group[x_col].nunique() <= 1:
                return False
    else:
        if len(valid_data) <= 1 or valid_data[x_col].nunique() <= 1:
            return False
            
    return True

def plot_feature_vs_laptime(df_features: pd.DataFrame, feature_col: str, title: str, output_dir: str, filename: str):
    """Plot scatter of a feature against LapTime_s."""
    clean_laps = df_features[df_features["is_clean_lap"] == True].copy()
    subset = clean_laps.dropna(subset=[feature_col, "LapTime_s"])
    if subset.empty:
        return
        
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=subset, x=feature_col, y="LapTime_s", ax=ax, alpha=0.7, color="teal")
    sns.regplot(data=subset, x=feature_col, y="LapTime_s", scatter=False, ax=ax, color="darkgrey", line_kws={"linestyle": "--"})
    ax.set_title(title, fontsize=14)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches="tight")
    plt.close(fig)

def plot_feature_distributions(df_features: pd.DataFrame, feature_cols: list, title: str, output_dir: str, filename: str):
    """Plot distribution (histogram) of features."""
    clean_laps = df_features[df_features["is_clean_lap"] == True].copy()
    
    # Filter to cols that exist
    cols = [c for c in feature_cols if c in clean_laps.columns]
    if not cols:
        return
        
    fig, axes = plt.subplots(1, len(cols), figsize=(5*len(cols), 5))
    if len(cols) == 1:
        axes = [axes]
        
    for ax, col in zip(axes, cols):
        kde_safe = _is_kde_safe(clean_laps, col)
        sns.histplot(data=clean_laps, x=col, ax=ax, kde=kde_safe, color="royalblue")
        ax.set_title(f"Distribution of {col}")
        
    fig.suptitle(title, fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches="tight")
    plt.close(fig)

def run_phase2(session_id: str, data_dir: str, output_dir: str):
    """
    Execute Phase 2: Telemetry Feature Engineering.
    """
    print("Starting Phase 2: Telemetry Feature Engineering...")
    
    laps_file = os.path.join(data_dir, f"{session_id}_laps.parquet")
    tel_file = os.path.join(data_dir, f"{session_id}_telemetry.parquet")
    
    if not os.path.exists(laps_file) or not os.path.exists(tel_file):
        print("Data files not found. Ensure Phase 0 exports exist.")
        return
        
    df_laps = pd.read_parquet(laps_file)
    df_tel = pd.read_parquet(tel_file)
    
    # Session output dir
    session_output_dir = os.path.join(output_dir, session_id)
    os.makedirs(session_output_dir, exist_ok=True)
    
    # Extract metadata for the report
    session_metadata = {}
    if not df_laps.empty:
        session_metadata = {
            "season": str(df_laps["season"].iloc[0]) if "season" in df_laps else "Unknown",
            "event": str(df_laps["event"].iloc[0]) if "event" in df_laps else "Unknown",
            "session_type": str(df_laps["session_type"].iloc[0]) if "session_type" in df_laps else "Unknown"
        }
    
    print("1. Engineering per-lap features...")
    df_features = engineer_lap_features(df_laps, df_tel)
    
    # Extract base name from laps file for generic naming
    base_name = session_id
    
    print("2. Profiling features and saving dataset...")
    out_parquet = os.path.join(data_dir, f"{session_id}_features.parquet")
    df_features.to_parquet(out_parquet, index=False)
    
    # Save a CSV for easy missingness/quality checks
    quality_profile = df_features.describe().T
    quality_profile["Valid_Count"] = df_features.count()
    quality_profile = quality_profile.reset_index().rename(columns={"index": "Feature"})
    quality_profile.to_csv(os.path.join(session_output_dir, "feature_quality.csv"), index=False)
    
    # 3. Generate initial visual profiles (distributions and pair correlation)
    print("3. Generating Visualizations...")
    for feat in ["speed_mean", "throttle_full_pct", "brake_active_pct", "drs_active_pct", "gear_mean", "LapTime_s"]:
        if feat in df_features.columns:
            plt.figure(figsize=(8, 5))
            kde_safe = _is_kde_safe(df_features, feat, "is_clean_lap")
            sns.histplot(data=df_features, x=feat, hue="is_clean_lap", kde=kde_safe, bins=30)
            plt.title(f"Distribution of {feat}")
            plt.tight_layout()
            plt.savefig(os.path.join(session_output_dir, f"dist_{feat}.png"), bbox_inches="tight")
            plt.close()
            
            # Scatter vs LapTime
            if feat != "LapTime_s":
                plt.figure(figsize=(8, 5))
                sns.scatterplot(data=df_features[df_features["is_clean_lap"] == True], x=feat, y="LapTime_s", hue="Compound", alpha=0.7)
                plt.title(f"{feat} vs LapTime_s (Clean Laps)")
                plt.tight_layout()
                plt.savefig(os.path.join(session_output_dir, f"scatter_{feat}_vs_laptime.png"), bbox_inches="tight")
                plt.close()
                
    # Correlation heatmap for numerical features
    numeric_feats = df_features.select_dtypes(include=[np.number])
    if not numeric_feats.empty:
        plt.figure(figsize=(12, 10))
        corr = numeric_feats.corr(method="pearson")
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", center=0, vmin=-1, vmax=1)
        plt.title("Pearson Correlation of Extracted Features")
        plt.tight_layout()
        plt.savefig(os.path.join(session_output_dir, "feature_correlation.png"), bbox_inches="tight")
        plt.close()
        
    print("4. Generating Phase 2 Report...")
    from src.analysis.report_phase2 import generate_phase2_report
    generate_phase2_report(session_output_dir, session_metadata, session_id)
    print("Phase 2 complete.")

if __name__ == "__main__":
    SESSION = "2023_01_Bahrain_Grand_Prix_Practice_1"
    DATA_DIR = "analytics_data"
    OUTPUT_DIR = "analytics_output"
    
    run_phase2(SESSION, DATA_DIR, OUTPUT_DIR)
