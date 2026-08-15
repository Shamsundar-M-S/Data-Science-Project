import pytest
import pandas as pd
import numpy as np

from src.analysis.statistics import (
    calculate_correlations,
    analyze_weather_impact,
    compare_group_differences
)

def test_calculate_correlations():
    df = pd.DataFrame({
        "LapTime_s": [90, 91, 92, 93, 94],
        "TyreLife": [1, 2, 3, 4, 5],
        "TrackTemp": [40, 39, 38, 37, 36],
        "is_clean_lap": [True, True, True, True, True]
    })
    
    corrs = calculate_correlations(df)
    assert "pearson" in corrs
    assert "spearman" in corrs
    
    p = corrs["pearson"]
    # Lap time perfectly correlates with TyreLife here
    assert p.loc["LapTime_s", "TyreLife"] == pytest.approx(1.0)
    # Track temp inversely correlates with Lap time
    assert p.loc["LapTime_s", "TrackTemp"] == pytest.approx(-1.0)

def test_analyze_weather_impact_insufficient_variation():
    df = pd.DataFrame({
        "LapTime_s": [90]*15,
        "TrackTemp": [40]*15, # 0 variation
        "is_clean_lap": [True]*15
    })
    
    res = analyze_weather_impact(df)
    assert res["status"] == "insufficient_variation"

def test_analyze_weather_impact_success():
    df = pd.DataFrame({
        "LapTime_s": np.random.normal(90, 1, 20),
        "TrackTemp": np.random.normal(40, 5, 20), # sufficient variation
        "is_clean_lap": [True]*20
    })
    
    res = analyze_weather_impact(df)
    assert res["status"] == "success"
    assert "spearman_r" in res
    assert "p_value" in res

def test_compare_group_differences():
    df = pd.DataFrame({
        "Driver": ["A"]*5 + ["B"]*5,
        "LapTime_s": [90, 90.1, 89.9, 90.2, 90.0] + [92, 92.1, 91.9, 92.2, 92.0],
        "is_clean_lap": [True]*10
    })
    
    res = compare_group_differences(df, "Driver", "LapTime_s")
    assert res["status"] == "success"
    assert res["test"] == "Kruskal-Wallis H-test"
    assert res["p_value"] < 0.05 # Should be significantly different
    assert res["n_samples"] == 10
    
def test_compare_group_differences_insufficient_groups():
    df = pd.DataFrame({
        "Driver": ["A"]*5 + ["B"]*1, # B has less than 3 samples
        "LapTime_s": [90, 90.1, 89.9, 90.2, 90.0, 92.0],
        "is_clean_lap": [True]*6
    })
    
    res = compare_group_differences(df, "Driver", "LapTime_s")
    assert res["status"] == "insufficient_groups"
