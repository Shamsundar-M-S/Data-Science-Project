import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OrdinalEncoder
from sklearn.inspection import permutation_importance

from src.analysis.historical_db import (
    load_historical_db,
    save_historical_db,
    add_race_observations,
    extract_race_records_from_session,
    compute_historical_features,
    HISTORICAL_COLUMNS
)
from src.analysis.plot_style import setup_plot_style, save_plot
from src.analysis.report_phase5 import generate_phase5_report


FEATURE_COLS_NUMERIC = [
    "grid_position",
    "qualifying_delta_pct",
    "driver_rolling_avg_finish",
    "team_rolling_avg_points",
    "championship_position"
]

FEATURE_COLS_CATEGORICAL = [
    "driver_id",
    "constructor_id",
    "circuit_id"
]

ALL_FEATURE_COLS = FEATURE_COLS_NUMERIC + FEATURE_COLS_CATEGORICAL


def run_phase5(session_id: str, data_dir: str = "analytics_data", output_dir: str = "analytics_output") -> None:
    """
    Phase 5: Race Outcome Predictive Analytics & Historical Database Integration.
    """
    laps_path = os.path.join(data_dir, f"{session_id}_laps.parquet")
    session_out_dir = os.path.join(output_dir, session_id)
    os.makedirs(session_out_dir, exist_ok=True)

    # 1. Load historical database
    df_db = load_historical_db()

    # 2. Inspect session laps if available to register current session in DB
    df_laps = None
    if os.path.exists(laps_path):
        df_laps = pd.read_parquet(laps_path)
        new_obs = extract_race_records_from_session(df_laps)
        if not new_obs.empty:
            df_db = add_race_observations(df_db, new_obs)
            save_historical_db(df_db)

    # 3. Compute leakage-free historical features across chronological races
    df_features = compute_historical_features(df_db)

    # 4. Identify target session observations
    target_mask = (df_features["event_name"].str.replace(" ", "_") == session_id) | \
                  (df_features["circuit_id"] == session_id)
    
    # Fallback match on season/round if explicit session_id match fails
    if not target_mask.any() and df_laps is not None and not df_laps.empty:
        season = int(df_laps["season"].iloc[0]) if "season" in df_laps.columns else 2024
        round_num = int(df_laps["round"].iloc[0]) if "round" in df_laps.columns else 1
        target_mask = (df_features["season"] == season) & (df_features["round"] == round_num)

    # If target session still not found, take the most recent race as target
    if not target_mask.any():
        max_s = df_features["season"].max()
        max_r = df_features[df_features["season"] == max_s]["round"].max()
        target_mask = (df_features["season"] == max_s) & (df_features["round"] == max_r)

    df_target = df_features[target_mask].copy().sort_values(by="grid_position").reset_index(drop=True)
    df_train_hist = df_features[~target_mask & df_features["finishing_position"].notna()].copy()

    # Check if target race is completed or prediction-only
    is_prediction_only = df_target["finishing_position"].isna().all()

    # 5. Expanding Window Temporal Validation
    val_summary = _perform_temporal_validation(df_train_hist)

    # 6. Fit Final Model on All Prior Historical Races
    model, encoder = _fit_model(df_train_hist)

    # 7. Generate Target Race Predictions
    predictions = []
    if model is not None and not df_target.empty:
        X_target = _prepare_feature_matrix(df_target, encoder)
        pred_vals = model.predict(X_target)
        df_target["pred_pos_val"] = pred_vals

        # Rank drivers by predicted position value (1 = lowest predicted value)
        df_target = df_target.sort_values(by="pred_pos_val").reset_index(drop=True)

        for i, row in df_target.iterrows():
            predictions.append({
                "driver_id": row["driver_id"],
                "constructor_id": row["constructor_id"],
                "grid_position": int(row["grid_position"]) if pd.notna(row["grid_position"]) else 10,
                "predicted_pos_val": float(row["pred_pos_val"]),
                "predicted_rank": i + 1,
                "actual_pos": float(row["finishing_position"]) if pd.notna(row["finishing_position"]) else None
            })

    # If target race was completed, evaluate metrics for this specific race
    if not is_prediction_only and df_target["finishing_position"].notna().any():
        race_metrics = _evaluate_single_race(df_target)
        val_summary["target_race_mae"] = race_metrics["mae"]
        val_summary["target_race_spearman"] = race_metrics["spearman"]
        val_summary["target_race_top3_overlap"] = race_metrics["top3_overlap"]

    metadata = {
        "status": "success",
        "session_id": session_id,
        "is_prediction_only": is_prediction_only,
        "predictions": predictions,
        "validation_summary": val_summary
    }

    # 8. Generate Visualizations
    setup_plot_style()
    _plot_predicted_vs_actual(df_target, is_prediction_only, session_out_dir)
    _plot_feature_importance(val_summary.get("feature_importances", {}), session_out_dir)

    # 9. Generate HTML Report
    generate_phase5_report(session_out_dir, session_id, metadata)
    print(f"Phase 5 complete. Results saved to {session_out_dir}")


