import os
from src.analysis.report import generate_html_report

def test_generate_html_report(tmp_path):
    output_dir = str(tmp_path)
    session_id = "test_session_isolated"
    session_metadata = {"season": "2024", "event": "Monaco Grand Prix", "session_type": "Qualifying"}
    report_path = os.path.join(output_dir, f"phase1_report_{session_id}.html")
    
    # Run the generator with empty directory (simulating missing files, should not crash)
    generate_html_report(output_dir, session_metadata, session_id)
    
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "FORMULA 1 DATA SCIENCE ANALYSIS" in content
        assert "2024 Monaco Grand Prix" in content
        assert "Qualifying" in content
        assert session_id in content
