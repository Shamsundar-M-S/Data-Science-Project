import fastf1
from src.analysis.export import export_lap_data, export_telemetry_data, validate_export

if __name__ == "__main__":
    fastf1.Cache.enable_cache("cache")
    session = fastf1.get_session(2023, 1, 'FP1')
    session.load(telemetry=True, weather=True)
    
    print("Exporting lap data...")
    laps_path = export_lap_data(session)
    print("Laps exported to:", laps_path)
    print("Lap Validation:", validate_export(laps_path))
    
    print("Exporting telemetry data...")
    tel_path = export_telemetry_data(session)
    print("Telemetry exported to:", tel_path)
    print("Tel Validation:", validate_export(tel_path))
