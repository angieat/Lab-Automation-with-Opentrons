"""
check_custom_labware.py
───────────────────────
Scans a protocol .py file (or all protocols in a directory) for every
load_labware() call, then checks whether the corresponding labware definition
exists in your local config/ folder or the Opentrons standard library.

Catches the most common pre-run mistake: using a custom labware name in a
protocol without having uploaded the JSON definition to the App.

Usage:
    python scripts/check_custom_labware.py protocols/ivtt_oaid/IVTT_OAID_V3.py
    python scripts/check_custom_labware.py protocols/ --all
    python scripts/check_custom_labware.py protocols/ --all --labware-dir config/labware
"""

import argparse
import ast
import re
import sys
from pathlib import Path


# ── ANSI colours ──────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✓{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def err(msg):   print(f"  {RED}✗{RESET}  {msg}")


# ── Opentrons standard labware ────────────────────────────────────────────────
# These are always available without uploading a custom definition.

STANDARD_LABWARE = {
    # Tip racks — OT-2
    "opentrons_96_tiprack_10ul",
    "opentrons_96_tiprack_20ul",
    "opentrons_96_tiprack_300ul",
    "opentrons_96_tiprack_1000ul",
    "opentrons_96_filtertiprack_20ul",
    "opentrons_96_filtertiprack_200ul",
    "opentrons_96_filtertiprack_1000ul",
    # Tip racks — Flex
    "opentrons_flex_96_tiprack_50ul",
    "opentrons_flex_96_tiprack_200ul",
    "opentrons_flex_96_tiprack_1000ul",
    "opentrons_flex_96_filtertiprack_50ul",
    "opentrons_flex_96_filtertiprack_200ul",
    # Plates
    "nest_96_wellplate_100ul_pcr_full_skirt",
    "nest_96_wellplate_200ul_flat",
    "nest_96_wellplate_2ml_deep",
    "nest_12_reservoir_15ml",
    "nest_1_reservoir_195ml",
    "nest_1_reservoir_290ml",
    "corning_96_wellplate_360ul_flat",
    "biorad_96_wellplate_200ul_pcr",
    "usascientific_96_wellplate_2.4ml_deep",
    "usascientific_12_reservoir_22ml",
    # Tube racks
    "opentrons_24_tuberack_nest_1.5ml_snapcap",
    "opentrons_24_tuberack_nest_1.5ml_screwcap",
    "opentrons_24_tuberack_nest_2ml_snapcap",
    "opentrons_24_tuberack_nest_2ml_screwcap",
    "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap",
    "opentrons_15_tuberack_falcon_15ml_conical",
    "opentrons_15_tuberack_nest_15ml_conical",
    "opentrons_15_tuberack_eppendorf_15ml_conical",
    "opentrons_6_tuberack_falcon_50ml_conical",
    "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical",
    # Modules
    "opentrons_96_aluminumblock_nest_wellplate_100ul",
    "opentrons_96_pcr_adapter_nest_wellplate_100ul_pcr_full_skirt",
    "opentrons_aluminum_block_2ml_eppendorf",
    "opentrons_aluminum_block_2ml_screwcap",
}


# ── Extractor ─────────────────────────────────────────────────────────────────

# Regex approach — handles both literal strings and runtime params in load_labware()
LOAD_LABWARE_LITERAL = re.compile(
    r'load_labware\s*\(\s*["\']([a-zA-Z0-9_\.]+)["\']'
)
LOAD_LABWARE_PARAM = re.compile(
    r'load_labware\s*\(\s*protocol\.params\.(\w+)'
)
PARAM_CHOICE_VALUE = re.compile(
    r'"value"\s*:\s*"([a-zA-Z0-9_\.]+)"'
)


def extract_labware_names(source: str) -> tuple[set, set]:
    """
    Returns (literal_names, param_names) found in a protocol file.
    literal_names: load_labware("exact_name", slot)
    param_names:   load_labware(protocol.params.xyz, slot) — extracts all
                   choice values for that param from add_str() blocks
    """
    literal_names = set(LOAD_LABWARE_LITERAL.findall(source))

    # For runtime params, extract all possible choice values from add_str definitions
    param_choice_values = set(PARAM_CHOICE_VALUE.findall(source))

    return literal_names, param_choice_values


