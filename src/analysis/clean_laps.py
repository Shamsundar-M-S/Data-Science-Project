"""
Canonical Clean Lap Definition for F1 Telemetry Data Science.

This module provides the central source of truth for filtering laps
across all analytical pipelines. It prevents duplicate or conflicting
definitions of "clean lap" in future Data Science modules.
"""

import pandas as pd


def is_out_lap(lap: pd.Series) -> bool:
    """
    Check if a lap is an out-lap (started from the pit lane).
    """
    # In FastF1, PitOutTime is set if the lap started from the pits
    return pd.notna(lap.get("PitOutTime"))


def is_in_lap(lap: pd.Series) -> bool:
    """
    Check if a lap is an in-lap (ended in the pit lane).
    """
    # In FastF1, PitInTime is set if the lap ended in the pits
    return pd.notna(lap.get("PitInTime"))


def is_pit_lap(lap: pd.Series) -> bool:
    """
    Check if a lap is affected by a pit stop (in-lap or out-lap).
    """
    return is_out_lap(lap) or is_in_lap(lap)


def is_sc_vsc_affected(lap: pd.Series) -> bool:
    """
    Check if a lap is affected by the Safety Car or Virtual Safety Car.
    
    FastF1 TrackStatus definitions:
    '4' = Safety Car
    '6' = VSC Deployed
    '7' = VSC Ending
    """
    status = str(lap.get("TrackStatus", ""))
    # Check for any of the SC/VSC status codes anywhere in the lap's status string
    return any(code in status for code in ("4", "6", "7"))


def is_clean_lap(lap: pd.Series) -> bool:
    """
    Determine if a lap is a canonically "clean" lap suitable for pace analysis.
    
    A clean lap is defined as:
    1. Complete and accurate (native FastF1 IsAccurate flag)
    2. Not an out-lap or in-lap (pit affected)
    3. Not affected by Safety Car or Virtual Safety Car
    
    Note: Future outlier removal (e.g., traffic, mistakes) belongs in the EDA phase, 
    but this provides the structural baseline.
    """
    # Must be accurate according to FastF1 (e.g., complete racing lap without major anomalies)
    is_accurate = lap.get("IsAccurate", False)
    if not isinstance(is_accurate, bool) and pd.isna(is_accurate):
        is_accurate = False
        
    return bool(
        is_accurate
        and not is_pit_lap(lap)
        and not is_sc_vsc_affected(lap)
    )
