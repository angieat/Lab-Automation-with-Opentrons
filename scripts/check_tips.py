"""
check_tips.py
─────────────
Calculates tip consumption for each protocol before you load the robot.
Warns if you will run out of tips mid-run based on your sample count and
parameter choices.

Usage:
    python scripts/check_tips.py --protocol pcr_lrg_prep_flex --samples 48
    python scripts/check_tips.py --protocol ivtt --samples 24 --addins 2
    python scripts/check_tips.py --protocol serial_dilution --plates 3 --components 8
    python scripts/check_tips.py --list
"""

import argparse
import sys

# ── ANSI colours ─────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


# ── Tip rack capacities ───────────────────────────────────────────────────────

TIP_RACKS = {
    "opentrons_flex_96_tiprack_50ul":       96,
    "opentrons_96_tiprack_300ul":           96,
    "opentrons_96_tiprack_1000ul":          96,
    "opentrons_96_filtertiprack_20ul":      96,
    "opentrons_96_filtertiprack_1000ul":    96,
}


# ── Protocol tip calculators ──────────────────────────────────────────────────
# Each function returns a dict with:
#   total_tips        int   — total tips consumed
#   breakdown         list  — [(step_name, tip_count), ...]
#   tip_racks_needed  dict  — {rack_load_name: count}
#   available_tips    int   — tips loaded in the protocol by default

def calc_pcr_prep_ot2(samples: int, separate_primers: bool = True, **kwargs) -> dict:
    """PCR_Prep_OT2.py — P20 + P1000, up to 8 samples"""
    primer_tips = 2 if separate_primers else 1   # fwd+rev or premixed
    per_sample = 1 + primer_tips + 1 + 1 + 1    # mastermix + primers + plasmid + water + mix
    total = samples * per_sample
    return {
        "total_tips": total,
        "breakdown": [
            ("Master mix (1 tip/sample)", samples),
            (f"Primers ({'fwd+rev' if separate_primers else 'premixed'}, {primer_tips} tip/sample)", samples * primer_tips),
            ("Plasmid DNA (1 tip/sample)", samples),
            ("Water top-up (1 tip/sample)", samples),
            ("Mix step (1 tip/sample)", samples),
        ],
        "tip_racks_needed": {
            "opentrons_96_filtertiprack_20ul":   2,
            "opentrons_96_filtertiprack_1000ul": 2,
        },
        "available_tips": 2 * 96 + 2 * 96,  # 2 × 20ul + 2 × 1000ul racks
    }


def calc_pcr_prep_flex(samples: int, separate_primers: bool = True, **kwargs) -> dict:
    """PCR_Prep_FLEX.py — P50 only, up to 96 samples"""
    primer_tips = 2 if separate_primers else 1
    per_sample = 1 + primer_tips + 1 + 1 + 1
    total = samples * per_sample
    return {
        "total_tips": total,
        "breakdown": [
            ("Master mix (1 tip/sample)", samples),
            (f"Primers ({'fwd+rev' if separate_primers else 'premixed'}, {primer_tips} tip/sample)", samples * primer_tips),
            ("Plasmid DNA (1 tip/sample)", samples),
            ("Water top-up (1 tip/sample)", samples),
            ("Mix step (1 tip/sample)", samples),
        ],
        "tip_racks_needed": {"opentrons_flex_96_tiprack_50ul": 2},
        "available_tips": 2 * 96,
    }


def calc_pcr_lrg_prep_flex(
    samples: int,
    separate_primers: bool = True,
    neg_ctrl: bool = True,
    pos_ctrl: bool = True,
    **kwargs
) -> dict:
    """PCR_LrgPrep_FLEX.py — P50, up to 94 experimental samples + controls"""
    total_wells = samples + (1 if neg_ctrl else 0) + (1 if pos_ctrl else 0)
    primer_tips = 2 if separate_primers else 1

    water_tips   = 1                         # entire batch in one tip
    mm_tips      = total_wells               # 1 per well
    primer_tips_ = total_wells * primer_tips
    dna_tips     = samples + (1 if pos_ctrl else 0)  # experimental + pos ctrl
    mix_tips     = total_wells

    total = water_tips + mm_tips + primer_tips_ + dna_tips + mix_tips
    return {
        "total_tips": total,
        "breakdown": [
            ("Water — entire batch (1 tip total)", 1),
            ("Master mix (1 tip/well)", mm_tips),
            (f"Primers ({primer_tips} tip/well)", primer_tips_),
            ("DNA — experimental + pos ctrl (1 tip/well)", dna_tips),
            ("Mix step (1 tip/well)", mix_tips),
        ],
        "tip_racks_needed": {"opentrons_flex_96_tiprack_50ul": 6},
        "available_tips": 6 * 96,
    }


