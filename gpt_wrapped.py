"""
gpt_wrapped.py - CLI orchestrator for GPT Wrapped.

Analyzes a ChatGPT data export ZIP file and generates a Spotify-Wrapped-style
yearly HTML report 100% locally and privately.

Usage:
    python gpt_wrapped.py [export.zip] [--year YYYY] [--output DIR] [--no-browser]
"""

import argparse
import logging
from pathlib import Path
import sys
import webbrowser

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from analyzer import analyze_export
from parser import parse_export_zip
from report import render_html_report

import logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger("gpt_wrapped")


def prompt_for_zip_path() -> str:
    """Prompt the user interactively if no zip path was passed via CLI."""
    print("=" * 60)
    print("  WELCOME TO GPT WRAPPED")
    print("  Local & Private ChatGPT Usage Analyzer")
    print("=" * 60)
    while True:
        try:
            val = input("\nEnter the path to your ChatGPT export ZIP file: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            sys.exit(0)

        val = val.strip("'\"")
        if not val:
            print("Please enter a valid path.")
            continue
        p = Path(val)
        if not p.exists():
            print(f"Error: File not found at '{val}'. Please verify the path.")
            continue
        return str(p.resolve())


def select_year_interactive(available_years: list) -> int | None:
    """Allow the user to choose from available years interactively."""


def run_pipeline(
    zip_path: str,
    year: int | None = None,
    output_dir: str = "output",
    open_browser: bool = True
) -> str:
    """
    Execute full pipeline:
    1. Parse ZIP safely
    2. Analyze conversations
    3. Generate standalone HTML report
    4. Open in browser
    """
    print(f"\n[FILE] Opening export archive: {zip_path}")
    try:
        parsed_export = parse_export_zip(zip_path)
    except FileNotFoundError as e:
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)
    except (ValueError, KeyError) as e:
        print(f"\n[ERROR] Parse Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error opening archive: {e}")
        sys.exit(1)

    total_loaded = len(parsed_export.conversations)
    print(f"[OK] Successfully loaded {total_loaded:,} conversation(s).")
    if parsed_export.corrupted_count > 0:
        print(f"[WARN] Skipped {parsed_export.corrupted_count} malformed record(s).")

    if total_loaded == 0:
        print("[ERROR] No valid conversations found in this export.")
        sys.exit(1)

    target_year = year
    if target_year is None and parsed_export.available_years:
        target_year = parsed_export.available_years[0]

    year_label = str(target_year) if target_year else "all_time"
    print(f"[STATS] Computing Wrapped statistics for: {target_year or 'All Time'}...")

    stats = analyze_export(parsed_export.conversations, target_year)

    if stats.total_conversations == 0:
        print(f"[WARN] No conversations found for the year {target_year}.")
        if parsed_export.available_years:
            print(f"   Available years in this export: {', '.join(str(y) for y in parsed_export.available_years)}")
        sys.exit(1)

    out_dir = Path(output_dir)
    out_file = out_dir / f"gpt_wrapped_{year_label}.html"

    print(f"[BUILD] Rendering self-contained Wrapped report...")
    saved_path = render_html_report(stats, parsed_export.available_years, str(out_file))

    print("\n" + "=" * 60)
    print("  YOUR GPT WRAPPED IS READY!")
    print("=" * 60)
    print(f"  • Selected Period:    {target_year or 'All Time'}")
    print(f"  • Total Chats:        {stats.total_conversations:,}")
    print(f"  • Total Messages:     {stats.total_messages:,}")
    print(f"  • Active Days:        {stats.active_days_count:,}")
    print(f"  • Top Topic:          {stats.top_topics[0][0] if stats.top_topics else 'General'}")
    if stats.rabbit_hole:
        print(f"  • Deepest Rabbit Hole: \"{stats.rabbit_hole.title}\" ({stats.rabbit_hole.message_count} msgs)")
    print(f"\n[FILE] Saved Report: {saved_path}")

    if open_browser:
        print("[WEB] Opening report in default web browser...")
        try:
            webbrowser.open(Path(saved_path).as_uri())
        except Exception as e:
            logger.debug(f"Could not open browser automatically: {e}")

    return saved_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate a private, local Spotify-Wrapped-style yearly report from your ChatGPT export."
    )
    parser.add_argument(
        "zip_path",
        nargs="?",
        default=None,
        help="Path to the ChatGPT export ZIP file"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the desktop graphical interface"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run interactive CLI mode in terminal"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Filter statistics by a specific year (e.g., 2026)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Directory to save the generated HTML report (default: output/)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically launch the report in your web browser"
    )

    args = parser.parse_args()

    if (len(sys.argv) == 1 or args.gui) and not args.cli and not args.zip_path:
        try:
            from gui import main as gui_main
            gui_main()
            return
        except Exception as e:
            logger.warning(f"Could not launch GUI ({e}), falling back to interactive terminal prompt...")

    zip_file = args.zip_path
    if not zip_file:
        zip_file = prompt_for_zip_path()

    run_pipeline(
        zip_path=zip_file,
        year=args.year,
        output_dir=args.output,
        open_browser=not args.no_browser
    )


if __name__ == "__main__":
    main()
