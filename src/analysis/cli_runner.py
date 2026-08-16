import os
import sys
from questionary import Style, select, Choice
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.lib.season import get_season
from src.f1_data import get_race_weekends_by_year, load_session
from src.analysis.export import export_lap_data, export_telemetry_data, _get_session_id
from src.analysis.run_phase1 import run_phase1_analysis
from src.analysis.run_phase2 import run_phase2
from src.analysis.report_server import serve_and_open_report

def main():
    current_year = get_season()

    style = Style([
        ("pointer", "fg:#e10600 bold"),
        ("selected", "noinherit fg:#64eb34 bold"),
        ("highlighted", "fg:#e10600 bold"),
        ("answer", "fg:#64eb34 bold")
    ])

    console = Console()
    console.print(Markdown("# F1 Data Science Analysis 📊"))

    years = [str(year) for year in range(current_year, 2017, -1)]
    year = select("Choose a Season:", choices=years, qmark="🗓️ ", style=style).ask()
    if not year:
        sys.exit(0)
    year = int(year)

    with Progress(
        SpinnerColumn(style="bold red"),
        TextColumn("[bold]Loading races…"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("load", total=None)
        data = get_race_weekends_by_year(year)

    rounds = [Choice(title=f"{row['event_name']} ({row['date']})", value=row['round_number']) for row in data]
    round_number = select("Choose an Event:", choices=rounds, qmark="🌏", style=style).ask()
    if not round_number:
        sys.exit(0)

    # Determine available sessions for the selected round
    sessions = []
    event_name = ""
    for row in data:
        if row['round_number'] == round_number:
            event_name = row['event_name']
            if 'session_dates' in row:
                for s_name in row['session_dates'].keys():
                    sessions.append(s_name)
            else:
                sessions = ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"]
                if row['type'].find('sprint') != -1:
                    sessions = ["Practice 1", "Qualifying", "Sprint", "Race"]

    session_name = select("Choose a Session:", choices=sessions, qmark="🏁", style=style).ask()
    if not session_name:
        sys.exit(0)

    console.print(f"\n[bold green]Selected:[/bold green] {year} Round {round_number} — {session_name}\n")

    # FastF1 mapping
    session_map = {
        "Practice 1": "FP1", "Practice 2": "FP2", "Practice 3": "FP3",
        "Qualifying": "Q", "Sprint Qualifying": "SQ", "Sprint Shootout": "SS",
        "Sprint": "S", "Race": "R"
    }
    short_session = session_map.get(session_name, session_name)

    console.print("[bold yellow]Initializing FastF1 Session...[/bold yellow]")
    try:
        session = load_session(year, round_number, short_session)
    except Exception as e:
        console.print(f"[bold red]Failed to load session from FastF1:[/bold red] {e}")
        sys.exit(1)

    session_id = _get_session_id(session)
    
    OUTPUT_DIR = "analytics_data"
    laps_file = os.path.join(OUTPUT_DIR, f"{session_id}_laps.parquet")
    tel_file = os.path.join(OUTPUT_DIR, f"{session_id}_telemetry.parquet")

    if os.path.exists(laps_file) and os.path.exists(tel_file):
        console.print("[bold green]Local Dataset Found![/bold green] Using cached Parquet files.")
    else:
        console.print("[bold yellow]Local Dataset Not Found.[/bold yellow] Running Phase 0 Acquisition pipeline...")
        try:
            export_lap_data(session, export_dir=OUTPUT_DIR)
            export_telemetry_data(session, export_dir=OUTPUT_DIR)
            console.print("[bold green]Phase 0 complete.[/bold green] Dataset saved locally.")
        except Exception as e:
            console.print(f"[bold red]Data export failed:[/bold red] {e}")
            sys.exit(1)

    # Phase 1
    console.print("\n[bold cyan]--- PHASE 1: EDA & Statistics ---[/bold cyan]")
    run_phase1_analysis(session_id, OUTPUT_DIR, "analytics_output")
    
    # Phase 2
    console.print("\n[bold cyan]--- PHASE 2: Telemetry Feature Engineering ---[/bold cyan]")
    run_phase2(session_id, OUTPUT_DIR, "analytics_output")
    
    session_title = f"{year} {event_name} — {session_name}"
    serve_and_open_report(session_id, session_title, "analytics_output")

if __name__ == "__main__":
    main()
