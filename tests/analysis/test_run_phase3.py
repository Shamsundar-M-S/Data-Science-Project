import os
import pandas as pd
import pytest
from src.analysis.run_phase3 import run_phase3
from src.analysis.report_phase3 import generate_phase3_report

def test_run_phase3_success(tmp_path):
    data_dir = tmp_path / "analytics_data"
    out_dir = tmp_path / "analytics_output"
    data_dir.mkdir()
    out_dir.mkdir()
    
    session_id = "test_session"
    
    # Create valid synthetic feature dataset with > 10 rows
    df = pd.DataFrame({
        'is_clean_lap': [True] * 20,
        'speed_mean': [200.0] * 20,
        'throttle_full_pct': [70.0] * 20,
        'brake_active_pct': [15.0] * 20,
        'drs_active_pct': [25.0] * 20,
        'TyreLife': [5] * 20,
        'Compound': ['SOFT'] * 20,
        'LapTime_s': [90.0 + i for i in range(20)]
    })
    features_path = data_dir / f"{session_id}_features.parquet"
    df.to_parquet(features_path)
    
    run_phase3(session_id, str(data_dir), str(out_dir))
    
    # Check outputs exist
    session_out = out_dir / session_id
    assert (session_out / f"phase3_report_{session_id}.html").exists()
    assert (session_out / "phase3_pred_vs_actual.png").exists()
    assert (session_out / "phase3_residuals.png").exists()
    assert (session_out / "phase3_feature_importance.png").exists()

def test_run_phase3_insufficient_samples(tmp_path):
    data_dir = tmp_path / "analytics_data"
    out_dir = tmp_path / "analytics_output"
    data_dir.mkdir()
    out_dir.mkdir()
    
    session_id = "short_session"
    
    # Create dataset with < 10 clean laps
    df = pd.DataFrame({
        'is_clean_lap': [True] * 5,
        'speed_mean': [200.0] * 5,
        'throttle_full_pct': [70.0] * 5,
        'brake_active_pct': [15.0] * 5,
        'drs_active_pct': [25.0] * 5,
        'TyreLife': [5] * 5,
        'Compound': ['SOFT'] * 5,
        'LapTime_s': [90.0] * 5
    })
    df.to_parquet(data_dir / f"{session_id}_features.parquet")
    
    run_phase3(session_id, str(data_dir), str(out_dir))
    
    session_out = out_dir / session_id
    assert (session_out / f"phase3_report_{session_id}.html").exists()
    # It shouldn't generate charts
    assert not (session_out / "phase3_pred_vs_actual.png").exists()

def test_run_phase3_missing_columns(tmp_path, capsys):
    data_dir = tmp_path / "analytics_data"
    out_dir = tmp_path / "analytics_output"
    data_dir.mkdir()
    
    session_id = "bad_session"
    
    # Missing speed_mean
    df = pd.DataFrame({
        'is_clean_lap': [True] * 15,
        'LapTime_s': [90.0] * 15
    })
    df.to_parquet(data_dir / f"{session_id}_features.parquet")
    
    run_phase3(session_id, str(data_dir), str(out_dir))
    
    captured = capsys.readouterr()
    assert "Missing required columns" in captured.out