def calc_ivtt(samples: int, addins: int = 2, **kwargs) -> dict:
    """IVTT_OAID_V3.py — P50, transfers per sample: Sol A + Sol B + add-ins + DNA/water + water + mix"""
    per_sample = 1 + 1 + addins + 1 + 1 + 1  # A + B + addins + plasmid/water + top-up + mix
    total = samples * per_sample
    return {
        "total_tips": total,
        "breakdown": [
            ("Solution A (1 tip/sample)", samples),
            ("Solution B (1 tip/sample)", samples),
            (f"{addins} add-in(s) ({addins} tip/sample)", samples * addins),
            ("Plasmid or water substitute (1 tip/sample)", samples),
            ("Water top-up (1 tip/sample)", samples),
            ("Mix step (1 tip/sample)", samples),
        ],
        "tip_racks_needed": {"opentrons_flex_96_tiprack_50ul": 6},
        "available_tips": 6 * 96,
    }


def calc_serial_dilution(plates: int, components: int, **kwargs) -> dict:
    """SerialDilutionV3.py — P300 multi + P1000 single
    P1000: 1 tip per component per plate (stock load) + 1 tip per component per column per plate (diluent)
    P300 multi: 1 tip set per plate (reused across all 11 serial transfers)
    """
    p1000_stock   = components * plates              # load stocks into col 1
    p1000_diluent = components * 11 * plates         # diluent into cols 2-12
    p300_multi    = 1 * plates                       # 1 tip set per plate, reused

    total_p1000 = p1000_stock + p1000_diluent
    total_p300  = p300_multi * 8                     # multi-channel = 8 tips per pickup

    return {
        "total_tips": total_p1000 + total_p300,
        "breakdown": [
            (f"P1000 — stock load into col 1 (1 tip/component/plate)", p1000_stock),
            (f"P1000 — diluent into cols 2-12 (1 tip/component/col/plate)", p1000_diluent),
            (f"P300 multi — serial transfer (1 set/plate, reused)", total_p300),
        ],
        "tip_racks_needed": {
            "opentrons_96_tiprack_300ul":  2,
            "opentrons_96_tiprack_1000ul": 2,
        },
        "available_tips": 2 * 96 + 2 * 96,
    }


def calc_media_distribution(plates: int, media: int = 1, **kwargs) -> dict:
    """MediaDistribution_26.py — P300 multi + P1000 single
    Standard (no pattern): 1 tip per media per plate
    Patterned (2 media): 2 tips per plate
    """
    tips_per_plate = media  # one tip per media source
    p1000_tips = tips_per_plate * plates
    return {
        "total_tips": p1000_tips,
        "breakdown": [
            (f"P1000 — media distribution ({media} media, 1 tip/media/plate)", p1000_tips),
            ("P300 multi — not used in standard distribution", 0),
        ],
        "tip_racks_needed": {
            "opentrons_96_tiprack_300ul":  2,
            "opentrons_96_tiprack_1000ul": 2,
        },
        "available_tips": 2 * 96 + 2 * 96,
    }


def calc_bac_distribution(samples_per_labware: int, labware_count: int = 1, **kwargs) -> dict:
    """bac_distribution2.py — P300 single + P1000 single
    Media: 1 tip per labware (reused across all wells)
    Bacteria: 1 tip per well inoculated
    """
    media_tips    = labware_count
    bacteria_tips = samples_per_labware * labware_count
    total = media_tips + bacteria_tips
    return {
        "total_tips": total,
        "breakdown": [
            ("P1000 — media distribution (1 tip/labware, reused)", media_tips),
            ("P300 — bacterial inoculation (1 tip/well)", bacteria_tips),
        ],
        "tip_racks_needed": {
            "opentrons_96_tiprack_300ul":       3,
            "opentrons_96_filtertiprack_1000ul": 3,
        },
        "available_tips": 3 * 96 + 3 * 96,
    }


def calc_media_matrix(csv_rows: int, **kwargs) -> dict:
    """MediaMatrixV2.py — P50 Flex
    1 tip per non-WATER row; WATER rows share one tip until a stock row appears.
    Approximate: assumes ~30% of rows are WATER rows.
    """
    stock_tips = int(csv_rows * 0.70)
    water_tips = max(1, int(csv_rows * 0.30 / 5))  # rough: 1 water tip per ~5 water rows
    total = stock_tips + water_tips
    return {
        "total_tips": total,
        "breakdown": [
            ("P50 — stock transfers (1 tip/row)", stock_tips),
            ("P50 — water top-up (shared tip, 1 per group of water rows)", water_tips),
        ],
        "tip_racks_needed": {"opentrons_flex_96_tiprack_50ul": 4},
        "available_tips": 4 * 96,
    }


# ── Protocol registry ─────────────────────────────────────────────────────────

