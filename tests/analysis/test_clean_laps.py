import pandas as pd
import pytest

from src.analysis.clean_laps import (
    is_out_lap,
    is_in_lap,
    is_pit_lap,
    is_sc_vsc_affected,
    is_clean_lap,
)


def test_is_out_lap():
    # Out lap has PitOutTime
    assert is_out_lap(pd.Series({"PitOutTime": pd.Timedelta(seconds=10)})) is True
    # Normal lap
    assert is_out_lap(pd.Series({"PitOutTime": pd.NaT})) is False
    # Missing column
    assert is_out_lap(pd.Series({"LapTime": 1.0})) is False


def test_is_in_lap():
    # In lap has PitInTime
    assert is_in_lap(pd.Series({"PitInTime": pd.Timedelta(seconds=10)})) is True
    # Normal lap
    assert is_in_lap(pd.Series({"PitInTime": pd.NaT})) is False
    # Missing column
    assert is_in_lap(pd.Series({"LapTime": 1.0})) is False


def test_is_pit_lap():
    # In lap
    assert is_pit_lap(pd.Series({"PitInTime": pd.Timedelta(seconds=1)})) is True
    # Out lap
    assert is_pit_lap(pd.Series({"PitOutTime": pd.Timedelta(seconds=1)})) is True
    # Both (e.g. drive through)
    assert is_pit_lap(pd.Series({"PitInTime": pd.Timedelta(seconds=1), "PitOutTime": pd.Timedelta(seconds=2)})) is True
    # Clean
    assert is_pit_lap(pd.Series({"PitInTime": pd.NaT, "PitOutTime": pd.NaT})) is False


def test_is_sc_vsc_affected():
    # Status 1 is clear
    assert is_sc_vsc_affected(pd.Series({"TrackStatus": "1"})) is False
    assert is_sc_vsc_affected(pd.Series({"TrackStatus": "12"})) is False
    # Status 4 is SC
    assert is_sc_vsc_affected(pd.Series({"TrackStatus": "14"})) is True
    assert is_sc_vsc_affected(pd.Series({"TrackStatus": "4"})) is True
    # Status 6 is VSC, 7 is VSC ending
    assert is_sc_vsc_affected(pd.Series({"TrackStatus": "6"})) is True
    assert is_sc_vsc_affected(pd.Series({"TrackStatus": "17"})) is True


def test_is_clean_lap():
    # Perfectly clean lap
    clean = pd.Series({
        "IsAccurate": True,
        "PitOutTime": pd.NaT,
        "PitInTime": pd.NaT,
        "TrackStatus": "1"
    })
    assert is_clean_lap(clean) is True

    # Not accurate
    not_accurate = clean.copy()
    not_accurate["IsAccurate"] = False
    assert is_clean_lap(not_accurate) is False

    # Pit lap
    pit = clean.copy()
    pit["PitInTime"] = pd.Timedelta(seconds=1)
    assert is_clean_lap(pit) is False

    # SC affected
    sc = clean.copy()
    sc["TrackStatus"] = "4"
    assert is_clean_lap(sc) is False
