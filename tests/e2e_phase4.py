from src.analysis.run_phase1 import run_phase1_analysis
from src.analysis.run_phase2 import run_phase2
from src.analysis.run_phase3 import run_phase3
from src.analysis.run_phase4 import run_phase4
from src.analysis.report_server import serve_and_open_report
from unittest.mock import patch
import os

sessions = [
    "2026_09_British_Grand_Prix_Race",
    "2023_01_Bahrain_Grand_Prix_Practice_1",
    "2023_02_Saudi_Arabian_Grand_Prix_Practice_1"
]
out_dir = "analytics_output"

for session_id in sessions:
    print(f"\n--- Running for {session_id} ---")
    data_dir = "analytics_data"
    
    # Check if dataset exists, otherwise skip
    laps_file = os.path.join(data_dir, f"{session_id}_laps.parquet")
    if not os.path.exists(laps_file):
        print(f"Skipping {session_id} (data not found)")
        continue
        
    print(f"Running Phase 1 for {session_id}...")
    run_phase1_analysis(session_id, data_dir, out_dir)

    print(f"Running Phase 2 for {session_id}...")
    run_phase2(session_id, data_dir, out_dir)

    print(f"Running Phase 3 for {session_id}...")
    run_phase3(session_id, data_dir, out_dir)
    
    print(f"Running Phase 4 for {session_id}...")
    run_phase4(session_id, data_dir, out_dir)
    
    # Verify HTML exists
    phase4_html = os.path.join(out_dir, session_id, f"phase4_report_{session_id}.html")
    assert os.path.exists(phase4_html), f"HTML report missing for {session_id}"

print("Multi-session Test complete!")
