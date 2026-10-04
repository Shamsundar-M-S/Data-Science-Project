import os
import pytest
import numpy as np
import pandas as pd

from src.analysis.historical_db import (
    load_historical_db,
    save_historical_db,
    add_race_observations,
    extract_race_records_from_session,
    compute_historical_features,
    HISTORICAL_COLUMNS
)


def test_load_historical_db_returns_dataframe(tmp_path):
    db_file = os.path.join(tmp_path, "test_hist.parquet")
    df = load_historical_db(db_file)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    for col in HISTORICAL_COLUMNS:
        assert col in df.columns


def test_save_and_load_historical_db_roundtrip(tmp_path):
    db_file = os.path.join(tmp_path, "test_hist_roundtrip.parquet")
    df_orig = load_historical_db(db_file)
    save_historical_db(df_orig, db_file)

    assert os.path.exists(db_file)
    df_loaded = pd.read_parquet(db_file)
    assert len(df_loaded) == len(df_orig)


def test_incremental_add_race_observations(tmp_path):
    test_db_file = os.path.join(tmp_path, "test_inc.parquet")
    df_existing = load_historical_db(test_db_file)
    initial_len = len(df_existing)

    new_rows = pd.DataFrame([{
        "season": 2025,
        "round": 1,
        "event_name": "Test Grand Prix",
        "circuit_id": "Test_Circuit",
        "driver_id": "NEW",
        "constructor_id": "Test Team",
        "grid_position": 1.0,
        "qualifying_time": 80.0,
        "pole_time": 80.0,
        "qualifying_delta_pct": 0.0,
        "finishing_position": 1.0,
        "points": 25.0,
        "status": "Finished"
    }])

    df_updated = add_race_observations(df_existing, new_rows)
    assert len(df_updated) == initial_len + 1
    assert "NEW" in df_updated["driver_id"].values

    # Adding duplicate row updates in-place without expanding length
    df_updated2 = add_race_observations(df_updated, new_rows)
    assert len(df_updated2) == len(df_updated)


def test_compute_historical_features_strict_no_leakage():
    # Construct 3 races for driver VER and HAM
    records = []
    for r in [1, 2, 3]:
        records.append({
            "season": 2024,
            "round": r,
            "event_name": f"GP {r}",
            "circuit_id": f"Circuit_{r}",
            "driver_id": "VER",
            "constructor_id": "Red Bull Racing",
            "grid_position": 1.0,
            "qualifying_time": 80.0,
            "pole_time": 80.0,
            "qualifying_delta_pct": 0.0,
            "finishing_position": float(r),  # Finishes P1, P2, P3
            "points": float(25 - r),
            "status": "Finished"
        })

    df_raw = pd.DataFrame(records)
    df_feats = compute_historical_features(df_raw)

    # Race 1: no prior races, driver_rolling_avg_finish should equal grid_position (1.0)
    row_r1 = df_feats[df_feats["round"] == 1].iloc[0]
    assert row_r1["driver_rolling_avg_finish"] == 1.0

    # Race 2: prior race 1 finish was P1 (1.0). Target race 2 finish (2.0) MUST NOT LEAK into race 2 features!
    row_r2 = df_feats[df_feats["round"] == 2].iloc[0]
    assert row_r2["driver_rolling_avg_finish"] == 1.0

    # Race 3: prior races were P1 and P2 -> mean = 1.5. Target race 3 finish (3.0) MUST NOT LEAK!
    row_r3 = df_feats[df_feats["round"] == 3].iloc[0]
    assert row_r3["driver_rolling_avg_finish"] == 1.5


def test_extract_race_records_from_session():
    laps_data = pd.DataFrame({
        "season": [2024, 2024, 2024],
        "round": [1, 1, 1],
        "event": ["Monaco Grand Prix", "Monaco Grand Prix", "Monaco Grand Prix"],
        "Driver": ["VER", "HAM", "LEC"],
        "Team": ["Red Bull", "Mercedes", "Ferrari"],
        "GridPosition": [1, 2, 3],
        "Position": [1, 3, 2],
        "LapTime_s": [75.0, 75.5, 75.2]
    })

    df_obs = extract_race_records_from_session(laps_data)
    assert len(df_obs) == 3
    assert set(df_obs["driver_id"]) == {"VER", "HAM", "LEC"}
    assert df_obs["pole_time"].iloc[0] == 75.0
    assert df_obs[df_obs["driver_id"] == "VER"]["qualifying_delta_pct"].iloc[0] == 0.0
