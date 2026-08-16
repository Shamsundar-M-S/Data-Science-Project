import os
import sys
import webbrowser
import socket
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
    phase1_html = f"{output_dir}/{session_id}/phase1_report_{session_id}.html".replace("\\", "/")
    phase2_html = f"{output_dir}/{session_id}/phase2_report_{session_id}.html".replace("\\", "/")

    # Do not start if report doesn't exist
    if not os.path.exists(phase2_html):
        console.print(f"[bold red]Error:[/bold red] Report {phase2_html} does not exist.")
        return

    port = find_available_port()
    if not port:
        console.print("[bold red]Error:[/bold red] Could not find an available port to start the report server.")
        return

    phase1_url = f"http://localhost:{port}/{phase1_html}"
    phase2_url = f"http://localhost:{port}/{phase2_html}"
    server_url = f"http://localhost:{port}/"

    console.print("\n============================================================")
    console.print("ANALYSIS COMPLETE")
    console.print("============================================================\n")
    console.print("Session:")
    console.print(f"{session_title}\n")
    console.print("Phase 1 Report:")
    console.print(f"{phase1_url}\n")
    console.print("Phase 2 Report:")
    console.print(f"{phase2_url}\n")

    if port != 8000:
        console.print(f"Preferred port 8000 unavailable.\nUsing available port {port}.\n")

    console.print("Starting local report server...\n")
    console.print("Report server:")
    console.print(f"{server_url}\n")
    console.print("Opening Phase 2 report in your browser...\n")
    console.print("============================================================")
    console.print("LOCAL REPORT SERVER RUNNING")
    console.print("============================================================\n")
    console.print("Server:")
    console.print(f"{server_url}\n")
    console.print("Phase 1:")
    console.print(f"{phase1_url}\n")
    console.print("Phase 2:")
    console.print(f"{phase2_url}\n")
    console.print("Browser:\nPhase 2 report opened automatically.\n")
    console.print("Press Ctrl+C to stop the report server.")
    console.print("============================================================\n")

    webbrowser.open(phase2_url)

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
