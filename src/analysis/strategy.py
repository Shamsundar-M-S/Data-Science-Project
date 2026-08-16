import pandas as pd
import numpy as np

def analyze_tyre_degradation(df_laps: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate observed lap-time degradation per tyre life per stint.
    Requires is_clean_lap == True, LapTime_s, TyreLife, Compound.
    """
    if df_laps.empty or 'is_clean_lap' not in df_laps.columns:
        return pd.DataFrame()
        
    df = df_laps[df_laps['is_clean_lap'] == True].copy()
    req_cols = ['LapTime_s', 'TyreLife', 'Compound', 'Driver', 'Stint']
    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        return pd.DataFrame()
        
    df = df.dropna(subset=req_cols)
    
    results = []
    
    for compound, comp_group in df.groupby('Compound'):
        for (driver, stint), group in comp_group.groupby(['Driver', 'Stint']):
            if len(group) < 3:
                continue
                
            x = group['TyreLife'].values
            y = group['LapTime_s'].values
            
            if np.var(x) == 0:
                continue
                
            # Simple linear regression to estimate slope
            slope, intercept = np.polyfit(x, y, 1)
            
            results.append({
                'Compound': compound,
                'Driver': driver,
                'Stint': stint,
                'clean_laps': len(group),
                'median_lap_time': np.median(y),
                'mean_lap_time': np.mean(y),
                'tyre_life_start': x.min(),
                'tyre_life_end': x.max(),
                'degradation_s_per_lap': slope
            })
            
    return pd.DataFrame(results)

def analyze_stints(df_laps: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze stint-level statistics.
    """
    req_cols = ['Driver', 'Stint', 'Compound', 'TyreLife', 'LapNumber', 'is_clean_lap']
    missing = [c for c in req_cols if c not in df_laps.columns]
    if missing or df_laps.empty:
        return pd.DataFrame()
        
    # We include all laps to get true stint bounds, but calculate pace on clean laps
    results = []
    
    for (driver, stint), group in df_laps.groupby(['Driver', 'Stint']):
        if pd.isna(stint):
            continue
            
        group = group.dropna(subset=['Compound', 'TyreLife', 'LapNumber'])
        if group.empty:
            continue
            
        compound = group['Compound'].iloc[0]
        stint_length = len(group)
        tyre_life_start = group['TyreLife'].min()
        tyre_life_end = group['TyreLife'].max()
        
        clean_group = group[group['is_clean_lap'] == True]
        
        if not clean_group.empty and 'LapTime_s' in clean_group.columns:
            clean_laps_count = len(clean_group.dropna(subset=['LapTime_s']))
            if clean_laps_count > 0:
                median_pace = clean_group['LapTime_s'].median()
                mean_pace = clean_group['LapTime_s'].mean()
                best_lap = clean_group['LapTime_s'].min()
            else:
                median_pace, mean_pace, best_lap = np.nan, np.nan, np.nan
        else:
            clean_laps_count = 0
            median_pace, mean_pace, best_lap = np.nan, np.nan, np.nan
            
        results.append({
            'Driver': driver,
            'Stint': stint,
            'Compound': compound,
            'stint_length': stint_length,
            'tyre_life_start': tyre_life_start,
            'tyre_life_end': tyre_life_end,
            'clean_laps_count': clean_laps_count,
            'median_pace': median_pace,
            'mean_pace': mean_pace,
            'best_lap': best_lap
        })
        
    return pd.DataFrame(results)

def analyze_driver_pace(df_laps: pd.DataFrame) -> pd.DataFrame:
    """
    Returns clean laps with relevant columns for driver pace evolution analysis.
    """
    if df_laps.empty or 'is_clean_lap' not in df_laps.columns:
        return pd.DataFrame()
        
    df = df_laps[df_laps['is_clean_lap'] == True].copy()
    req_cols = ['Driver', 'LapNumber', 'LapTime_s', 'TyreLife', 'Compound']
    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        return pd.DataFrame()
        
    return df.dropna(subset=req_cols)[req_cols]

def analyze_strategy_timeline(df_laps: pd.DataFrame) -> pd.DataFrame:
    """
    Extract compound usage timeline for each driver (primarily for Race sessions).
    """
    req_cols = ['Driver', 'Stint', 'Compound', 'LapNumber']
    missing = [c for c in req_cols if c not in df_laps.columns]
    if missing or df_laps.empty:
        return pd.DataFrame()
        
    results = []
    
    for driver, group in df_laps.groupby('Driver'):
        group = group.dropna(subset=req_cols)
        
        for stint, stint_group in group.groupby('Stint'):
            if stint_group.empty:
                continue
                
            compound = stint_group['Compound'].iloc[0]
            start_lap = stint_group['LapNumber'].min()
            end_lap = stint_group['LapNumber'].max()
            
            results.append({
                'Driver': driver,
                'Stint': stint,
                'Compound': compound,
                'start_lap': start_lap,
                'end_lap': end_lap
            })
            
    return pd.DataFrame(results)
