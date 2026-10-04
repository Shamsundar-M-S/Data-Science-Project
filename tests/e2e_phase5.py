import os
import glob
import re
import pytest
import pandas as pd

from src.analysis.run_phase1 import run_phase1_analysis
from src.analysis.run_phase2 import run_phase2
from src.analysis.run_phase3 import run_phase3
from src.analysis.run_phase4 import run_phase4
from src.analysis.run_phase5 import run_phase5


def test_e2e_phase1_to_phase5_pipeline(tmp_path):
    data_dir = os.path.join(tmp_path, "analytics_data")
    output_dir = os.path.join(tmp_path, "analytics_output")
    session_id = "2024_01_Bahrain_Grand_Prix_Race"

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Create realistic mock laps and telemetry datasets (Phase 0 output simulation)
    laps_data = []
    drivers = ["VER", "PER", "SAI", "LEC", "NOR"]
    teams = ["Red Bull Racing", "Red Bull Racing", "Ferrari", "Ferrari", "McLaren"]

    for lap_num in range(1, 15):
        for idx, (drv, team) in enumerate(zip(drivers, teams)):
            laps_data.append({
                "session_id": session_id,
                "season": 2024,
                "round": 1,
                "event": "Bahrain Grand Prix",
                "session_type": "Race",
                "Driver": drv,
                "driver_code": drv,
                "Team": team,
                "LapNumber": lap_num,
                "LapTime_s": 90.0 + idx * 0.5 + (lap_num * 0.05),
                "Compound": "MEDIUM" if lap_num <= 7 else "HARD",
                "TyreLife": lap_num if lap_num <= 7 else lap_num - 7,
                "Stint": 1 if lap_num <= 7 else 2,
                "is_clean_lap": True,
                "GridPosition": idx + 1,
                "Position": idx + 1,
                "TrackTemp": 30.0,
                "AirTemp": 22.0
            })

    df_laps = pd.DataFrame(laps_data)
    df_laps.to_parquet(os.path.join(data_dir, f"{session_id}_laps.parquet"), index=False)

    # Mock telemetry
    tel_data = []
    for lap_num in range(1, 15):
        for drv in drivers:
            for s in range(50):
                tel_data.append({
                    "session_id": session_id,
                    "driver_code": drv,
                    "driver_number": 1,
                    "lap_number": lap_num,
                    "SessionTime_s": s * 0.1,
                    "Speed": 250.0 + (s % 10),
                    "nGear": 7,
                    "Throttle": 100.0,
                    "Brake": 0.0,
                    "DRS": 0,
                    "X": 100.0 + s,
                    "Y": 200.0 + s
                })
    df_tel = pd.DataFrame(tel_data)
    df_tel.to_parquet(os.path.join(data_dir, f"{session_id}_telemetry.parquet"), index=False)

    # 2. Run Phase 1 to Phase 5
    run_phase1_analysis(session_id, data_dir, output_dir)
    run_phase2(session_id, data_dir, output_dir)
    run_phase3(session_id, data_dir, output_dir)
    run_phase4(session_id, data_dir, output_dir)
    run_phase5(session_id, data_dir, output_dir)

    # 3. Verify all phase reports are created
    session_out_dir = os.path.join(output_dir, session_id)
    assert os.path.exists(session_out_dir)

    expected_reports = [
        f"phase1_report_{session_id}.html",
        f"phase2_report_{session_id}.html",
        f"phase3_report_{session_id}.html",
        f"phase4_report_{session_id}.html",
        f"phase5_report_{session_id}.html"
    ]

    for rep in expected_reports:
        assert os.path.exists(os.path.join(session_out_dir, rep)), f"Missing expected report: {rep}"

    # 4. Verify numerical sorting discovery logic used by report_server.py
    def extract_phase_num(filepath):
        basename = os.path.basename(filepath)
        match = re.search(r'phase(\d+)_report', basename)
        return int(match.group(1)) if match else 0

    search_pattern = f"{output_dir}/{session_id}/phase*_report_{session_id}.html"
    discovered_reports = sorted(glob.glob(search_pattern), key=extract_phase_num)

    assert len(discovered_reports) == 5
    primary_html = discovered_reports[-1]
    assert "phase5_report" in os.path.basename(primary_html), f"Highest phase should be Phase 5, got {primary_html}"