# ── Checker ───────────────────────────────────────────────────────────────────

def check_protocol(protocol_path: Path, labware_dir: Path) -> dict:
    """
    Check a protocol file for missing labware definitions.
    Returns dict with: protocol, literal_names, param_names,
    missing, standard, custom_found, custom_missing
    """
    source = protocol_path.read_text(encoding="utf-8", errors="replace")
    literal_names, param_names = extract_labware_names(source)

    all_names = literal_names | param_names

    # Collect available custom labware JSON files
    custom_available = set()
    if labware_dir.is_dir():
        for jf in labware_dir.glob("*.json"):
            custom_available.add(jf.stem)           # filename without .json
            # Also try to read loadName from inside the JSON
            try:
                import json
                data = json.loads(jf.read_text())
                load_name = data.get("parameters", {}).get("loadName", "")
                if load_name:
                    custom_available.add(load_name)
            except Exception:
                pass

    results = {
        "protocol":        protocol_path.name,
        "all_names":       all_names,
        "standard":        set(),
        "custom_found":    set(),
        "custom_missing":  set(),
        "runtime_params":  param_names,
    }

    for name in sorted(all_names):
        if name in STANDARD_LABWARE:
            results["standard"].add(name)
        elif name in custom_available:
            results["custom_found"].add(name)
        else:
            results["custom_missing"].add(name)

    return results


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(result: dict, labware_dir: Path):
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}  Protocol: {result['protocol']}{RESET}")
    print(f"{'─' * 60}")

    if result["standard"]:
        print(f"\n  Standard labware (always available):")
        for name in sorted(result["standard"]):
            ok(name)

    if result["custom_found"]:
        print(f"\n  Custom labware (definition found in {labware_dir}):")
        for name in sorted(result["custom_found"]):
            ok(name)

    if result["custom_missing"]:
        print(f"\n  Custom labware (definition NOT found — must upload to App):")
        for name in sorted(result["custom_missing"]):
            err(f"{name}")
            print(f"       → Create JSON at labware.opentrons.com and save to {labware_dir}/{name}.json")

    if result["runtime_params"] and not result["custom_missing"]:
        print(f"\n  Runtime param labware choices all accounted for.")

    if not result["all_names"]:
        warn("No load_labware() calls found in this file.")

    total = len(result["all_names"])
    missing = len(result["custom_missing"])
    print()
    if missing == 0:
        print(f"  {GREEN}{BOLD}All {total} labware name(s) resolved.{RESET}")
    else:
        print(f"  {RED}{BOLD}{missing} of {total} labware name(s) missing definitions.{RESET}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Check that all labware in a protocol has a definition available."
    )
    parser.add_argument(
        "target",
        help="Path to a protocol .py file or directory"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Scan all .py files recursively in a directory"
    )
    parser.add_argument(
        "--labware-dir", default="config/labware",
        help="Path to folder containing custom labware JSON files (default: config/labware)"
    )
    args = parser.parse_args()

    labware_dir = Path(args.labware_dir)
    target = Path(args.target)

    if target.is_dir():
        protocol_files = sorted(target.rglob("*.py")) if args.all else []
        if not protocol_files:
            print(f"No .py files found. Use --all to scan recursively.")
            sys.exit(1)
    elif target.is_file():
        protocol_files = [target]
    else:
        print(f"Error: {target} not found.")
        sys.exit(1)

    print(f"\n{BOLD}Custom Labware Checker{RESET}")
    print(f"Labware definition folder: {labware_dir}")
    if not labware_dir.is_dir():
        warn(f"Labware folder '{labware_dir}' does not exist — only checking standard library.")

    all_clear = True
    for pf in protocol_files:
        result = check_protocol(pf, labware_dir)
        print_report(result, labware_dir)
        if result["custom_missing"]:
            all_clear = False

    print(f"\n{'─' * 60}")
    if all_clear:
        print(f"{GREEN}{BOLD}All protocols clear — no missing labware definitions.{RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}Missing labware definitions found. Upload JSON files before running.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
