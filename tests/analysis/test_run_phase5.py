import os
import pytest
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.analysis.run_phase5 import (
    run_phase5,
    _fit_model,
    _prepare_feature_matrix,
    _calculate_top3_overlap,
    _evaluate_single_race,
    _perform_temporal_validation
)
from src.analysis.historical_db import load_historical_db, compute_historical_features
from src.analysis.report_phase5 import generate_phase5_report


def test_fit_model_hyperparameters():
    df_db = load_historical_db()
    df_feats = compute_historical_features(df_db)

    model, encoder = _fit_model(df_feats)
    assert model is not None
    assert encoder is not None
    assert model.max_iter == 100
    assert model.max_depth == 5
    assert model.min_samples_leaf == 10
    assert model.random_state == 42


def test_categorical_unknown_handling():
    df_db = load_historical_db()
    df_feats = compute_historical_features(df_db)

    model, encoder = _fit_model(df_feats)

    # Unseen driver and team
    df_unseen = pd.DataFrame([{
        "grid_position": 1.0,
        "qualifying_delta_pct": 0.0,
        "driver_rolling_avg_finish": 1.0,
        "team_rolling_avg_points": 25.0,
        "championship_position": 1.0,
        "driver_id": "UNSEEN_DRIVER_99",
        "constructor_id": "UNSEEN_TEAM_99",
        "circuit_id": "UNSEEN_CIRCUIT_99"
    }])

    X_unseen = _prepare_feature_matrix(df_unseen, encoder)
    preds = model.predict(X_unseen)

    assert len(preds) == 1
    assert not np.isnan(preds[0])


def test_top3_overlap_calculation():
    df_test = pd.DataFrame({
        "driver_id": ["A", "B", "C", "D", "E"],
        "pred_pos_val": [1.0, 2.0, 3.0, 4.0, 5.0],
        "finishing_position": [1.0, 2.0, 3.0, 4.0, 5.0]
    })
    ov100 = _calculate_top3_overlap(df_test, "pred_pos_val", "finishing_position")
    assert ov100 == 100.0

    df_partial = pd.DataFrame({
        "driver_id": ["A", "B", "C", "D", "E"],
        "pred_pos_val": [1.0, 2.0, 4.0, 3.0, 5.0],  # C and D swapped
        "finishing_position": [1.0, 2.0, 3.0, 4.0, 5.0]  # Top 3 are A, B, C. Pred top 3 are A, B, D. Overlap = 2/3 = 66.67%
    })
    ov66 = _calculate_top3_overlap(df_partial, "pred_pos_val", "finishing_position")
    assert pytest.approx(ov66, 0.1) == 66.67


def test_evaluate_single_race():
    df_race = pd.DataFrame({
        "driver_id": ["VER", "HAM", "LEC", "NOR"],
        "pred_pos_val": [1.1, 2.2, 3.3, 4.4],
        "finishing_position": [1.0, 2.0, 3.0, 4.0]
    })

    metrics = _evaluate_single_race(df_race)
    assert "mae" in metrics
    assert "spearman" in metrics
    assert "top3_overlap" in metrics
    assert metrics["mae"] < 0.5
    assert metrics["spearman"] == 1.0
    assert metrics["top3_overlap"] == 100.0


def test_perform_temporal_validation():
    df_db = load_historical_db()
    df_feats = compute_historical_features(df_db)

    val_res = _perform_temporal_validation(df_feats)
    assert "model_mae" in val_res
    assert "spearman_corr" in val_res
    assert "top3_overlap_pct" in val_res
    assert val_res["val_races_count"] > 0


def test_report_generation_completed_and_prediction_only(tmp_path):
    out_dir = str(tmp_path)
    session_id = "2024_01_Test_Grand_Prix_Race"

    meta_completed = {
        "is_prediction_only": False,
        "predictions": [
            {"driver_id": "VER", "constructor_id": "Red Bull", "grid_position": 1, "predicted_pos_val": 1.05, "actual_pos": 1.0},
            {"driver_id": "HAM", "constructor_id": "Mercedes", "grid_position": 2, "predicted_pos_val": 2.10, "actual_pos": 2.0}
        ],
        "validation_summary": {"model_mae": "1.20", "grid_mae": "1.80", "champ_mae": "2.10", "spearman_corr": "0.850", "top3_overlap_pct": "66.7%"}
    }

    report_path = generate_phase5_report(out_dir, session_id, meta_completed)
    assert os.path.exists(report_path)
    assert f"phase5_report_{session_id}.html" in report_path

    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()
    assert "COMPLETED RACE" in html
    assert "VER" in html

    meta_pred_only = {
        "is_prediction_only": True,
        "predictions": [
            {"driver_id": "VER", "constructor_id": "Red Bull", "grid_position": 1, "predicted_pos_val": 1.05, "actual_pos": None}
        ],
        "validation_summary": {}
    }
    report_path_pred = generate_phase5_report(out_dir, "2025_01_Future_GP_Race", meta_pred_only)
    with open(report_path_pred, "r", encoding="utf-8") as f:
        html_pred = f.read()
    assert "PREDICTION-ONLY RACE" in html_pred
    assert "Actual Result: Not Available — Prediction Only" in html_pred


def test_run_phase5_e2e_mock(tmp_path):
    data_dir = os.path.join(tmp_path, "analytics_data")
    output_dir = os.path.join(tmp_path, "analytics_output")
    session_id = "2024_01_Bahrain_Grand_Prix_Race"

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Create mock laps parquet
    df_laps = pd.DataFrame({
        "season": [2024]*4,
        "round": [1]*4,
        "event": ["Bahrain Grand Prix"]*4,
        "Driver": ["VER", "PER", "SAI", "LEC"],
        "Team": ["Red Bull Racing", "Red Bull Racing", "Ferrari", "Ferrari"],
        "GridPosition": [1, 2, 3, 4],
        "Position": [1, 2, 3, 4],
        "LapTime_s": [90.0, 90.5, 90.8, 91.0]
    })
    df_laps.to_parquet(os.path.join(data_dir, f"{session_id}_laps.parquet"), index=False)

    run_phase5(session_id, data_dir=data_dir, output_dir=output_dir)

    target_out_dir = os.path.join(output_dir, session_id)
    assert os.path.exists(os.path.join(target_out_dir, f"phase5_report_{session_id}.html"))
    assert os.path.exists(os.path.join(target_out_dir, "phase5_predicted_vs_actual.png"))
    assert os.path.exists(os.path.join(target_out_dir, "phase5_feature_importance.png"))
