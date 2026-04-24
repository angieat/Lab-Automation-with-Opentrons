"""
parse_run_log.py
────────────────
Parses Opentrons run log JSON files (downloaded from the robot or App) and
appends a summary row to a lab CSV log. Useful for maintaining a run history
in your lab notebook or for linking robot runs to experimental data.

The Opentrons App stores run logs at:
  OT-2:  http://<robot-ip>:31950/runs
  Flex:  http://<robot-ip>:31950/runs

You can also export a run log JSON from the App via the run details page.

Usage:
    # Parse a single run log file
    python scripts/parse_run_log.py run_logs/run_20240315.json

    # Parse all JSON files in a folder
    python scripts/parse_run_log.py run_logs/

    # Fetch the latest run directly from a connected robot
    python scripts/parse_run_log.py --fetch --robot-ip 169.254.68.68

    # Specify a custom output CSV (default: run_history.csv)
    python scripts/parse_run_log.py run_logs/ --output data/run_history.csv
"""

import argparse
import csv
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


# ── CSV output columns ────────────────────────────────────────────────────────

CSV_COLUMNS = [
    "run_id",
    "protocol_name",
    "robot_type",
    "status",
    "started_at",
    "completed_at",
    "duration_min",
    "operator",
    "errors",
    "error_messages",
    "commands_total",
    "commands_failed",
    "labware_loaded",
    "pipettes_used",
    "source_file",
]


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_run_log(log_path: Path) -> dict:
    """
    Parse a single Opentrons run log JSON file.
    Returns a flat dict matching CSV_COLUMNS.
    """
    with open(log_path) as f:
        data = json.load(f)

    # The Opentrons API wraps the run in a 'data' key when fetched via HTTP
    run = data.get("data", data)

    # ── Basic metadata ──
    run_id       = run.get("id", "unknown")
    status       = run.get("status", "unknown")
    protocol     = run.get("protocolId", "")

    # Protocol name — nested under protocol.metadata or labware[0] in older formats
    protocol_name = (
        run.get("protocol", {}).get("metadata", {}).get("protocolName")
        or run.get("protocolKey", "")
        or "unknown"
    )

    robot_type = run.get("robotType", "unknown")

    # ── Timestamps ──
    started_raw   = run.get("startedAt",   run.get("createdAt", ""))
    completed_raw = run.get("completedAt", "")

    def parse_ts(ts_str: str):
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    started_at   = parse_ts(started_raw)
    completed_at = parse_ts(completed_raw)

    if started_at and completed_at:
        duration_min = round((completed_at - started_at).total_seconds() / 60, 1)
    else:
        duration_min = ""

    started_str   = started_at.strftime("%Y-%m-%d %H:%M:%S UTC") if started_at else ""
    completed_str = completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if completed_at else ""

    # ── Commands ──
    commands = run.get("commands", [])
    commands_total  = len(commands)
    commands_failed = sum(1 for c in commands if c.get("status") == "failed")

    # ── Errors ──
    errors_list = run.get("errors", [])
    error_count = len(errors_list)
    error_messages = "; ".join(
        e.get("detail", e.get("errorType", "unknown error"))
        for e in errors_list[:3]  # cap at 3 for readability
    )

    # ── Labware ──
    labware_list = run.get("labware", [])
    labware_names = ", ".join(
        lw.get("loadName", lw.get("definitionUri", "unknown"))
        for lw in labware_list
        if lw.get("loadName") not in ("fixedTrash", "opentrons_1_trash_3200ml_fixed")
    )

    # ── Pipettes ──
    pipettes = run.get("pipettes", [])
    pipette_names = ", ".join(
        f"{p.get('mount', '?')}:{p.get('pipetteName', p.get('name', 'unknown'))}"
        for p in pipettes
    )

    # ── Operator — not in standard run log, left blank for manual entry ──
    operator = ""

    return {
        "run_id":           run_id,
        "protocol_name":    protocol_name,
        "robot_type":       robot_type,
        "status":           status,
        "started_at":       started_str,
        "completed_at":     completed_str,
        "duration_min":     duration_min,
        "operator":         operator,
        "errors":           error_count,
        "error_messages":   error_messages,
        "commands_total":   commands_total,
        "commands_failed":  commands_failed,
        "labware_loaded":   labware_names,
        "pipettes_used":    pipette_names,
        "source_file":      str(log_path),
    }


