"""
validate_deck.py
────────────────
Runs opentrons_simulate on a protocol file and parses the output for errors,
warnings, and deck conflicts before you load anything on the robot.

Usage:
    python scripts/validate_deck.py protocols/pcr_prep_flex/PCR_Prep_FLEX.py
    python scripts/validate_deck.py protocols/ --all
    python scripts/validate_deck.py protocols/ivtt_oaid/IVTT_OAID_V3.py --verbose
"""

import argparse
import subprocess
import sys
import re
from pathlib import Path


# ── ANSI colours for terminal output ────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✓{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def err(msg):   print(f"  {RED}✗{RESET}  {msg}")
def info(msg):  print(f"     {msg}")


# ── Patterns to look for in simulate output ──────────────────────────────────

ERROR_PATTERNS = [
    (re.compile(r"LabwareNotFoundError", re.I),      "Labware definition not found — check custom labware is uploaded"),
    (re.compile(r"RuntimeError",         re.I),      "RuntimeError in protocol logic"),
    (re.compile(r"ValueError",           re.I),      "ValueError — check parameter ranges"),
    (re.compile(r"DeckConflictError",    re.I),      "Deck conflict — two labware assigned to same slot"),
    (re.compile(r"PipetteNotAttached",   re.I),      "Pipette not attached or wrong mount specified"),
    (re.compile(r"OutOfTipsError",       re.I),      "Out of tips — add more tip racks"),
    (re.compile(r"Traceback",            re.I),      "Python traceback — protocol crashed"),
]

WARNING_PATTERNS = [
    (re.compile(r"aspirating more than",       re.I), "Volume exceeds pipette max — will split into multiple transfers"),
    (re.compile(r"disposing.*trash",           re.I), "Tip disposed to trash (expected)"),
    (re.compile(r"flow rate.*outside",         re.I), "Flow rate outside recommended range"),
]

LABWARE_PATTERN  = re.compile(r"Labware:\s+(.+)")
PIPETTE_PATTERN  = re.compile(r"(left|right) mount:\s+(.+)", re.I)
TRANSFER_PATTERN = re.compile(r"Transferring")


# ── Core simulation runner ───────────────────────────────────────────────────

def simulate_protocol(protocol_path: Path, verbose: bool = False) -> dict:
    """
    Run opentrons_simulate on a protocol file.
    Returns a dict with keys: success, errors, warnings, labware, pipettes,
    transfer_count, raw_output.
    """
    result = {
        "success": False,
        "errors": [],
        "warnings": [],
        "labware": [],
        "pipettes": [],
        "transfer_count": 0,
        "raw_output": "",
    }

    try:
        proc = subprocess.run(
            ["opentrons_simulate", str(protocol_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        result["errors"].append(
            "opentrons_simulate not found. Install with: pip install opentrons"
        )
        return result
    except subprocess.TimeoutExpired:
        result["errors"].append("Simulation timed out after 120 seconds.")
        return result

    output = proc.stdout + proc.stderr
    result["raw_output"] = output

    # Check for errors
    for pattern, message in ERROR_PATTERNS:
        matches = pattern.findall(output)
        if matches:
            # Find the full line for context
            for line in output.splitlines():
                if pattern.search(line):
                    result["errors"].append(f"{message}\n        → {line.strip()}")
                    break

    # Check for warnings
    for pattern, message in WARNING_PATTERNS:
        for line in output.splitlines():
            if pattern.search(line):
                result["warnings"].append(f"{message}")
                break

    # Extract labware loaded
    for line in output.splitlines():
        m = LABWARE_PATTERN.search(line)
        if m:
            result["labware"].append(m.group(1).strip())
        m = PIPETTE_PATTERN.search(line)
        if m:
            result["pipettes"].append(f"{m.group(1).capitalize()} mount: {m.group(2).strip()}")

    # Count transfers
    result["transfer_count"] = len(TRANSFER_PATTERN.findall(output))

    # Success if no errors and process exited cleanly
    result["success"] = (len(result["errors"]) == 0 and proc.returncode == 0)

    return result


# ── Report printer ───────────────────────────────────────────────────────────

def print_report(protocol_path: Path, result: dict, verbose: bool = False):
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}  Protocol: {protocol_path.name}{RESET}")
    print(f"  Path:     {protocol_path}")
    print(f"{'─' * 60}")

    if result["pipettes"]:
        print("  Pipettes detected:")
        for p in result["pipettes"]:
            info(p)

    if result["labware"]:
        print("  Labware loaded:")
        for lw in result["labware"]:
            info(lw)

    if result["transfer_count"]:
        info(f"{result['transfer_count']} transfer steps in simulation")

    print()

    if result["errors"]:
        for e in result["errors"]:
            err(e)
    
    if result["warnings"]:
        for w in result["warnings"]:
            warn(w)

    if result["success"]:
        ok("Simulation passed — no errors detected")
    else:
        err("Simulation FAILED — fix errors before running on robot")

    if verbose and result["raw_output"]:
        print(f"\n{BOLD}  Full simulation output:{RESET}")
        for line in result["raw_output"].splitlines():
            info(line)


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate Opentrons protocol files using opentrons_simulate."
    )
    parser.add_argument(
        "target",
        help="Path to a protocol .py file, or a directory to scan for all protocols"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="If target is a directory, validate all .py files found recursively"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print full simulation output"
    )
    args = parser.parse_args()

    target = Path(args.target)

    if target.is_dir():
        protocol_files = sorted(target.rglob("*.py")) if args.all else []
        if not protocol_files:
            print(f"No .py files found in {target}. Use --all to scan recursively.")
            sys.exit(1)
    elif target.is_file() and target.suffix == ".py":
        protocol_files = [target]
    else:
        print(f"Error: {target} is not a .py file or directory.")
        sys.exit(1)

    print(f"\n{BOLD}Opentrons Deck Validator{RESET}")
    print(f"Validating {len(protocol_files)} protocol(s)...\n")

    all_passed = True
    for pf in protocol_files:
        result = simulate_protocol(pf, verbose=args.verbose)
        print_report(pf, result, verbose=args.verbose)
        if not result["success"]:
            all_passed = False

    print(f"\n{'─' * 60}")
    if all_passed:
        print(f"{GREEN}{BOLD}All protocols passed validation.{RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}One or more protocols failed. Fix errors before running.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
