import os
from typing import Dict, Any

import pandas as pd
import fastf1

from src.analysis.clean_laps import is_clean_lap


def _get_session_id(session: fastf1.core.Session) -> str:
    """Generate a deterministic session identifier."""
    # FastF1 session exposes event properties
    event_name = str(session.event.EventName).replace(" ", "_")
    return f"{session.event.year}_{session.event.RoundNumber:02d}_{event_name}_{session.name.replace(' ', '_')}"


def export_lap_data(session: fastf1.core.Session, export_dir: str = "analytics_data") -> str:
    """
    Extract lap data, merge with weather, apply clean-lap rules, and export to Parquet.
    """
    os.makedirs(export_dir, exist_ok=True)
    session_id = _get_session_id(session)
    
    # Get base laps and weather
    # get_weather_data() magically aligns weather samples to each lap
    laps = session.laps
    if laps.empty:
        raise ValueError(f"No lap data found for session {session_id}")
        
    weather = laps.get_weather_data()
    
    # Reset index to allow merging without duplicate index errors
    laps_reset = laps.reset_index(drop=True)
    
    # Drop Time from weather to prevent duplicate columns
    if "Time" in weather.columns and "Time" in laps.columns:
        weather = weather.drop(columns=["Time"])
        
    weather_reset = weather.reset_index(drop=True)
    
    # Concat column-wise:
    df = pd.DataFrame(pd.concat([laps_reset, weather_reset], axis=1))
    
    # Add our canonical clean lap flag
    df["is_clean_lap"] = df.apply(is_clean_lap, axis=1)
    
    # Add metadata columns
    df["session_id"] = session_id
    df["season"] = session.event.year
    df["round"] = session.event.RoundNumber
    df["event"] = session.event.EventName
    df["session_type"] = session.name
    
    # Normalize some columns if necessary (like Timedeltas to seconds for Parquet compatibility)
    timedelta_cols = df.select_dtypes(include=['timedelta64[ns]']).columns
    for col in timedelta_cols:
        # Convert to seconds as float
        df[col + "_s"] = df[col].dt.total_seconds()
        df = df.drop(columns=[col])
        
    output_path = os.path.join(export_dir, f"{session_id}_laps.parquet")
    df.to_parquet(output_path, engine="pyarrow", index=False)
    return output_path


def export_telemetry_data(session: fastf1.core.Session, export_dir: str = "analytics_data") -> str:
    """
    Extract raw telemetry for all drivers, flatten into a single dataframe, and export.
    """
    os.makedirs(export_dir, exist_ok=True)
    session_id = _get_session_id(session)
    
    all_telemetry = []
    
    for driver_no in session.drivers:
        laps_driver = session.laps.pick_drivers(driver_no)
        if laps_driver.empty:
            continue
            
        driver_code = session.get_driver(driver_no)["Abbreviation"]
        
        for _, lap in laps_driver.iterlaps():
            try:
                # Get raw telemetry for the lap
                tel = lap.get_telemetry()
            except Exception:
                continue
                
            if tel.empty:
                continue
                
            # Keep only relevant columns to avoid bloat
            keep_cols = ["SessionTime", "Distance", "Speed", "nGear", "Throttle", "Brake", "DRS", "X", "Y"]
            existing_cols = [c for c in keep_cols if c in tel.columns]
            
            tel_sub = tel[existing_cols].copy()
            
            # Add identifiers
            tel_sub["session_id"] = session_id
            tel_sub["driver_number"] = driver_no
            tel_sub["driver_code"] = driver_code
            tel_sub["lap_number"] = lap.LapNumber
            
            all_telemetry.append(tel_sub)
            
    if not all_telemetry:
        raise ValueError(f"No telemetry data could be extracted for session {session_id}")
        
    df_tel = pd.concat(all_telemetry, ignore_index=True)
    
    # Convert timedelta to seconds
    if "SessionTime" in df_tel.columns and pd.api.types.is_timedelta64_dtype(df_tel["SessionTime"]):
        df_tel["SessionTime_s"] = df_tel["SessionTime"].dt.total_seconds()
        df_tel = df_tel.drop(columns=["SessionTime"])
        
    output_path = os.path.join(export_dir, f"{session_id}_telemetry.parquet")
    df_tel.to_parquet(output_path, engine="pyarrow", index=False)
    return output_path


def validate_export(parquet_path: str) -> Dict[str, Any]:
    """
    Lightweight validation/reporting mechanism for exported data.
    """
    if not os.path.exists(parquet_path):
        return {"error": "File does not exist"}
        
    df = pd.read_parquet(parquet_path, engine="pyarrow")
    
    report = {
        "row_count": len(df),
        "columns": list(df.columns),
    }
    
    if "DriverNumber" in df.columns:
        report["drivers_count"] = df["DriverNumber"].nunique()
    elif "driver_number" in df.columns:
        report["drivers_count"] = df["driver_number"].nunique()
        
    if "LapNumber" in df.columns:
        report["max_laps"] = int(df["LapNumber"].max()) if not df.empty else 0
        
    if "Compound" in df.columns:
        report["unique_compounds"] = df["Compound"].dropna().unique().tolist()
        
    if "is_clean_lap" in df.columns:
        report["clean_lap_count"] = int(df["is_clean_lap"].sum())
        report["excluded_lap_count"] = len(df) - report["clean_lap_count"]
        
    if "session_id" in df.columns:
        report["session_id"] = str(df["session_id"].iloc[0]) if not df.empty else None
        
    # Missing values count per column
    report["missing_values"] = df.isna().sum().to_dict()
    
    return report