def _prepare_feature_matrix(df: pd.DataFrame, encoder: Optional[OrdinalEncoder] = None) -> Tuple[np.ndarray, OrdinalEncoder]:
    """
    Extract numerical and categorical features into a numpy matrix compatible with HistGradientBoostingRegressor.
    Handles unknown categories safely.
    """
    X_num = df[FEATURE_COLS_NUMERIC].values.astype(float)
    X_cat_raw = df[FEATURE_COLS_CATEGORICAL].astype(str).values

    if encoder is None:
        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        X_cat = encoder.fit_transform(X_cat_raw)
    else:
        X_cat = encoder.transform(X_cat_raw)

    X = np.hstack([X_num, X_cat])
    return X if encoder is not None else (X, encoder)


def _fit_model(df_train: pd.DataFrame) -> Tuple[Optional[HistGradientBoostingRegressor], Optional[OrdinalEncoder]]:
    """
    Fit HistGradientBoostingRegressor with exact specified parameters.
    max_iter=100, max_depth=5, min_samples_leaf=10, random_state=42.
    """
    if df_train.empty or len(df_train) < 10:
        return None, None

    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_num = df_train[FEATURE_COLS_NUMERIC].values.astype(float)
    X_cat = encoder.fit_transform(df_train[FEATURE_COLS_CATEGORICAL].astype(str).values)
    X = np.hstack([X_num, X_cat])

    y = df_train["finishing_position"].values.astype(float)

    # Categorical indices in hstack are [5, 6, 7]
    cat_indices = list(range(len(FEATURE_COLS_NUMERIC), len(ALL_FEATURE_COLS)))

    model = HistGradientBoostingRegressor(
        max_iter=100,
        max_depth=5,
        min_samples_leaf=10,
        random_state=42,
        categorical_features=cat_indices
    )
    model.fit(X, y)
    return model, encoder


def _perform_temporal_validation(df_hist: pd.DataFrame) -> Dict[str, Any]:
    """
    Expanding window temporal validation across chronological historical races.
    Train on preceding races, validate on next race.
    """
    if df_hist.empty:
        return {}

    races = df_hist[["season", "round"]].drop_duplicates().sort_values(by=["season", "round"]).values
    if len(races) < 3:
        return {"model_mae": "N/A", "grid_mae": "N/A", "champ_mae": "N/A", "spearman_corr": "N/A", "top3_overlap_pct": "N/A", "val_races_count": 0}

    # Use last 30% of races for expanding window validation (minimum 2 races)
    n_val = max(2, int(len(races) * 0.3))
    val_races = races[-n_val:]

    model_maes = []
    grid_maes = []
    champ_maes = []
    spearmans = []
    top3_overlaps = []
    all_importances = []

    for s_val, r_val in val_races:
        df_tr = df_hist[(df_hist["season"] < s_val) | ((df_hist["season"] == s_val) & (df_hist["round"] < r_val)) & df_hist["finishing_position"].notna()]
        df_val = df_hist[(df_hist["season"] == s_val) & (df_hist["round"] == r_val) & df_hist["finishing_position"].notna()].copy()

        if df_tr.empty or df_val.empty:
            continue

        model, encoder = _fit_model(df_tr)
        if model is None:
            continue

        X_val = _prepare_feature_matrix(df_val, encoder)
        y_val = df_val["finishing_position"].values

        pred_val = model.predict(X_val)
        df_val["pred_pos_val"] = pred_val

        # Model MAE
        m_mae = np.mean(np.abs(pred_val - y_val))
        model_maes.append(m_mae)

        # Baseline 1: Grid Position MAE
        grid_mae = np.mean(np.abs(df_val["grid_position"].values - y_val))
        grid_maes.append(grid_mae)

        # Baseline 2: Championship Position MAE
        champ_mae = np.mean(np.abs(df_val["championship_position"].values - y_val))
        champ_maes.append(champ_mae)

        # Race Spearman Correlation
        if len(y_val) >= 3 and np.std(y_val) > 0 and np.std(pred_val) > 0:
            sp = spearmanr(pred_val, y_val).statistic
            if not np.isnan(sp):
                spearmans.append(sp)

        # Top 3 Overlap
        top3_overlaps.append(_calculate_top3_overlap(df_val, "pred_pos_val", "finishing_position"))

        # Permutation Importance on validation set
        try:
            perm_imp = permutation_importance(model, X_val, y_val, n_repeats=5, random_state=42)
            all_importances.append(perm_imp.importances_mean)
        except Exception:
            pass

    # Aggregate validation results
    avg_model_mae = float(np.mean(model_maes)) if model_maes else 0.0
    avg_grid_mae = float(np.mean(grid_maes)) if grid_maes else 0.0
    avg_champ_mae = float(np.mean(champ_maes)) if champ_maes else 0.0
    avg_spearman = float(np.mean(spearmans)) if spearmans else 0.0
    avg_top3 = float(np.mean(top3_overlaps)) if top3_overlaps else 0.0

    imp_dict = {}
    if all_importances:
        mean_imps = np.mean(all_importances, axis=0)
        for col_name, imp_val in zip(ALL_FEATURE_COLS, mean_imps):
            imp_dict[col_name] = max(0.0, float(imp_val))

    return {
        "model_mae": f"{avg_model_mae:.2f}",
        "grid_mae": f"{avg_grid_mae:.2f}",
        "champ_mae": f"{avg_champ_mae:.2f}",
        "spearman_corr": f"{avg_spearman:.3f}",
        "top3_overlap_pct": f"{avg_top3:.1f}%",
        "val_races_count": len(model_maes),
        "feature_importances": imp_dict
    }


