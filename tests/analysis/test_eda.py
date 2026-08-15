import pytest
import pandas as pd
import numpy as np

from src.analysis.eda import (
    generate_data_quality_profile, 
    generate_descriptive_summaries,
    plot_data_quality,
    plot_track_temp_vs_lap_time,
    plot_correlation_heatmap
)

def test_generate_data_quality_profile_empty():
    df_empty = pd.DataFrame()
    profiles = generate_data_quality_profile(df_empty, df_empty)
    assert len(profiles) == 0

def test_generate_data_quality_profile():
    df_laps = pd.DataFrame({
        "LapTime_s": [90.5, 91.0, np.nan],
        "Driver": ["A", "B", "A"]
    })
    df_tel = pd.DataFrame({
        "Speed": [300, 310, 320]
    })
    
    profiles = generate_data_quality_profile(df_laps, df_tel)
    assert "laps" in profiles
    assert "telemetry" in profiles
    
    lap_prof = profiles["laps"]
    assert lap_prof.loc["LapTime_s", "Missing_Count"] == 1
    assert lap_prof.loc["Driver", "Missing_Count"] == 0
    assert lap_prof.loc["Driver", "Unique_Count"] == 2

def test_generate_descriptive_summaries():
    df_laps = pd.DataFrame({
        "Driver": ["A", "A", "B", "B", "C"],
        "Compound": ["SOFT", "SOFT", "MEDIUM", "MEDIUM", "HARD"],
        "LapTime_s": [90.0, 91.0, 92.0, 93.0, 95.0],
        "LapNumber": [1, 2, 1, 2, 1],
        "is_clean_lap": [True, True, True, False, True]
    })
    
    drivers, compounds = generate_descriptive_summaries(df_laps)
    
    # Driver B has 1 clean lap, Driver A has 2, C has 1
    assert len(drivers) == 3
    
    driver_a = drivers[drivers["Driver"] == "A"].iloc[0]
    assert driver_a["Clean_Laps"] == 2
    assert driver_a["Min_LapTime_s"] == 90.0
    
    driver_b = drivers[drivers["Driver"] == "B"].iloc[0]
    assert driver_b["Clean_Laps"] == 1
    assert driver_b["Median_LapTime_s"] == 92.0

def test_generate_descriptive_summaries_empty():
    df_empty = pd.DataFrame({
        "Driver": [], "Compound": [], "LapTime_s": [], "is_clean_lap": []
    })
    drivers, compounds = generate_descriptive_summaries(df_empty)
    assert drivers.empty
    assert compounds.empty

def test_plot_data_quality(mocker, tmp_path):
    df_laps = pd.DataFrame({"is_clean_lap": [True, False, True]})
    mock_savefig = mocker.patch("matplotlib.figure.Figure.savefig")
    plot_data_quality(df_laps, str(tmp_path))
    mock_savefig.assert_called_once()

def test_plot_track_temp_vs_lap_time(mocker, tmp_path):
    df_laps = pd.DataFrame({
        "is_clean_lap": [True, True],
        "TrackTemp": [40.0, 41.0],
        "LapTime_s": [90.0, 91.0]
    })
    mock_savefig = mocker.patch("matplotlib.figure.Figure.savefig")
    plot_track_temp_vs_lap_time(df_laps, str(tmp_path))
    mock_savefig.assert_called_once()

def test_plot_correlation_heatmap(mocker, tmp_path):
    df_laps = pd.DataFrame({
        "is_clean_lap": [True, True, True],
        "TrackTemp": [40.0, 41.0, 42.0],
        "LapTime_s": [90.0, 91.0, 92.0]
    })
    mock_savefig = mocker.patch("matplotlib.figure.Figure.savefig")
    plot_correlation_heatmap(df_laps, str(tmp_path))
    mock_savefig.assert_called_once()
