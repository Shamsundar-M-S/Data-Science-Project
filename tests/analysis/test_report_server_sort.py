import pytest
import os
from unittest.mock import patch, MagicMock
from src.analysis.report_server import serve_and_open_report

@patch('src.analysis.report_server.glob.glob')
@patch('src.analysis.report_server.os.path.exists')
@patch('src.analysis.report_server.find_available_port')
@patch('src.analysis.report_server.webbrowser.open')
@patch('src.analysis.report_server.console.print')
@patch('src.analysis.report_server.HTTPServer')
def test_serve_and_open_report_dynamic_sort(mock_http_server, mock_print, mock_webbrowser, mock_port, mock_exists, mock_glob):
    # Mock finding an available port
    mock_port.return_value = 8001
    
    session_id = "test_session"
    output_dir = "analytics_output"
    
    # Mock glob to return files in scrambled order to test sorting
    scrambled_files = [
        f"{output_dir}/{session_id}/phase10_report_{session_id}.html",
        f"{output_dir}/{session_id}/phase2_report_{session_id}.html",
        f"{output_dir}/{session_id}/phase1_report_{session_id}.html",
        f"{output_dir}/{session_id}/phase4_report_{session_id}.html",
        f"{output_dir}/{session_id}/phase3_report_{session_id}.html"
    ]
    mock_glob.return_value = scrambled_files
    
    # Mock KeyboardInterrupt to prevent httpd from serving forever
    mock_server_instance = MagicMock()
    mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()
    mock_http_server.return_value = mock_server_instance
    
    # Run the function
    serve_and_open_report(session_id, "Test Session", output_dir)
    
    # 1 & 2. Verify sorting produced 1, 2, 3, 4, 10
    # The glob pattern should be dynamically searching for all phases
    mock_glob.assert_called_with(f"{output_dir}/{session_id}/phase*_report_{session_id}.html")
    
    # We can verify sorting by checking the print calls
    printed_lines = [call.args[0] for call in mock_print.call_args_list]
    
    # Verify the order of "Phase X:" in the "LOCAL REPORT SERVER RUNNING" section
    phase_order = []
    for line in printed_lines:
        if isinstance(line, str) and line.startswith("Phase ") and line.endswith(":") and "Report" not in line:
            phase_order.append(line)
            
    assert phase_order == ["Phase 1:", "Phase 2:", "Phase 3:", "Phase 4:", "Phase 10:"]
    
    # 3. Verify Phase 10 becomes primary_html
    # This implies webbrowser.open is called with phase 10
    mock_webbrowser.assert_called_with(f"http://localhost:8001/{output_dir}/{session_id}/phase10_report_{session_id}.html".replace("\\", "/"))
    
    # 4. URLs are generated correctly
    # Assert specific print output
    assert f"http://localhost:8001/{output_dir}/{session_id}/phase10_report_{session_id}.html".replace("\\", "/") + "\n" in printed_lines
    
    # 5. Assert no hardcoded phase logic exists
    with open("src/analysis/report_server.py", "r", encoding="utf-8") as f:
        content = f.read()
        assert "phase1_html =" not in content
        assert "phase2_html =" not in content
        assert "phase3_html =" not in content
        assert "phase4_html =" not in content
