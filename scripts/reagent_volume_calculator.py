"""
reagent_volume_calculator.py
─────────────────────────────
Calculates the volume of each reagent you need to prepare before a run,
based on your sample count and protocol parameters. Includes a dead volume
buffer (default 10%) to account for pipetting losses.

Usage:
    python scripts/reagent_volume_calculator.py --protocol ivtt --samples 24
    python scripts/reagent_volume_calculator.py --protocol pcr_lrg --samples 48 --mm 10 --final-vol 25
    python scripts/reagent_volume_calculator.py --protocol serial_dilution --plates 2 --components 8 --stock-vol 450
    python scripts/reagent_volume_calculator.py --protocol media_distribution --plates 4 --transfer-vol 900 --wells 96
    python scripts/reagent_volume_calculator.py --list
"""

import argparse
import sys


# ── ANSI colours ──────────────────────────────────────────────────────────────

BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
RESET = "\033[0m"


# ── Reagent calculators ───────────────────────────────────────────────────────

def calc_pcr_ot2_flex(
    samples: int,
    mm_vol: float = 10,
    fwd_vol: float = 2.5,
    rev_vol: float = 2.5,
    dna_vol: float = 1.0,
    final_vol: float = 25,
    separate_primers: bool = True,
    dead_pct: float = 0.10,
    **kwargs
) -> list:
    """PCR_Prep_OT2.py / PCR_Prep_FLEX.py"""
    n = samples
    d = 1 + dead_pct

    primer_vol = fwd_vol + rev_vol if separate_primers else 5.0
    water_per  = final_vol - mm_vol - primer_vol - dna_vol

    reagents = [
        ("PCR Master Mix",     round(n * mm_vol * d, 1),      "µL", "A1 of source labware"),
    ]
    if separate_primers:
        reagents += [
            ("Forward primer",     round(n * fwd_vol * d, 1),     "µL", "A3 of source labware"),
            ("Reverse primer",     round(n * rev_vol * d, 1),     "µL", "A4 of source labware"),
        ]
    else:
        reagents += [
            ("Primer mix",         round(n * 5.0 * d, 1),         "µL", "A2 of source labware"),
        ]
    reagents += [
        ("DNA (per sample)",   round(dna_vol, 1),               "µL", "B1–B8 of source labware (individual tubes)"),
        ("Nuclease-free water",round(n * water_per * d, 1),     "µL", "A1 of water reservoir"),
    ]
    return reagents


def calc_pcr_lrg(
    samples: int,
    mm_vol: float = 10,
    fwd_vol: float = 2.5,
    rev_vol: float = 2.5,
    dna_vol: float = 1.0,
    ctrl_vol: float = 1.0,
    final_vol: float = 25,
    neg_ctrl: bool = True,
    pos_ctrl: bool = True,
    separate_primers: bool = True,
    dead_pct: float = 0.10,
    **kwargs
) -> list:
    """PCR_LrgPrep_FLEX.py"""
    total = samples + (1 if neg_ctrl else 0) + (1 if pos_ctrl else 0)
    d = 1 + dead_pct
    primer_vol = fwd_vol + rev_vol if separate_primers else 5.0
    water_per_exp  = final_vol - mm_vol - primer_vol - dna_vol
    water_neg      = final_vol - mm_vol - primer_vol           # neg ctrl: water replaces DNA
    water_pos      = final_vol - mm_vol - primer_vol - ctrl_vol

    # Conservative water estimate
    total_water = (
        (samples * water_per_exp)
        + (water_neg if neg_ctrl else 0)
        + (water_pos if pos_ctrl else 0)
    )

    reagents = [
        ("PCR Master Mix",      round(total * mm_vol * d, 1),    "µL", "A1 of reagent source"),
    ]
    if separate_primers:
        reagents += [
            ("Forward primer",  round(total * fwd_vol * d, 1),   "µL", "A3 of reagent source"),
            ("Reverse primer",  round(total * rev_vol * d, 1),   "µL", "A4 of reagent source"),
        ]
    else:
        reagents += [
            ("Primer mix",      round(total * 5.0 * d, 1),       "µL", "A2 of reagent source"),
        ]
    if pos_ctrl:
        reagents.append(
            ("Positive ctrl DNA", round(ctrl_vol * d, 1),         "µL", "A1 of DNA plate"),
        )
    reagents += [
        ("Experimental DNA",    round(dna_vol, 1),                "µL", f"A2–A{samples+1} of DNA plate (1 tube/sample)"),
        ("Nuclease-free water", round(total_water * d, 1),        "µL", "A1 of water reservoir"),
    ]
    return reagents


