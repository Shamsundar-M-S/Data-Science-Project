import pandas as pd
import numpy as np
from src.analysis.strategy import (
    analyze_tyre_degradation,
    analyze_stints,
    analyze_driver_pace,
    analyze_strategy_timeline
)

def test_analyze_tyre_degradation():
    df = pd.DataFrame({
        'Driver': ['VER'] * 5 + ['VER'] * 2,
        'Stint': [1] * 5 + [2] * 2,
        'Compound': ['SOFT'] * 5 + ['HARD'] * 2,
        'TyreLife': [1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 2.0],
        'LapTime_s': [90.0, 90.1, 90.2, 90.3, 90.4, 91.0, 91.0],
        'is_clean_lap': [True] * 7
    })
    
    res = analyze_tyre_degradation(df)
    assert len(res) == 1
    assert res.iloc[0]['Stint'] == 1
    # Expected slope is 0.1
    assert np.isclose(res.iloc[0]['degradation_s_per_lap'], 0.1)

def test_analyze_tyre_degradation_insufficient():
    df = pd.DataFrame({
        'Driver': ['VER'] * 2,
        'Stint': [1] * 2,
        'Compound': ['SOFT'] * 2,
        'TyreLife': [1.0, 2.0],
        'LapTime_s': [90.0, 90.1],
        'is_clean_lap': [True] * 2
    })
    res = analyze_tyre_degradation(df)
    assert res.empty

def test_analyze_stints():
    df = pd.DataFrame({
        'Driver': ['VER'] * 4,
        'Stint': [1] * 4,
        'Compound': ['SOFT'] * 4,
        'TyreLife': [1.0, 2.0, 3.0, 4.0],
        'LapTime_s': [90.0, 91.0, np.nan, 92.0],
        'LapNumber': [1, 2, 3, 4],
        'is_clean_lap': [True, True, False, True]
    })
    res = analyze_stints(df)
    assert len(res) == 1
    assert res.iloc[0]['clean_laps_count'] == 3
    assert res.iloc[0]['stint_length'] == 4

def test_analyze_strategy_timeline():
    df = pd.DataFrame({
        'Driver': ['VER', 'VER', 'VER'],
        'Stint': [1, 1, 2],
        'Compound': ['SOFT', 'SOFT', 'HARD'],
        'LapNumber': [1, 2, 3]
    })
    res = analyze_strategy_timeline(df)
    assert len(res) == 2
    assert res.iloc[0]['Compound'] == 'SOFT'
    assert res.iloc[0]['end_lap'] == 2
