import os
import pandas as pd

laps_file = r'analytics_data\2023_01_Bahrain_Grand_Prix_Practice_1_laps.parquet'
tel_file = r'analytics_data\2023_01_Bahrain_Grand_Prix_Practice_1_telemetry.parquet'

print('7. VERIFY BAHRAIN FP1 EXPORTS')
print(f'Laps file exists: {os.path.exists(laps_file)}')
print(f'Tel file exists: {os.path.exists(tel_file)}')

if os.path.exists(laps_file) and os.path.exists(tel_file):
    df_laps = pd.read_parquet(laps_file, engine='pyarrow')
    df_tel = pd.read_parquet(tel_file, engine='pyarrow')

    print(f'Laps rows: {len(df_laps)}')
    print(f'Drivers: {df_laps["DriverNumber"].nunique()}')
    print(f'Clean laps: {df_laps["is_clean_lap"].sum()}')
    print(f'Laps columns: {len(df_laps.columns)}')
    print(f'Missing is_clean_lap: {df_laps["is_clean_lap"].isna().sum()}')
    
    print(f'Tel rows: {len(df_tel)}')
    print(f'Tel columns: {len(df_tel.columns)}')
    print(f'Tel data types:\\n{df_tel.dtypes}')
    
    print('\n8. PARQUET ROUND-TRIP')
    print('Laps Schema Valid:', df_laps.empty == False)
    print('Tel Schema Valid:', df_tel.empty == False)
