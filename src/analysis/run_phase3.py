import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold, cross_val_score, cross_val_predict
from sklearn.metrics import root_mean_squared_error, r2_score

from src.analysis.plot_style import setup_plot_style, save_plot
from src.analysis.report_phase3 import generate_phase3_report

def run_phase3(session_id: str, data_dir: str = "analytics_data", output_dir: str = "analytics_output"):
    """
    Phase 3: Advanced Data Science / Modeling
    Target: LapTime_s
    Features: speed_mean, throttle_full_pct, brake_active_pct, drs_active_pct, TyreLife, Compound
    """
    features_path = os.path.join(data_dir, f"{session_id}_features.parquet")
    session_out_dir = os.path.join(output_dir, session_id)
    os.makedirs(session_out_dir, exist_ok=True)
    
    if not os.path.exists(features_path):
        print(f"Features file {features_path} not found. Skipping Phase 3.")
        return
        
    df = pd.read_parquet(features_path)
    
    # Filter for clean laps only
    if 'is_clean_lap' in df.columns:
        df = df[df['is_clean_lap'] == True].copy()
        
    feature_cols = ['speed_mean', 'throttle_full_pct', 'brake_active_pct', 'drs_active_pct', 'TyreLife']
    target_col = 'LapTime_s'
    
    required_cols = feature_cols + [target_col, 'Compound']
    
    # Check if required columns exist
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"Missing required columns for Phase 3: {missing_cols}")
        return
        
    # Drop rows with NaN in required columns
    df = df.dropna(subset=required_cols).copy()
    
    n_samples = len(df)
    
    metrics = {
        'n_samples': n_samples,
        'rf_r2': None,
        'rf_rmse': None,
        'dummy_r2': None,
        'dummy_rmse': None,
        'feature_importances': {},
        'status': 'success'
    }
    
    if n_samples < 10:
        print(f"Phase 3: Insufficient clean lap samples ({n_samples}). Skipping ML modeling.")
        metrics['status'] = 'insufficient_data'
        generate_phase3_report(session_out_dir, session_id, metrics)
        return
        
    # Prepare features
    X_num = df[feature_cols]
    
    # One-hot encode Compound
    compounds = pd.get_dummies(df['Compound'], prefix='Compound', drop_first=True)
    X = pd.concat([X_num, compounds], axis=1)
    y = df[target_col]
    
    # Validation strategy
    n_splits = min(5, n_samples)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # Baseline model
    dummy_model = DummyRegressor(strategy='mean')
    dummy_preds = cross_val_predict(dummy_model, X, y, cv=kf)
    metrics['dummy_r2'] = r2_score(y, dummy_preds)
    metrics['dummy_rmse'] = root_mean_squared_error(y, dummy_preds)
    
    # Random Forest
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    rf_preds = cross_val_predict(rf_model, X, y, cv=kf)
    metrics['rf_r2'] = r2_score(y, rf_preds)
    metrics['rf_rmse'] = root_mean_squared_error(y, rf_preds)
    
    # Fit on all data for feature importances and residuals
    rf_model.fit(X, y)
    importances = rf_model.feature_importances_
    feat_names = X.columns
    
    # Sort importances
    imp_dict = {name: float(imp) for name, imp in zip(feat_names, importances)}
    sorted_importances = dict(sorted(imp_dict.items(), key=lambda item: item[1], reverse=True))
    metrics['feature_importances'] = sorted_importances
    
    # Generate Visualizations
    setup_plot_style()
    _generate_visualizations(y, rf_preds, sorted_importances, session_out_dir)
    
    # Generate Report
    generate_phase3_report(session_out_dir, session_id, metrics)
    print(f"Phase 3 complete. Results saved to {session_out_dir}")

def _generate_visualizations(y_true, y_pred, importances, session_out_dir):
    residuals = y_true - y_pred
    
    # 1. Prediction vs Actual
    fig = plt.figure(figsize=(8, 6))
    sns.scatterplot(x=y_pred, y=y_true, alpha=0.7)
    
    # Ideal line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--')
    
    plt.title('Prediction vs Actual Lap Time (Random Forest)')
    plt.xlabel('Predicted Lap Time (s)')
    plt.ylabel('Actual Lap Time (s)')
    save_plot(fig, session_out_dir, "phase3_pred_vs_actual.png")
    
    # 2. Residual Distribution
    fig = plt.figure(figsize=(8, 6))
    try:
        if residuals.var() > 0:
            sns.histplot(residuals, kde=True, bins=20)
        else:
            sns.histplot(residuals, kde=False, bins=20)
    except Exception:
        # Fallback to pure matplotlib if seaborn KDE fails
        plt.hist(residuals, bins=20)
        
    plt.axvline(x=0, color='r', linestyle='--')
    plt.title('Residual Distribution')
    plt.xlabel('Residuals (Actual - Predicted)')
    plt.ylabel('Count')
    save_plot(fig, session_out_dir, "phase3_residuals.png")
    
    # 3. Feature Importances
    fig = plt.figure(figsize=(10, 6))
    features = list(importances.keys())
    values = list(importances.values())
    sns.barplot(x=values, y=features, palette='viridis', hue=features, legend=False)
    plt.title('Feature Importances (Random Forest)')
    plt.xlabel('Importance')
    save_plot(fig, session_out_dir, "phase3_feature_importance.png")
