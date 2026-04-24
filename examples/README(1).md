# Serial Dilution — M9 Media Component Dose-Response Example

**Protocol file:** `protocols/serial_dilution/SerialDilutionV3.py`
**Robot:** OT-2
**Author:** Angie
**Use case:** Preparing 96-well plates with 1:2 serial dilutions of M9 media components to identify optimal growth concentrations.

---

## Background

M9 minimal media supports defined, reproducible bacterial growth. It contains 6 core components that can be individually titrated to find the concentration that supports the most optimized growth. Rather than preparing each concentration by hand, this protocol automates serial dilution of all 6 components across a 96-well plate in a single robot run.

Each component occupies one row of the plate. The robot loads the stock concentration into column 1, fills the remaining columns with diluent, then performs a 1:2 serial transfer cascade from column 1 through column 11. Column 12 receives diluent only and serves as a blank.

---

## Dilution Scheme

![Serial dilution cascade across a 96-well plate. Column 1 contains the undiluted stock (1:1). Each subsequent column is a 1:2 dilution of the previous, ending at 1:1032 in column 11. Column 12 is the diluent blank.](deck_layout.png)

The dilution factor at each column:

| Column | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dilution | 1:1 | 1:2 | 1:4 | 1:8 | 1:16 | 1:32 | 1:64 | 1:128 | 1:256 | 1:512 | 1:1032 | Blank |

Each transfer moves 150 µL from the current column into the next. Each destination column already contains 150 µL of diluent, producing a 1:2 dilution at every step.

---

## M9 Component Layout

This example uses 6 components, one per row (A–F). Rows G and H can be used for additional conditions or left empty.

| Row | Component | Stock concentration | Typical final range tested |
|---|---|---|---|
| A | MgSO₄ | 1 M | 0.1–50 mM |
| B | CaCl₂ | 100 mM | 0.05–5 mM |
| C | Carbon source (glucose) | 40% w/v | 0.02–5% |
| D | NH₄Cl (nitrogen) | 1 M | 0.1–50 mM |
| E | Na₂HPO₄ | 1 M | 0.1–50 mM |
| F | KH₂PO₄ | 1 M | 0.1–50 mM |
| G | (spare — e.g. trace metals) | — | — |
| H | (spare — e.g. vitamin supplement) | — | — |

Prepare each component as a stock solution at the concentration shown. Aliquot into the 12-well reservoir (one component per well, loaded in row order A–F → reservoir wells 1–6).

---

## Reagents and Materials

| Item | Amount needed | Location |
|---|---|---|
| MgSO₄ stock | 600 µL | Reservoir well 1 (A1) |
| CaCl₂ stock | 600 µL | Reservoir well 2 (A2) |
| Glucose stock | 600 µL | Reservoir well 3 (A3) |
| NH₄Cl stock | 600 µL | Reservoir well 4 (A4) |
| Na₂HPO₄ stock | 600 µL | Reservoir well 5 (A5) |
| KH₂PO₄ stock | 600 µL | Reservoir well 6 (A6) |
| Nuclease-free water or M9 base | ~25 mL | Reservoir well 9 (A9) |
| Axygen 96-well plate (500 µL) | 1 | Destination plate |

> Use the reagent volume calculator before every run:
> ```bash
> python scripts/reagent_volume_calculator.py --protocol serial_dilution \
>     --plates 1 --components 6 --stock-vol 450
> ```

---

## Deck Layout

| Slot | Labware |
|---|---|
| 1 | `usascientific_12_reservoir_22ml` — stock solutions (wells 1–6) + water (well 9) |
| 2 | `axygen_96_wellplate_500ul` — destination plate |
| 3 | Second destination plate (if `num_plates` = 2) |
| 4 | *(empty or third plate)* |
| 5 | Diluent reservoir (same type as stock source, or a second reservoir) |
| 7 | `opentrons_96_tiprack_300ul` |
| 8 | `opentrons_96_tiprack_1000ul` |
| 10 | `opentrons_96_tiprack_300ul` |
| 11 | `opentrons_96_tiprack_1000ul` |
| 12 | Fixed trash |

**Pipettes:**
- Right mount: P300 Multi-Channel Gen2 (serial dilution transfers)
- Left mount: P1000 Single-Channel Gen2 (stock and diluent loading)

---

## Runtime Parameters for This Example

Open the Opentrons App, load `SerialDilutionV3.py`, and set:

| Parameter | Value for this example |
|---|---|
| Final 96-well labware | 500 µL plate (`axygen_96_wellplate_500ul`) |
| Number of plates | 1 |
| Number of components | 6 |
| Reagent source labware | 12-well reservoir (`usascientific_12_reservoir_22ml`) |
| Diluent labware type | 12-well reservoir |
| Diluent pattern | `1,1,1,1,1,1` — all components use the same diluent well (well 9) |

If you want a component-specific diluent (e.g. DMSO for an organic compound), change that component's index in the pattern. For example, `1,1,2,1,1,1` means the glucose row (row C) draws from diluent well 2 instead of well 1.

