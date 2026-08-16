import os
import pandas as pd
from src.analysis.run_phase4 import run_phase4

def test_run_phase4_success(tmp_path):
    data_dir = tmp_path / "analytics_data"
    out_dir = tmp_path / "analytics_output"
    data_dir.mkdir()
    out_dir.mkdir()
    
    session_id = "test_session_race"
    
    # Create valid synthetic laps dataset
    df = pd.DataFrame({
        'Driver': ['VER'] * 5 + ['HAM'] * 5,
        'Stint': [1] * 5 + [1] * 5,
        'Compound': ['SOFT'] * 5 + ['MEDIUM'] * 5,
        'TyreLife': [1.0, 2.0, 3.0, 4.0, 5.0] * 2,
        'LapTime_s': [90.0, 90.1, 90.2, 90.3, 90.4] * 2,
        'is_clean_lap': [True] * 10,
        'LapNumber': list(range(1, 6)) * 2,
        'session_type': ['Race'] * 10
    })
    
    laps_path = data_dir / f"{session_id}_laps.parquet"
    df.to_parquet(laps_path)
    
    run_phase4(session_id, str(data_dir), str(out_dir))
    
    session_out = out_dir / session_id
    assert (session_out / f"phase4_report_{session_id}.html").exists()
    assert (session_out / "phase4_tyre_degradation.png").exists()
    assert (session_out / "phase4_stint_pace.png").exists()
    assert (session_out / "phase4_driver_pace.png").exists()
    assert (session_out / "phase4_compound_performance.png").exists()
    assert (session_out / "phase4_strategy_timeline.png").exists()

def test_run_phase4_insufficient_samples(tmp_path):
    data_dir = tmp_path / "analytics_data"
    out_dir = tmp_path / "analytics_output"
    data_dir.mkdir()
    out_dir.mkdir()
    
    session_id = "short_session"
    
    # Create dataset with < 3 clean laps per stint
    df = pd.DataFrame({
        'Driver': ['VER'] * 2,
        'Stint': [1] * 2,
        'Compound': ['SOFT'] * 2,
        'TyreLife': [1.0, 2.0],
        'LapTime_s': [90.0, 90.1],
        'is_clean_lap': [True] * 2,
        'LapNumber': [1, 2],
        'session_type': ['Race'] * 2
    })
    
    laps_path = data_dir / f"{session_id}_laps.parquet"
    df.to_parquet(laps_path)
    
    run_phase4(session_id, str(data_dir), str(out_dir))
    
    session_out = out_dir / session_id
    assert (session_out / f"phase4_report_{session_id}.html").exists()
    assert not (session_out / "phase4_tyre_degradation.png").exists()
    assert (session_out / "phase4_strategy_timeline.png").exists()

def test_run_phase4_non_race(tmp_path):
    data_dir = tmp_path / "analytics_data"
    out_dir = tmp_path / "analytics_output"
    data_dir.mkdir()
    out_dir.mkdir()
    
    session_id = "practice_session"
    
    df = pd.DataFrame({
        'Driver': ['VER'] * 5,
        'Stint': [1] * 5,
        'Compound': ['SOFT'] * 5,
        'TyreLife': [1.0, 2.0, 3.0, 4.0, 5.0],
        'LapTime_s': [90.0, 90.1, 90.2, 90.3, 90.4],
        'is_clean_lap': [True] * 5,
        'LapNumber': list(range(1, 6)),
        'session_type': ['Practice 1'] * 5
    })
    
    laps_path = data_dir / f"{session_id}_laps.parquet"
    df.to_parquet(laps_path)
    
    run_phase4(session_id, str(data_dir), str(out_dir))
    
    session_out = out_dir / session_id
    assert (session_out / f"phase4_report_{session_id}.html").exists()
    # Strategy timeline should NOT exist for non-race sessions
    assert not (session_out / "phase4_strategy_timeline.png").exists()
