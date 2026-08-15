import os
import tempfile
import pandas as pd
import pytest

from src.analysis.export import (
    _get_session_id,
    export_lap_data,
    export_telemetry_data,
    validate_export,
)


class MockEvent:
    def __init__(self):
        self.year = 2023
        self.RoundNumber = 1
        self.EventName = "Bahrain Grand Prix"


class MockSession:
    def __init__(self, empty_laps=False, empty_tel=False):
        self.event = MockEvent()
        self.name = "Practice 1"
        self.api_path = "mock_api_path"
        
        self._empty_laps = empty_laps
        self._empty_tel = empty_tel
        
        self.drivers = ["1"]
        
    @property
    def laps(self):
        if self._empty_laps:
            return MockLaps(pd.DataFrame())
            
        df = pd.DataFrame({
            "Time": [pd.Timedelta(seconds=100)],
            "DriverNumber": ["1"],
            "LapTime": [pd.Timedelta(seconds=90)],
            "LapNumber": [1],
            "Compound": ["SOFT"],
            "IsAccurate": [True],
            "PitOutTime": [pd.NaT],
            "PitInTime": [pd.NaT],
            "TrackStatus": ["1"],
        })
        return MockLaps(df, self._empty_tel)
        
    def get_driver(self, driver_no):
        return {"Abbreviation": "VER"}


class MockLaps(pd.DataFrame):
    def __init__(self, data, empty_tel=False):
        super().__init__(data)
        self._empty_tel = empty_tel
        
    def get_weather_data(self):
        if self.empty:
            return pd.DataFrame()
        return pd.DataFrame({
            "AirTemp": [25.0],
            "TrackTemp": [35.0],
            "Humidity": [40.0],
        })
        
    def pick_drivers(self, driver_no):
        sliced = self[self["DriverNumber"] == driver_no]
        return MockLaps(sliced, self._empty_tel)
        
    def iterlaps(self):
        for idx, row in self.iterrows():
            yield idx, MockLapRow(row, self._empty_tel)


class MockLapRow(pd.Series):
    def __init__(self, data, empty_tel=False):
        super().__init__(data)
        self._empty_tel = empty_tel
        
    def get_telemetry(self):
        if self._empty_tel:
            return pd.DataFrame()
        return pd.DataFrame({
            "SessionTime": [pd.Timedelta(seconds=100), pd.Timedelta(seconds=101)],
            "Distance": [10.0, 50.0],
            "Speed": [100.0, 200.0],
            "nGear": [3, 5],
            "Throttle": [100, 100],
            "Brake": [0, 0],
            "DRS": [0, 0],
            "X": [1000, 2000],
            "Y": [1000, 2000]
        })


def test_get_session_id():
    session = MockSession()
    session_id = _get_session_id(session)
    assert session_id == "2023_01_Bahrain_Grand_Prix_Practice_1"


def test_export_lap_data():
    session = MockSession()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = export_lap_data(session, export_dir=tmpdir)
        
        assert os.path.exists(output_path)
        
        # Verify schema
        df = pd.read_parquet(output_path, engine="pyarrow")
        assert len(df) == 1
        assert "is_clean_lap" in df.columns
        assert bool(df["is_clean_lap"].iloc[0]) is True
        assert "AirTemp" in df.columns
        assert df["session_id"].iloc[0] == "2023_01_Bahrain_Grand_Prix_Practice_1"
        assert "Time" not in df.columns  # Transformed to Time_s
        assert "Time_s" in df.columns


def test_export_lap_data_empty():
    session = MockSession(empty_laps=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="No lap data found"):
            export_lap_data(session, export_dir=tmpdir)


def test_export_telemetry_data():
    session = MockSession()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = export_telemetry_data(session, export_dir=tmpdir)
        
        assert os.path.exists(output_path)
        
        df = pd.read_parquet(output_path, engine="pyarrow")
        assert len(df) == 2
        assert "SessionTime_s" in df.columns
        assert "Speed" in df.columns
        assert "driver_code" in df.columns
        assert df["driver_code"].iloc[0] == "VER"


def test_export_telemetry_data_empty():
    session = MockSession(empty_tel=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="No telemetry data could be extracted"):
            export_telemetry_data(session, export_dir=tmpdir)


def test_validate_export():
    session = MockSession()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = export_lap_data(session, export_dir=tmpdir)
        
        report = validate_export(output_path)
        assert report["row_count"] == 1
        assert report["drivers_count"] == 1
        assert report["max_laps"] == 1
        assert "SOFT" in report["unique_compounds"]
        assert report["clean_lap_count"] == 1
        assert report["session_id"] == "2023_01_Bahrain_Grand_Prix_Practice_1"
        assert "missing_values" in report
