import sys
import os

from src.f1_data import load_session
from src.analysis.export import export_lap_data, export_telemetry_data, _get_session_id
from src.analysis.run_phase1 import run_phase1_analysis
from src.analysis.run_phase2 import run_phase2
from src.analysis.run_phase3 import run_phase3
from src.analysis.run_phase4 import run_phase4

def verify_2018():
    session = load_session(2018, 8, "R")
    session_id = _get_session_id(session)
    print(f"Loaded session: {session_id}")
    
    OUTPUT_DIR = "analytics_data"
    export_lap_data(session, export_dir=OUTPUT_DIR)
    export_telemetry_data(session, export_dir=OUTPUT_DIR)
    
    print("Running Phase 1")
    run_phase1_analysis(session_id, OUTPUT_DIR, "analytics_output")
    print("Running Phase 2")
    run_phase2(session_id, OUTPUT_DIR, "analytics_output")
    print("Running Phase 3")
    run_phase3(session_id, OUTPUT_DIR, "analytics_output")
    print("Running Phase 4")
    run_phase4(session_id, OUTPUT_DIR, "analytics_output")
    print("ALL PHASES COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    verify_2018()
