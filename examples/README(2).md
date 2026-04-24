# Automated Media Matrix — *E. coli* Growth Optimization

**Protocols used:** `MediaMatrixV2.py` + `SerialDilutionV3.py` + `M9+.py`
**Robot:** OT-2 (serial dilution) → Opentrons Flex (media matrix)
**Date:** October 20–22, 2025
**Author:** Angie Aguirre-Tobar
**Status:** Completed ✓

---

## Purpose

This experiment tests combinations of three M9 media components — NaCl, MgSO₄, and D-Glucose — across a 96-well plate to identify which concentrations support optimal *E. coli* growth. Rather than preparing each well manually, two Opentrons protocols handle the full liquid handling pipeline:

1. **Serial dilution** (`SerialDilutionV3.py` on the OT-2) — generates a concentration gradient of each component across a source plate
2. **Media matrix** (`MediaMatrixV2.py` on the Flex) — cherry-picks specific dilutions from the source plate into each destination well according to the CSV, then tops up with water to reach the target volume

---

## Components and Starting Concentrations

| Row in serial dilution plate | Component | Stock concentration |
|---|---|---|
| A | NaCl | 5 M |
| B | MgSO₄ | 40 mM |
| C | D-Glucose | 800 mM |

Each component was serially diluted 1:2 across 12 columns, producing concentrations from stock (column 1) down to ~1:1032 (column 11) with a water blank in column 12.

---

## CSV Cherry-Picking File

**File:** [`na_mg_glu_water.csv`](na_mg_glu_water.csv)

The CSV defines the exact source well and volume for each transfer into the destination plate. Each destination well receives one transfer from a NaCl dilution row (row A of source), one from MgSO₄ (row B), one from D-Glucose (row C), and a WATER top-up calculated to reach the target volume.

**CSV format:**
```
well.num,volume,dest
WATER,29.41,A1       ← water top-up for well A1
...
C5,21.77,A1          ← 21.77 µL of D-Glucose from source well C5 → dest A1
A7,24.19,A1          ← 24.19 µL of NaCl from source well A7 → dest A1
B2,24.63,A1          ← 24.63 µL of MgSO₄ from source well B2 → dest A1
```

Each destination well draws from a different dilution step of each component, creating a combinatorial matrix where every well has a unique combination of NaCl, MgSO₄, and glucose concentrations. The water volume for each well is calculated to bring the total to the target volume (100 µL).

The source well references map to the serial dilution plate:
- `A1`–`A12` = NaCl at 12 dilution steps
- `B1`–`B12` = MgSO₄ at 12 dilution steps
- `C1`–`C12` = D-Glucose at 12 dilution steps

---

## Protocol Run Notes

### Day 1 — October 20, 2025

**Serial dilution adjustments:**
- Updated `SerialDilutionV3.py` with runtime parameters for final volume, dilution factor, number of components, and water source — eliminating the need to edit code between runs
- Removed the "dispense extra water" function to reduce run time

**Pipetting issue — multi-channel inconsistency:**
- Observed uneven fill across the P300 multi-channel, with plate 1 prepped more consistently than plate 2
- Removed the pipette, cleaned with 70% ethanol, and re-attached
- Issue persisted → see Day 2

**Overnight culture:** Inoculated *E. coli* from frozen stock and grew overnight culture

---

### Day 2 — October 21, 2025

**Pipetting issue — resolved:**
- Removed pipette, replaced o-rings, re-leveled
- ✅ Issue resolved — consistent fill across all channels

**Moved to the Flex for media matrix:**
- Custom labware issue with the 2 mL 96-well plate: pipette was bumping the well edges and miscounting positions
- Troubleshooting steps:
  1. Remeasured the plate and rebuilt the JSON definition from scratch
  2. Re-calibrated the labware in the Opentrons App
  3. Reached out to the plate manufacturer for the official CAD file
  4. Received CAD file, imported manufacturer measurements into the JSON definition
  5. ✅ Issue resolved — accurate dispensing confirmed

**Re-ran serial dilution** with corrected pipette for fresh source plates:
- Note: calibrate the robot arm slightly higher above the plate surface than the default — helps with consistent tip immersion depth on this labware type

**Ran media matrix** using the freshly prepared serial dilution plates and [`na_mg_glu_water.csv`](na_mg_glu_water.csv)

---

### Day 3 — October 22, 2025

**Media matrix re-run:**
- The serial dilution source plate had been frozen over the weekend and thawed at room temperature before use

**M9 media preparation (100 mL total):**
- 50 mL of 2× M9 base
- 50 mL of sterile water
- 50 µL ampicillin (antibiotic selection)

**Inoculation:**
- Set up *E. coli* culture from frozen stock, grown for 4 hours to mid-log phase
- Beginning OD₆₀₀: **0.06** (uniform across all wells at inoculation)