---

## Pre-Run Checklist

Before loading the robot, run through these steps:

```bash
# 1. Simulate the protocol — catches labware and logic errors
python scripts/validate_deck.py protocols/serial_dilution/SerialDilutionV3.py

# 2. Check you have enough tips
python scripts/check_tips.py --protocol serial_dilution --plates 1 --components 6

# 3. Check all custom labware definitions are uploaded
python scripts/check_custom_labware.py protocols/serial_dilution/SerialDilutionV3.py
```

Expected tip check output for 1 plate, 6 components:
```
  P1000 — stock load into col 1 (1 tip/component/plate)         6
  P1000 — diluent into cols 2-12 (1 tip/component/col/plate)   66
  P300 multi — serial transfer (1 set/plate, reused)             8
  ──────────────────────────────────────────────────────
  Total tips needed:                                            80
  Total tips available:                                        384
  ✓ Sufficient tips — 304 tips to spare.
```

---

## Protocol Steps (What the Robot Does)

### Step 1 — Load stocks into column 1

The P1000 single-channel pipette transfers 450 µL of each component's stock solution from the reservoir into column 1 of the plate, one row at a time. A new tip is used for each component to prevent cross-contamination between stocks.

```
Well A1 ← 450 µL MgSO₄ stock     (reservoir well 1)
Well B1 ← 450 µL CaCl₂ stock     (reservoir well 2)
Well C1 ← 450 µL Glucose stock    (reservoir well 3)
Well D1 ← 450 µL NH₄Cl stock     (reservoir well 4)
Well E1 ← 450 µL Na₂HPO₄ stock   (reservoir well 5)
Well F1 ← 450 µL KH₂PO₄ stock   (reservoir well 6)
```

> **Note:** 450 µL is loaded to account for dead volume. After the serial transfer (Step 3), approximately 150 µL remains in column 1.

### Step 2 — Distribute diluent into columns 2–12

The P1000 transfers 200 µL of diluent (water or M9 base) into every well in columns 2–12. Each row's diluent is drawn from the well index specified in the diluent pattern. A new tip is used per row per column.

### Step 3 — Serial dilution

The P300 multi-channel picks up one set of 8 tips and performs the serial transfer without changing tips:

```
Column 1 → Column 2  (150 µL, mix 3× at 50 µL)
Column 2 → Column 3  (150 µL, mix 3× at 50 µL)
...
Column 10 → Column 11 (150 µL, mix 3× at 50 µL)
```

Column 12 is not transferred from — it remains as a diluent-only blank for your plate reader baseline.

The tip reuse across all 11 transfers is intentional. Because each transfer moves through a continuous dilution series of the same component, cross-contamination between columns is not an issue.

---

## After the Run

### Downstream use

The completed plate is ready for:

- **Growth assay:** inoculate with a standardized bacterial suspension (e.g. OD₆₀₀ = 0.05) and incubate. Read OD₆₀₀ at 16–24 h.
- **Fluorescence assay:** if using a reporter strain, read fluorescence alongside OD₆₀₀.
- **Colorimetric assay:** add your indicator and read absorbance at the appropriate wavelength.

### Logging the run

After the protocol completes, export the run log from the Opentrons App and parse it:

```bash
python scripts/parse_run_log.py run_logs/your_run_log.json
```

This appends a row to `run_history.csv` with the run ID, timestamp, duration, and any errors — useful for linking the robot run to your plate reader data file.

### Plate map

Keep a copy of the plate layout. A simple format:

```
Rows:    A=MgSO₄  B=CaCl₂  C=Glucose  D=NH₄Cl  E=Na₂HPO₄  F=KH₂PO₄
Columns: 1=1:1  2=1:2  3=1:4  4=1:8  5=1:16  6=1:32
         7=1:64  8=1:128  9=1:256  10=1:512  11=1:1032  12=blank
```

Save this alongside your raw plate reader output file so you can always reconstruct which well contained which condition.

---

## Adapting This Example

**More plates:** Increase `num_plates` to 2–4. The robot repeats the full protocol for each plate using the same stock reservoir.

**More components:** Increase `num_components` up to 8 (one per row). Add additional stock aliquots to the reservoir and extend the diluent pattern string accordingly.

**Different dilution factor:** The current protocol does 1:2 (transfers 150 µL into 150 µL of diluent). For a 1:3 dilution, change the stock volume in column 1 to 300 µL and the transfer volume to 150 µL into 300 µL of diluent — edit the `left.transfer(450, ...)` and the diluent volume in the protocol code.

**Using SerialDilutionV3 instead of the original V2:** V3 adds per-component diluent assignment, multi-plate support, and runtime parameters so you do not need to edit the code. The original V2 code (included in the Notion export) is useful as a reference for understanding the core logic, but V3 is the production version in this repo.

---

## Files in This Example

| File | Description |
|---|---|
| `deck_layout.png` | Dilution cascade diagram showing 1:2 serial dilution across all 12 columns |
| `README.md` | This file — full walkthrough of the M9 component titration example |