def _evaluate_single_race(df_race: pd.DataFrame) -> Dict[str, float]:
    """
    Evaluate MAE, Spearman correlation, and Top-3 overlap for a single race.
    """
    y_true = df_race["finishing_position"].values
    y_pred = df_race["pred_pos_val"].values

    mae = float(np.mean(np.abs(y_pred - y_true)))

    if len(y_true) >= 3 and np.std(y_true) > 0 and np.std(y_pred) > 0:
        sp = float(spearmanr(y_pred, y_true).statistic)
        if np.isnan(sp):
            sp = 0.0
    else:
        sp = 0.0

    top3_ov = _calculate_top3_overlap(df_race, "pred_pos_val", "finishing_position")
    return {"mae": mae, "spearman": sp, "top3_overlap": top3_ov}


def _calculate_top3_overlap(df: pd.DataFrame, pred_col: str, actual_col: str) -> float:
    """
    Calculate Podium / Top-3 Overlap percentage.
    """
    if len(df) < 3 or df[actual_col].isna().all():
        return 0.0

    pred_top3 = set(df.sort_values(by=pred_col)["driver_id"].head(3))
    actual_top3 = set(df.sort_values(by=actual_col)["driver_id"].head(3))

    overlap_count = len(pred_top3.intersection(actual_top3))
    return float(overlap_count / 3.0 * 100.0)


def _plot_predicted_vs_actual(df_target: pd.DataFrame, is_prediction_only: bool, out_dir: str) -> None:
    """
    Plot predicted vs actual finishing position comparison chart.
    """
    fig = plt.figure(figsize=(12, 6))
    
    if df_target.empty:
        plt.title("No Race Data Available")
        save_plot(fig, out_dir, "phase5_predicted_vs_actual.png")
        return

    df_plot = df_target.copy()
    drivers = df_plot["driver_id"].tolist()
    grid_pos = df_plot["grid_position"].tolist()
    pred_rank = list(range(1, len(drivers) + 1))

    plt.plot(drivers, grid_pos, marker='o', linestyle='--', color='#9ca3af', label='Starting Grid', alpha=0.7)
    plt.plot(drivers, pred_rank, marker='s', linestyle='-', color='#ef4444', label='Predicted Finish Rank', linewidth=2)

    if not is_prediction_only and df_plot["finishing_position"].notna().any():
        actual_pos = df_plot["finishing_position"].tolist()
        plt.plot(drivers, actual_pos, marker='^', linestyle='-', color='#22c55e', label='Actual Race Finish', linewidth=2)
        plt.title("F1 Race Outcome Prediction: Starting Grid vs Predicted vs Actual")
    else:
        plt.title("F1 Race Outcome Prediction: Starting Grid vs Predicted Finish Rank (Prediction Only)")

    plt.xlabel("Driver")
    plt.ylabel("Position (1 = Winner)")
    plt.gca().invert_yaxis()  # Position 1 at top
    plt.xticks(rotation=45)
    plt.legend()
    save_plot(fig, out_dir, "phase5_predicted_vs_actual.png")


def _plot_feature_importance(importances: Dict[str, float], out_dir: str) -> None:
    """
    Plot horizontal bar chart of Permutation Feature Importances.
    """
    fig = plt.figure(figsize=(10, 6))
    
    if not importances:
        importances = {col: 0.1 for col in ALL_FEATURE_COLS}

    df_imp = pd.DataFrame(list(importances.items()), columns=["Feature", "Importance"]).sort_values(by="Importance", ascending=True)

    plt.barh(df_imp["Feature"], df_imp["Importance"], color="#3b82f6", edgecolor="black")
    plt.title("Phase 5 Permutation Feature Importance (Validation Data)")
    plt.xlabel("Mean Permutation Importance (Increase in MAE)")
    plt.ylabel("Pre-Race Feature")
    save_plot(fig, out_dir, "phase5_feature_importance.png")
