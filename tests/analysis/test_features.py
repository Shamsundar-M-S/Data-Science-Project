import pytest
import pandas as pd
import numpy as np

from src.analysis.features import engineer_lap_features

def test_engineer_lap_features_empty():
    df_laps = pd.DataFrame()
    df_tel = pd.DataFrame()
    df_features = engineer_lap_features(df_laps, df_tel)
    assert df_features.empty

def test_engineer_lap_features_missing_tel():
    df_laps = pd.DataFrame({
        "Driver": ["VER"],
        "LapNumber": [1],
        "LapTime_s": [90.0]
    })
    df_tel = pd.DataFrame({
        "driver_code": ["HAM"],
        "lap_number": [1]
    })
    df_features = engineer_lap_features(df_laps, df_tel)
    assert len(df_features) == 1
    assert df_features.iloc[0]["telemetry_sample_count"] == 0
    assert pd.isna(df_features.iloc[0]["speed_mean"])

def test_engineer_lap_features_basic():
    df_laps = pd.DataFrame({
        "Driver": ["VER", "VER"],
        "LapNumber": [1, 2],
        "LapTime_s": [90.0, 89.0],
        "is_clean_lap": [True, True]
    })
    
    df_tel = pd.DataFrame({
        "driver_code": ["VER", "VER", "VER", "VER"],
        "lap_number": [1, 1, 2, 2],
        "Distance": [0, 100, 0, 100],
        "Speed": [100.0, 200.0, 300.0, 310.0],
        "Throttle": [50.0, 100.0, 0.0, 10.0],
        "Brake": [False, True, False, False],
        "DRS": [8, 12, 8, 8],
        "nGear": [2, 3, 4, 4]
    })
    
    df_features = engineer_lap_features(df_laps, df_tel)
    assert len(df_features) == 2
    
    # Lap 1 Features
    lap1 = df_features[df_features["LapNumber"] == 1].iloc[0]
    assert lap1["telemetry_sample_count"] == 2
    assert lap1["distance_span"] == 100.0
    assert lap1["speed_max"] == 200.0
    assert lap1["speed_mean"] == 150.0
    assert lap1["throttle_full_pct"] == 50.0
    assert lap1["brake_active_pct"] == 50.0
    assert lap1["brake_events_count"] == 1
    assert lap1["drs_active_pct"] == 50.0
    assert lap1["gear_max"] == 3
    assert lap1["gear_8_pct"] == 0.0
    
    # Lap 2 Features
    lap2 = df_features[df_features["LapNumber"] == 2].iloc[0]
    assert lap2["telemetry_sample_count"] == 2
    assert lap2["speed_max"] == 310.0
    assert lap2["brake_events_count"] == 0
    assert lap2["drs_active_pct"] == 0.0

def test_brake_events_count():
    df_laps = pd.DataFrame({"Driver": ["VER"], "LapNumber": [1]})
    df_tel = pd.DataFrame({
        "driver_code": ["VER"] * 9,
        "lap_number": [1] * 9,
        "Distance": range(9),
        "Speed": [100] * 9,
        "Throttle": [100] * 9,
        "Brake": [False, False, True, True, True, False, True, True, False],
        "DRS": [0] * 9,
        "nGear": [1] * 9
    })
    
    df_features = engineer_lap_features(df_laps, df_tel)
    assert df_features.iloc[0]["brake_events_count"] == 2
