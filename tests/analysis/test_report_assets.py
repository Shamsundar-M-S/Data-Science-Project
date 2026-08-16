import os
import re
import pytest
from src.analysis.report_phase2 import generate_phase2_report

def test_phase2_report_assets(tmp_path):
    """Verify that Phase 2 report generates valid, relative image paths that actually exist."""
    session_id = "test_session_2026"
    output_dir = tmp_path / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create fake image files to satisfy the test
    expected_images = [
        "dist_speed_mean.png",
        "scatter_speed_mean_vs_laptime.png",
        "dist_throttle_full_pct.png",
        "scatter_throttle_full_pct_vs_laptime.png",
        "dist_brake_active_pct.png",
        "scatter_brake_active_pct_vs_laptime.png",
        "dist_drs_active_pct.png",
        "dist_gear_mean.png",
        "feature_correlation.png"
    ]
    for img in expected_images:
        (output_dir / img).touch()
        
    generate_phase2_report(str(output_dir), {"season": "2026", "event": "Test GP", "session_type": "Race"}, session_id)
    
    html_path = output_dir / f"phase2_report_{session_id}.html"
    assert html_path.exists()
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # Extract all <img src="...">
    img_tags = re.findall(r'<img[^>]+src="([^"]+)"', html_content)
    assert len(img_tags) == len(expected_images)
    
    for src in img_tags:
        # No absolute paths
        assert not os.path.isabs(src), f"Absolute path found: {src}"
        assert not src.startswith("C:\\") and not src.startswith("/")
        
        # No Windows backslashes
        assert "\\" not in src, f"Windows backslash found: {src}"
        
        # Path stays inside the session output directory (it should just be the filename)
        assert "/" not in src and ".." not in src, f"Path escapes directory: {src}"
        
        # File must exist
        assert (output_dir / src).exists(), f"Image {src} referenced in HTML does not exist."
        
def test_phase2_report_asset_isolation(tmp_path):
    """Verify isolation between multiple session reports."""
    session_A = "Session_A"
    session_B = "Session_B"
    
    dir_A = tmp_path / session_A
    dir_B = tmp_path / session_B
    dir_A.mkdir(parents=True)
    dir_B.mkdir(parents=True)
    
    generate_phase2_report(str(dir_A), {}, session_A)
    generate_phase2_report(str(dir_B), {}, session_B)
    
    # Just generating should not cause session B to be referenced in session A
    with open(dir_A / f"phase2_report_{session_A}.html", "r", encoding="utf-8") as f:
        html_A = f.read()
        assert session_B not in html_A
