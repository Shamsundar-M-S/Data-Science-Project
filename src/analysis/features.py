import pandas as pd
import numpy as np

def engineer_lap_features(df_laps: pd.DataFrame, df_tel: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw high-frequency telemetry into per-lap features.
    Only uses telemetry from Lap N to calculate features for Lap N.
    """
    if df_laps.empty or df_tel.empty:
        return pd.DataFrame()
        
    features = []
    
    # We iterate over laps explicitly to guarantee temporal isolation.
    
    # FastF1 telemetry DRS encoding: >= 10 is usually active/open.
    DRS_ACTIVE_THRESHOLD = 10
    THROTTLE_FULL_THRESHOLD = 99.0
    
    tel_grouped = df_tel.groupby(['driver_code', 'lap_number'])
    
    for _, lap_row in df_laps.iterrows():
        driver = lap_row['Driver']
        lap_num = lap_row['LapNumber']
        
        # Base dictionary with lap metadata
        lap_feat = {
            'Driver': driver,
            'LapNumber': lap_num,
            'LapTime_s': lap_row.get('LapTime_s', np.nan),
            'Compound': lap_row.get('Compound', None),
            'TyreLife': lap_row.get('TyreLife', np.nan),
            'TrackTemp': lap_row.get('TrackTemp', np.nan),
            'is_clean_lap': lap_row.get('is_clean_lap', False)
        }
        
        # Try to get telemetry for this specific lap
        try:
            lap_tel = tel_grouped.get_group((driver, lap_num))
        except KeyError:
            # Telemetry for this lap does not exist
            lap_feat.update({
                'telemetry_sample_count': 0,
                'distance_span': 0.0,
                'speed_max': np.nan,
                'speed_mean': np.nan,
                'speed_std': np.nan,
                'throttle_mean': np.nan,
                'throttle_full_pct': np.nan,
                'brake_active_pct': np.nan,
                'brake_events_count': 0,
                'drs_active_pct': np.nan,
                'gear_mean': np.nan,
                'gear_max': np.nan,
                'gear_8_pct': np.nan
            })
            features.append(lap_feat)
            continue
            
        n_samples = len(lap_tel)
        lap_feat['telemetry_sample_count'] = n_samples
        
        if n_samples == 0:
            features.append(lap_feat)
            continue
            
        # Distance
        lap_feat['distance_span'] = lap_tel['Distance'].max() - lap_tel['Distance'].min()
        
        # Speed
        lap_feat['speed_max'] = lap_tel['Speed'].max()
        lap_feat['speed_mean'] = lap_tel['Speed'].mean()
        lap_feat['speed_std'] = lap_tel['Speed'].std()
        
        # Throttle
        lap_feat['throttle_mean'] = lap_tel['Throttle'].mean()
        lap_feat['throttle_full_pct'] = (lap_tel['Throttle'] >= THROTTLE_FULL_THRESHOLD).mean() * 100.0
        
        # Brake
        brake_series = lap_tel['Brake'].astype(bool)
        lap_feat['brake_active_pct'] = brake_series.mean() * 100.0
        
        # Brake Events Count (contiguous blocks of True)
        # Shift the boolean series to find transitions from False to True
        brake_starts = (brake_series & ~brake_series.shift(1, fill_value=False))
        lap_feat['brake_events_count'] = int(brake_starts.sum())
        
        # DRS
        lap_feat['drs_active_pct'] = (lap_tel['DRS'] >= DRS_ACTIVE_THRESHOLD).mean() * 100.0
        
        # Gear
        lap_feat['gear_mean'] = lap_tel['nGear'].mean()
        lap_feat['gear_max'] = lap_tel['nGear'].max()
        lap_feat['gear_8_pct'] = (lap_tel['nGear'] == 8).mean() * 100.0
        
        features.append(lap_feat)
        
    df_features = pd.DataFrame(features)
    return df_features