# ── Fetcher (live robot) ──────────────────────────────────────────────────────

def fetch_latest_run(robot_ip: str) -> dict:
    """Fetch the most recent run log directly from a connected robot."""
    url = f"http://{robot_ip}:31950/runs?pageLength=1&sortBy=createdAt&sortOrder=desc"
    try:
        print(f"  Fetching latest run from {robot_ip}...")
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        runs = data.get("data", [])
        if not runs:
            print("  No runs found on robot.")
            return None
        run_id = runs[0]["id"]

        # Fetch full run detail
        detail_url = f"http://{robot_ip}:31950/runs/{run_id}"
        with urllib.request.urlopen(detail_url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"  Could not reach robot at {robot_ip}: {e}")
        return None


# ── CSV writer ────────────────────────────────────────────────────────────────

def append_to_csv(rows: list, output_path: Path):
    """Append parsed run rows to a CSV log. Creates file with header if missing."""
    file_exists = output_path.exists()
    existing_ids = set()

    if file_exists:
        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            existing_ids = {r["run_id"] for r in reader}

    new_rows = [r for r in rows if r["run_id"] not in existing_ids]
    skipped  = len(rows) - len(new_rows)

    with open(output_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    return len(new_rows), skipped


# ── Printer ───────────────────────────────────────────────────────────────────

def print_row(row: dict):
    status_icon = {
        "succeeded": "\033[92m✓\033[0m",
        "failed":    "\033[91m✗\033[0m",
        "running":   "\033[93m⟳\033[0m",
    }.get(row["status"], "·")

    print(f"\n  {status_icon}  {row['protocol_name']}  [{row['run_id'][:8]}...]")
    print(f"     Robot:    {row['robot_type']}")
    print(f"     Status:   {row['status']}")
    print(f"     Started:  {row['started_at']}")
    if row["duration_min"]:
        print(f"     Duration: {row['duration_min']} min")
    if row["errors"]:
        print(f"     \033[91mErrors:   {row['errors']} — {row['error_messages']}\033[0m")
    print(f"     Commands: {row['commands_total']} total, {row['commands_failed']} failed")
    if row["labware_loaded"]:
        print(f"     Labware:  {row['labware_loaded'][:80]}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parse Opentrons run log JSON files into a CSV run history."
    )
    parser.add_argument(
        "target", nargs="?",
        help="Path to a run log .json file or directory of .json files"
    )
    parser.add_argument(
        "--fetch", action="store_true",
        help="Fetch latest run log directly from the robot"
    )
    parser.add_argument(
        "--robot-ip", default="169.254.68.68",
        help="Robot IP address for --fetch (default: 169.254.68.68)"
    )
    parser.add_argument(
        "--output", "-o", default="run_history.csv",
        help="Output CSV file path (default: run_history.csv)"
    )
    parser.add_argument(
        "--print-only", action="store_true",
        help="Print parsed rows without writing to CSV"
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    rows = []

    if args.fetch:
        raw = fetch_latest_run(args.robot_ip)
        if raw:
            # Save fetched JSON temporarily for parsing
            tmp = Path("_fetched_run.json")
            tmp.write_text(json.dumps(raw))
            rows.append(parse_run_log(tmp))
            tmp.unlink()
    elif args.target:
        target = Path(args.target)
        if target.is_dir():
            json_files = sorted(target.glob("*.json"))
            if not json_files:
                print(f"No .json files found in {target}")
                sys.exit(1)
            for jf in json_files:
                try:
                    rows.append(parse_run_log(jf))
                except Exception as e:
                    print(f"  Skipping {jf.name}: {e}")
        elif target.is_file():
            rows.append(parse_run_log(target))
        else:
            print(f"Error: {target} not found.")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    if not rows:
        print("No run logs parsed.")
        sys.exit(0)

    print(f"\n\033[1mOpentrons Run Log Parser\033[0m")
    print(f"{'─' * 56}")
    for row in rows:
        print_row(row)

    if not args.print_only:
        added, skipped = append_to_csv(rows, output_path)
        print(f"\n{'─' * 56}")
        print(f"  CSV updated: {output_path}")
        print(f"  {added} new row(s) added, {skipped} duplicate(s) skipped.\n")
    else:
        print(f"\n  (--print-only: CSV not written)\n")


if __name__ == "__main__":
    main()