**Incubation:**
- Sealed with air-porous seals (allows gas exchange while preventing evaporation/contamination)
- 37°C, 450 rpm, 24 hours

---

## Results — OD₆₀₀ Endpoint (24 h)

**Reader:** BioTek Synergy H1
**Date measured:** October 22, 2025, 16:18
**Actual plate temperature:** 37.1°C
**Wavelength:** 600 nm

Raw OD₆₀₀ readings after 24 h incubation:

|   | **Col 1** | **Col 2** | **Col 3** | **Col 4** | **Col 5** | **Col 6** | **Col 7** | **Col 8** | **Col 9** | **Col 10** | **Col 11** | **Col 12** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A** | 0.145 | 0.139 | 0.141 | **0.318** | 0.168 | **0.284** | 0.117 | 0.143 | 0.098 | 0.097 | 0.130 | 0.092 |
| **B** | 0.101 | 0.131 | 0.150 | 0.126 | 0.154 | 0.149 | 0.192 | 0.128 | 0.108 | 0.117 | **0.336** | 0.120 |
| **C** | 0.138 | 0.106 | 0.155 | 0.153 | 0.126 | 0.165 | **0.320** | 0.154 | 0.095 | 0.136 | 0.096 | 0.132 |
| **D** | 0.145 | 0.136 | 0.119 | 0.105 | 0.157 | **0.233** | 0.128 | 0.099 | 0.148 | 0.116 | 0.099 | 0.093 |
| **E** | 0.146 | 0.154 | 0.162 | 0.152 | 0.127 | 0.140 | 0.137 | 0.098 | 0.102 | 0.122 | 0.094 | **0.326** |
| **F** | 0.190 | 0.156 | 0.198 | 0.120 | 0.117 | 0.128 | 0.120 | 0.092 | 0.127 | 0.101 | 0.090 | 0.091 |
| **G** | 0.132 | 0.197 | 0.115 | **0.228** | 0.100 | 0.107 | 0.133 | 0.141 | **0.245** | 0.125 | 0.090 | 0.106 |
| **H** | 0.153 | 0.105 | 0.137 | 0.102 | 0.168 | 0.112 | 0.198 | **0.250** | 0.108 | 0.107 | 0.105 | 0.113 |

**Bold** = OD₆₀₀ > 0.2 (above-average growth; baseline starting OD = 0.06)

**Raw data file:** [`od600_results_AAT.xlsx`](od600_results_AAT.xlsx)

---

## Analysis and Observations

**Variance was achieved** — the plate shows a clear spread of OD₆₀₀ values ranging from 0.090 to 0.336, confirming that the different media compositions produce meaningfully different growth outcomes.

**Good pellets** — visible cell pellets were observed at the bottom of high-OD wells after plate reading, confirming the OD readings reflect actual bacterial growth rather than turbidity artifacts.

**High-growth wells (OD > 0.2):** A4, A6, B11, C7, D6, E12, G4, G9, H8

These wells represent the specific NaCl/MgSO₄/Glucose combinations that supported the strongest *E. coli* growth under these conditions. The source well assignments for each of these wells can be traced back through the CSV to identify which dilution of each component was present.

**Next step:** Metabolomics analysis is needed before drawing conclusions about which specific concentration combinations are driving growth differences — OD alone cannot distinguish between wells where growth is carbon-limited, ion-limited, or growth factor-limited.

---

## Troubleshooting Log

| Issue | Root cause | Resolution |
|---|---|---|
| Inconsistent multi-channel pipetting | Dirty o-rings / pipette not level | Replaced o-rings, re-leveled pipette |
| Serial dilution plate 1 better than plate 2 | Pipette calibration drift across run | Fixed by pipette maintenance; re-ran plates |
| Flex bumping well edges on 2 mL plate | Inaccurate custom labware JSON | Obtained manufacturer CAD file; rebuilt JSON with correct dimensions |
| Inaccurate serial dilution tip depth | Arm calibrated too close to plate | Calibrated slightly higher above plate surface than default |

---

## File Reference

| File | Description |
|---|---|
| [`na_mg_glu_water.csv`](na_mg_glu_water.csv) | Cherry-picking CSV used as input to `MediaMatrixV2.py` — defines source well, transfer volume, and destination for every well on the plate |
| [`od600_results_AAT.xlsx`](od600_results_AAT.xlsx) | Raw OD₆₀₀ plate reader output from BioTek Synergy H1, October 22 2025 |

**Protocol files used (stored on cluster):**
- `/fh/fast/sinnott-armstrong_n/proj/opentrons/protocols/OT2_SerialDilution.py`
- `/fh/fast/sinnott-armstrong_n/proj/opentrons/protocols/MediaMatrixV2.py`
- `/fh/fast/sinnott-armstrong_n/proj/opentrons/protocols/M9+.py`

Current versions of the serial dilution and media matrix protocols are also maintained in this repository under `protocols/serial_dilution/` and `protocols/media_matrix/`.