def calc_ivtt(
    samples: int,
    final_vol: float = 25,
    addins: int = 2,
    addin_vols: list = None,
    dead_pct: float = 0.10,
    **kwargs
) -> list:
    """IVTT_OAID_V3.py — fixed volumes for Sol A and Sol B"""
    SOL_A = 10.0
    SOL_B = 7.5
    PLASMID = 2.0
    d = 1 + dead_pct
    n = samples

    if addin_vols is None:
        addin_vols = [1.0] * addins

    total_addin = sum(addin_vols[:addins])
    water_per = final_vol - SOL_A - SOL_B - total_addin - PLASMID

    reagents = [
        ("PURExpress Solution A", round(n * SOL_A * d, 1),    "µL", "Row A of source labware (aliquot per well)"),
        ("PURExpress Solution B", round(n * SOL_B * d, 1),    "µL", "Row B of source labware (aliquot per well)"),
    ]
    for i, vol in enumerate(addin_vols[:addins]):
        reagents.append(
            (f"Add-in {i+1}",     round(n * vol * d, 1),      "µL", f"Row {chr(67+i)} of source labware"),
        )
    reagents += [
        ("Plasmid DNA",           f"{PLASMID} µL/well",        "",   "A1 (pos ctrl), A2+ (experimental) of plasmid plate"),
        ("Nuclease-free water",   round(n * water_per * d, 1), "µL", "A1 of water reservoir"),
    ]
    return reagents


def calc_serial_dilution(
    plates: int = 1,
    components: int = 8,
    stock_vol: float = 450,
    diluent_vol: float = 200,
    dead_pct: float = 0.10,
    **kwargs
) -> list:
    """SerialDilutionV3.py"""
    d = 1 + dead_pct
    n = plates

    # Stock: loaded into column 1, one per component per plate
    stock_total = components * stock_vol * n

    # Diluent: added to columns 2–12 (11 columns)
    diluent_total = components * 11 * diluent_vol * n

    reagents = [
        ("Stock solution (per component)", round(stock_vol * n * d, 1),    "µL", f"Source labware wells 0–{components-1} (one per row)"),
        ("Diluent — total",               round(diluent_total * d, 1),     "µL", "Diluent reservoir (split across wells per your diluent pattern)"),
    ]
    return reagents


def calc_media_distribution(
    plates: int = 1,
    transfer_vol: float = 900,
    wells: int = 96,
    media_count: int = 1,
    dead_pct: float = 0.10,
    **kwargs
) -> list:
    """MediaDistribution_26.py"""
    d = 1 + dead_pct
    wells_per_media = wells // media_count

    reagents = []
    for i in range(media_count):
        total = plates * wells_per_media * transfer_vol * d
        reagents.append(
            (f"Media {i+1}", round(total / 1000, 2), "mL",
             f"Reservoir {i+1} (slot {'1' if i==0 else '4'})"),
        )
    return reagents


def calc_bac_distribution(
    samples: int = 96,
    labware_count: int = 1,
    media_vol: float = 900,
    inoculation_vol: float = 9,    # 1:100 of media_vol
    dead_pct: float = 0.10,
    **kwargs
) -> list:
    """bac_distribution2.py"""
    d = 1 + dead_pct
    total_wells = samples * labware_count
    inoculation_vol = media_vol / 100  # 1:100 dilution

    reagents = [
        ("LB media",          round(total_wells * media_vol * d / 1000, 2), "mL",
         "Media reservoir (slot 5)"),
        ("E. coli culture",   round(total_wells * inoculation_vol * d, 1),  "µL",
         "Source culture rack (slot 1) — culture will be diluted 1:100"),
    ]
    return reagents


def calc_media_matrix(
    csv_rows: int = 50,
    target_vol: float = 100,
    dead_pct: float = 0.10,
    **kwargs
) -> list:
    """MediaMatrixV2.py — rough estimate; actual volumes come from your CSV"""
    d = 1 + dead_pct
    stock_rows = int(csv_rows * 0.70)
    water_rows  = csv_rows - stock_rows
    avg_stock_vol = 25   # µL — rough average

    reagents = [
        ("Stock solutions (total, all sources)", round(stock_rows * avg_stock_vol * d, 1), "µL",
         "Source plate — actual per-well volumes defined in your CSV"),
        ("Nuclease-free water",                  round(water_rows * target_vol * d, 1),    "µL",
         "Well A12 of water reservoir"),
    ]
    return reagents


# ── Protocol registry ─────────────────────────────────────────────────────────

