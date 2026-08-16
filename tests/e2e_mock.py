import sys
from unittest.mock import patch
from src.analysis.cli_runner import main

# Mock choices: 2026 -> British Grand Prix -> Race
def mock_ask(self):
    if "Season" in self.message:
        return "2026"
    elif "Event" in self.message:
        # For 2026, British Grand Prix is round 9
        return 9
    elif "Session" in self.message:
        return "Race"
    return None

with patch("questionary.select") as mock_select:
    mock_instance = mock_select.return_value
    mock_instance.ask.side_effect = lambda: mock_ask(mock_select.call_args[1])
    
    # We also need to patch webbrowser.open so it doesn't try to open a real GUI
    # But wait, we WANT to test if it starts the server. The server will block forever.
    # We'll patch serve_forever to just return after 1 second, or we can just kill it.
    with patch("webbrowser.open") as mock_webbrowser:
        with patch("src.analysis.report_server.HTTPServer.serve_forever", side_effect=KeyboardInterrupt):
            try:
                main()
            except SystemExit:
                pass
            print("E2E Test complete!")