PROTOCOLS = {
    "pcr_ot2":            (calc_pcr_prep_ot2,      "PCR_Prep_OT2.py",          "samples"),
    "pcr_flex":           (calc_pcr_prep_flex,     "PCR_Prep_FLEX.py",         "samples"),
    "pcr_lrg":            (calc_pcr_lrg_prep_flex, "PCR_LrgPrep_FLEX.py",      "samples"),
    "ivtt":               (calc_ivtt,              "IVTT_OAID_V3.py",          "samples"),
    "serial_dilution":    (calc_serial_dilution,   "SerialDilutionV3.py",      "plates + components"),
    "media_distribution": (calc_media_distribution,"MediaDistribution_26.py",  "plates"),
    "bac_distribution":   (calc_bac_distribution,  "bac_distribution2.py",     "samples_per_labware"),
    "media_matrix":       (calc_media_matrix,      "MediaMatrixV2.py",         "csv_rows"),
}


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(protocol_key: str, result: dict, kwargs: dict):
    calc_fn, filename, _ = PROTOCOLS[protocol_key]

    print(f"\n{BOLD}{'─' * 58}{RESET}")
    print(f"{BOLD}  Protocol: {filename}{RESET}")
    print(f"  Parameters: {', '.join(f'{k}={v}' for k, v in kwargs.items() if v is not None)}")
    print(f"{'─' * 58}")

    print(f"\n  Tip consumption breakdown:")
    for step, count in result["breakdown"]:
        if count > 0:
            print(f"    {count:>4}  {step}")

    print(f"\n  {'─' * 40}")
    print(f"  {'Total tips needed:':30} {BOLD}{result['total_tips']}{RESET}")

    print(f"\n  Tip racks loaded in this protocol:")
    total_available = 0
    for rack, count in result["tip_racks_needed"].items():
        capacity = TIP_RACKS.get(rack, 96) * count
        total_available += capacity
        print(f"    {count}× {rack}  ({capacity} tips)")

    print(f"  {'Total tips available:':30} {total_available}")
    print()

    surplus = total_available - result["total_tips"]
    if surplus < 0:
        print(f"  {RED}{BOLD}⚠ INSUFFICIENT TIPS — short by {abs(surplus)} tips.{RESET}")
        extra_racks = -(-abs(surplus) // 96)  # ceiling division
        print(f"  {RED}  Add {extra_racks} more tip rack(s) before running.{RESET}")
    elif surplus < 50:
        print(f"  {YELLOW}⚠ Tight margin — only {surplus} tips to spare. Consider adding a rack.{RESET}")
    else:
        print(f"  {GREEN}✓ Sufficient tips — {surplus} tips to spare.{RESET}")

    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Calculate tip consumption for Opentrons protocols."
    )
    parser.add_argument("--protocol",  "-p", help="Protocol key (use --list to see all)")
    parser.add_argument("--list",      "-l", action="store_true", help="List all available protocols")
    parser.add_argument("--samples",         type=int, help="Number of samples (most protocols)")
    parser.add_argument("--plates",          type=int, help="Number of plates (serial dilution, media)")
    parser.add_argument("--components",      type=int, default=8, help="Number of components/rows (serial dilution)")
    parser.add_argument("--addins",          type=int, default=2, help="Number of add-ins (IVTT)")
    parser.add_argument("--media",           type=int, default=1, help="Number of media types (media distribution)")
    parser.add_argument("--labware-count",   type=int, default=1, dest="labware_count", help="Number of labware (bac distribution)")
    parser.add_argument("--csv-rows",        type=int, dest="csv_rows", help="Number of CSV rows (media matrix)")
    parser.add_argument("--separate-primers",action="store_true", default=True, dest="separate_primers")
    parser.add_argument("--premixed-primers",action="store_true", dest="premixed_primers")
    parser.add_argument("--neg-ctrl",        action="store_true", default=True, dest="neg_ctrl")
    parser.add_argument("--pos-ctrl",        action="store_true", default=True, dest="pos_ctrl")
    args = parser.parse_args()

    if args.list:
        print(f"\n{BOLD}Available protocols:{RESET}\n")
        for key, (_, filename, params) in PROTOCOLS.items():
            print(f"  {BOLD}{key:<22}{RESET}  {filename}  [{params}]")
        print()
        return

    if not args.protocol:
        parser.print_help()
        sys.exit(1)

    if args.protocol not in PROTOCOLS:
        print(f"Unknown protocol '{args.protocol}'. Use --list to see options.")
        sys.exit(1)

    separate_primers = not args.premixed_primers

    kwargs = {
        "samples":          args.samples,
        "plates":           args.plates,
        "components":       args.components,
        "addins":           args.addins,
        "media":            args.media,
        "labware_count":    args.labware_count,
        "csv_rows":         args.csv_rows,
        "separate_primers": separate_primers,
        "neg_ctrl":         args.neg_ctrl,
        "pos_ctrl":         args.pos_ctrl,
        "samples_per_labware": args.samples,
    }

    calc_fn = PROTOCOLS[args.protocol][0]

    # Validate required args per protocol
    required = {
        "pcr_ot2":            "samples",
        "pcr_flex":           "samples",
        "pcr_lrg":            "samples",
        "ivtt":               "samples",
        "serial_dilution":    "plates",
        "media_distribution": "plates",
        "bac_distribution":   "samples",
        "media_matrix":       "csv_rows",
    }
    req_arg = required[args.protocol]
    if kwargs.get(req_arg) is None:
        print(f"Error: --{req_arg.replace('_','-')} is required for {args.protocol}.")
        sys.exit(1)

    result = calc_fn(**kwargs)
    print_report(args.protocol, result, {k: v for k, v in kwargs.items() if v is not None})


if __name__ == "__main__":
    main()