PROTOCOLS = {
    "pcr_ot2":            (calc_pcr_ot2_flex,       "PCR_Prep_OT2.py"),
    "pcr_flex":           (calc_pcr_ot2_flex,       "PCR_Prep_FLEX.py"),
    "pcr_lrg":            (calc_pcr_lrg,            "PCR_LrgPrep_FLEX.py"),
    "ivtt":               (calc_ivtt,               "IVTT_OAID_V3.py"),
    "serial_dilution":    (calc_serial_dilution,    "SerialDilutionV3.py"),
    "media_distribution": (calc_media_distribution, "MediaDistribution_26.py"),
    "bac_distribution":   (calc_bac_distribution,   "bac_distribution2.py"),
    "media_matrix":       (calc_media_matrix,       "MediaMatrixV2.py"),
}


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(protocol_key: str, reagents: list, kwargs: dict):
    _, filename = PROTOCOLS[protocol_key]
    dead_pct = kwargs.get("dead_pct", 0.10)

    print(f"\n{BOLD}{'─' * 64}{RESET}")
    print(f"{BOLD}  Protocol:   {filename}{RESET}")
    print(f"  Parameters: {', '.join(f'{k}={v}' for k,v in kwargs.items() if v is not None and k != 'dead_pct')}")
    print(f"  Dead volume buffer: {int(dead_pct*100)}%")
    print(f"{'─' * 64}")
    print(f"\n  {'Reagent':<35} {'Amount':>10}  {'Location'}")
    print(f"  {'─'*33} {'─'*10}  {'─'*24}")

    for name, amount, unit, location in reagents:
        amount_str = f"{amount} {unit}".strip() if unit else str(amount)
        print(f"  {name:<35} {BOLD}{amount_str:>10}{RESET}  {location}")

    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Calculate reagent volumes needed before a protocol run."
    )
    parser.add_argument("--protocol",      "-p",  help="Protocol key (use --list to see all)")
    parser.add_argument("--list",          "-l",  action="store_true")
    parser.add_argument("--samples",              type=int,   help="Number of samples")
    parser.add_argument("--plates",               type=int,   help="Number of plates")
    parser.add_argument("--components",           type=int,   default=8)
    parser.add_argument("--addins",               type=int,   default=2)
    parser.add_argument("--addin-vol",            type=float, default=1.0,  dest="addin_vol")
    parser.add_argument("--mm",                   type=float, default=10.0, dest="mm_vol")
    parser.add_argument("--fwd-vol",              type=float, default=2.5,  dest="fwd_vol")
    parser.add_argument("--rev-vol",              type=float, default=2.5,  dest="rev_vol")
    parser.add_argument("--dna-vol",              type=float, default=1.0,  dest="dna_vol")
    parser.add_argument("--final-vol",            type=float, default=25.0, dest="final_vol")
    parser.add_argument("--stock-vol",            type=float, default=450,  dest="stock_vol")
    parser.add_argument("--transfer-vol",         type=float, default=900,  dest="transfer_vol")
    parser.add_argument("--wells",                type=int,   default=96)
    parser.add_argument("--media-count",          type=int,   default=1,    dest="media_count")
    parser.add_argument("--csv-rows",             type=int,   default=50,   dest="csv_rows")
    parser.add_argument("--target-vol",           type=float, default=100,  dest="target_vol")
    parser.add_argument("--labware-count",        type=int,   default=1,    dest="labware_count")
    parser.add_argument("--dead-pct",             type=float, default=0.10, dest="dead_pct",
                        help="Dead volume buffer as decimal (default 0.10 = 10%%)")
    parser.add_argument("--premixed-primers",     action="store_true",      dest="premixed_primers")
    parser.add_argument("--neg-ctrl",             action="store_true", default=True, dest="neg_ctrl")
    parser.add_argument("--pos-ctrl",             action="store_true", default=True, dest="pos_ctrl")
    args = parser.parse_args()

    if args.list:
        print(f"\n{BOLD}Available protocols:{RESET}\n")
        for key, (_, filename) in PROTOCOLS.items():
            print(f"  {BOLD}{key:<22}{RESET}  {filename}")
        print()
        return

    if not args.protocol:
        parser.print_help()
        sys.exit(1)

    if args.protocol not in PROTOCOLS:
        print(f"Unknown protocol '{args.protocol}'. Use --list.")
        sys.exit(1)

    addin_vols = [args.addin_vol] * args.addins

    kwargs = {
        "samples":          args.samples,
        "plates":           args.plates,
        "components":       args.components,
        "addins":           args.addins,
        "addin_vols":       addin_vols,
        "mm_vol":           args.mm_vol,
        "fwd_vol":          args.fwd_vol,
        "rev_vol":          args.rev_vol,
        "dna_vol":          args.dna_vol,
        "final_vol":        args.final_vol,
        "stock_vol":        args.stock_vol,
        "transfer_vol":     args.transfer_vol,
        "wells":            args.wells,
        "media_count":      args.media_count,
        "csv_rows":         args.csv_rows,
        "target_vol":       args.target_vol,
        "labware_count":    args.labware_count,
        "dead_pct":         args.dead_pct,
        "separate_primers": not args.premixed_primers,
        "neg_ctrl":         args.neg_ctrl,
        "pos_ctrl":         args.pos_ctrl,
        "samples_per_labware": args.samples,
    }

    calc_fn = PROTOCOLS[args.protocol][0]
    reagents = calc_fn(**kwargs)
    print_report(args.protocol, reagents, kwargs)


if __name__ == "__main__":
    main()
