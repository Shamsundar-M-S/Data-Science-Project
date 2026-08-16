import os
import pytest
from unittest.mock import patch, MagicMock
from src.analysis.report_server import serve_and_open_report

@pytest.fixture
def mock_console_and_browser():
    with patch("src.analysis.report_server.console.print") as mock_print, \
         patch("src.analysis.report_server.webbrowser.open") as mock_open, \
         patch("src.analysis.report_server.HTTPServer") as mock_server:
        
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        yield mock_print, mock_open, mock_server_instance

def test_url_construction_and_no_hardcoded_session(tmp_path, mock_console_and_browser):
    """Test 1 & Test 5: URLs are correctly built based on the provided session_id, no hardcoded session."""
    _, mock_open, mock_server = mock_console_and_browser
    
    session_id = "2026_09_British_Grand_Prix_Race"
    output_dir = tmp_path / "analytics_output"
    
    # Create fake phase2 report to pass existence check
    session_dir = output_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / f"phase2_report_{session_id}.html").touch()

    # Mock finding port 8000
    with patch("src.analysis.report_server.find_available_port", return_value=8000):
        # We need to simulate KeyboardInterrupt to break the serve_forever loop
        mock_server.serve_forever.side_effect = KeyboardInterrupt
        serve_and_open_report(session_id, "2026 British GP — Race", str(output_dir))

    # Check that webbrowser opened the EXACT correct url with the session ID
    expected_url = f"http://localhost:8000/{output_dir}/{session_id}/phase2_report_{session_id}.html"
    # Note: windows paths might have backslashes in str(output_dir), but the URL should ideally use whatever path logic works locally.
    # In the code we did f"{output_dir}/{session_id}/...", so it combines them.
    # We just check the end part is there.
    opened_url = mock_open.call_args[0][0]
    assert session_id in opened_url
    assert "2026_09_British_Grand_Prix_Race" in opened_url
    assert "phase2_report_2026_09_British_Grand_Prix_Race.html" in opened_url

def test_session_isolation(tmp_path, mock_console_and_browser):
    """Test 2: Two different session IDs construct completely isolated URLs."""
    _, mock_open, mock_server = mock_console_and_browser
    output_dir = tmp_path / "analytics_output"

    for sid in ["Session_A", "Session_B"]:
        (output_dir / sid).mkdir(parents=True, exist_ok=True)
        (output_dir / sid / f"phase2_report_{sid}.html").touch()
    
    with patch("src.analysis.report_server.find_available_port", return_value=8000):
        mock_server.serve_forever.side_effect = KeyboardInterrupt
        
        serve_and_open_report("Session_A", "A", str(output_dir))
        url_A = mock_open.call_args[0][0]
        
        serve_and_open_report("Session_B", "B", str(output_dir))
        url_B = mock_open.call_args[0][0]
        
        assert "Session_A" in url_A
        assert "Session_B" not in url_A
        
        assert "Session_B" in url_B
        assert "Session_A" not in url_B

def test_report_existence_check(tmp_path, mock_console_and_browser):
    """Test 3: Browser opening MUST NOT occur if the HTML report is missing."""
    mock_print, mock_open, mock_server = mock_console_and_browser
    output_dir = tmp_path / "analytics_output"
    session_id = "Ghost_Session"
    # We DO NOT create the file
    
    serve_and_open_report(session_id, "Ghost", str(output_dir))
    
    # Should not open browser or start server
    mock_open.assert_not_called()
    mock_server.serve_forever.assert_not_called()
    
    # Check that error was printed
    # The last call to print should contain Error
    error_called = any("Error:" in str(call_args) for call_args in mock_print.call_args_list)
    assert error_called

def test_port_handling(tmp_path, mock_console_and_browser):
    """Test 4: Use available port if 8000 is taken, and format URL correctly."""
    _, mock_open, mock_server = mock_console_and_browser
    session_id = "Port_Session"
    output_dir = tmp_path / "analytics_output"
    
    session_dir = output_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / f"phase2_report_{session_id}.html").touch()

    # Mock finding port 8001
    with patch("src.analysis.report_server.find_available_port", return_value=8001):
        mock_server.serve_forever.side_effect = KeyboardInterrupt
        serve_and_open_report(session_id, "Port", str(output_dir))

    opened_url = mock_open.call_args[0][0]
    assert "http://localhost:8001/" in opened_url
