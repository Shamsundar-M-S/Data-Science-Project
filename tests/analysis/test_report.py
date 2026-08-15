import os
from src.analysis.report import generate_html_report

def test_generate_html_report(tmp_path):
    output_dir = str(tmp_path)
    report_path = os.path.join(output_dir, "phase1_report.html")
    
    # Run the generator with empty directory (simulating missing files, should not crash)
    generate_html_report(output_dir)
    
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "FORMULA 1 DATA SCIENCE ANALYSIS" in content
        assert "2023 Bahrain Grand Prix" in content
