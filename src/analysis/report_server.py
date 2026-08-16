import os
import sys
import webbrowser
import socket
import glob
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from rich.console import Console

console = Console()

def find_available_port(start_port=8000, max_port=8050):
    """Find an available localhost port."""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return None

def serve_and_open_report(session_id: str, session_title: str, output_dir="analytics_output"):
    """
    Start a local HTTP server and open the Phase 2 report in the browser.
    Blocks until interrupted by the user (Ctrl+C).
    """
    def extract_phase_num(filepath):
        basename = os.path.basename(filepath)
        match = re.search(r'phase(\d+)_report', basename)
        return int(match.group(1)) if match else 0
        
    # Dynamically find all phase reports
    search_pattern = f"{output_dir}/{session_id}/phase*_report_{session_id}.html"
    discovered_reports = sorted(glob.glob(search_pattern), key=extract_phase_num)
    
    if not discovered_reports:
        console.print(f"[bold red]Error:[/bold red] Required reports do not exist.")
        return

    # Use the highest numbered phase as the primary report to open
    primary_html = discovered_reports[-1].replace("\\", "/")

    port = find_available_port()
    if not port:
        console.print("[bold red]Error:[/bold red] Could not find an available port to start the report server.")
        return

    server_url = f"http://localhost:{port}/"
    primary_url = f"http://localhost:{port}/{primary_html}"

    console.print("\n============================================================")
    console.print("ANALYSIS COMPLETE")
    console.print("============================================================\n")
    console.print("Session:")
    console.print(f"{session_title}\n")
    
    for report_path in discovered_reports:
        report_path = report_path.replace("\\", "/")
        # Extract "Phase X" from "phaseX_report_..."
        filename = os.path.basename(report_path)
        phase_str = filename.split("_report_")[0].capitalize().replace("Phase", "Phase ")
        report_url = f"http://localhost:{port}/{report_path}"
        console.print(f"{phase_str} Report:")
        console.print(f"{report_url}\n")

    if port != 8000:
        console.print(f"Preferred port 8000 unavailable.\nUsing available port {port}.\n")

    primary_filename = os.path.basename(primary_html)
    primary_phase_str = primary_filename.split("_report_")[0].capitalize().replace("Phase", "Phase ")
    
    console.print("Starting local report server...\n")
    console.print("Report server:")
    console.print(f"{server_url}\n")
    console.print(f"Opening {primary_phase_str} report in your browser...\n")
    
    console.print("============================================================")
    console.print("LOCAL REPORT SERVER RUNNING")
    console.print("============================================================\n")
    console.print("Server:")
    console.print(f"{server_url}\n")
    
    for report_path in discovered_reports:
        report_path = report_path.replace("\\", "/")
        filename = os.path.basename(report_path)
        phase_str = filename.split("_report_")[0].capitalize().replace("Phase", "Phase ")
        report_url = f"http://localhost:{port}/{report_path}"
        console.print(f"{phase_str}:")
        console.print(f"{report_url}\n")
        
    console.print(f"Browser:\n{primary_phase_str} report opened automatically.\n")
    console.print("Press Ctrl+C to stop the report server.")
    console.print("============================================================")

    webbrowser.open(primary_url)

    # Use the project root as the handler's directory
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress default HTTP logging to keep terminal clean

    httpd = HTTPServer(('localhost', port), QuietHandler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Stopping report server...[/bold yellow]")
        httpd.server_close()
