# Hardware Setup & Custom Labware Guide

This guide covers everything you need to set up an Opentrons robot in a wet lab, with a detailed walkthrough for creating and registering custom labware definitions.

---

## Table of Contents

1. [Physical Setup](#1-physical-setup)
2. [Software Installation](#2-software-installation)
3. [Connecting to Your Robot](#3-connecting-to-your-robot)
4. [Deck and Pipette Calibration](#4-deck-and-pipette-calibration)
5. [Custom Labware — Step-by-Step Guide](#5-custom-labware--step-by-step-guide)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Physical Setup

### Site requirements

The robot needs a stable, flat, vibration-free surface. Bench vibration — from nearby centrifuges, shakers, or building HVAC — can cause positional drift over long runs. If possible, place the robot on a dedicated anti-vibration mat or a separate bench away from heavy equipment.

Clearance requirements:

- **OT-2:** 60 cm of clearance above the deck for the arm travel path; 30 cm clearance on all sides for access
- **Flex:** 70 cm above the deck; door access on the front requires 50 cm clearance

Keep the robot away from HVAC vents and direct air currents. Air movement can cause evaporation artifacts in small-volume transfers and disrupt droplet formation at tip ends.

### Power and network

Plug into a stable power outlet. Both robots can be connected via USB (direct laptop connection) or Ethernet (network/Wi-Fi bridged). For production use, Ethernet to a dedicated switch is preferred — USB connections can time out during long protocols.

**OT-2 IP addresses:**
- USB: `169.254.68.68` (link-local, fixed)
- Wi-Fi: DHCP-assigned — check the touchscreen or Opentrons App

**Flex IP addresses:**
- Ethernet: DHCP-assigned
- Wi-Fi: DHCP-assigned
- Both displayed on the touchscreen under Settings → Network

---

## 2. Software Installation

### Opentrons App

Download the desktop application from [opentrons.com/ot-app](https://opentrons.com/ot-app). This is the primary interface for running protocols, managing labware, and performing calibration.

Supported platforms: macOS 12+, Windows 10+, Ubuntu 20.04+.

### Python SDK (for protocol development)

```bash
pip install opentrons
```

This installs the `opentrons` Python package and the `opentrons_simulate` command-line tool, which lets you test protocols on your laptop without a robot connected.

To simulate a protocol:

```bash
opentrons_simulate your_protocol.py
```

Simulation output shows every liquid transfer, tip pickup, and error check. Review it carefully before running on the robot, especially for new protocols.

---

## 3. Connecting to Your Robot

**Via USB:**

1. Connect the USB-A to USB-B cable between your laptop and the robot.
2. Open the Opentrons App.
3. The robot should appear automatically in the left panel within 30 seconds.

**Via network (OT-2 Wi-Fi or Flex Ethernet):**

1. In the Opentrons App, click **Devices** → **Add robot manually**.
2. Enter the robot's IP address.
3. Click **Connect**.

Once connected, you will see the robot's name, serial number, and firmware version. Keep the firmware updated — the App will prompt you when a new version is available.

---

## 4. Deck and Pipette Calibration

Calibration tells the robot exactly where each deck slot and labware position is in 3D space. You must calibrate before your first run and re-calibrate after moving the robot, swapping pipettes, or changing tip types.

### Deck calibration (OT-2)

Deck calibration is a one-time process per robot. Use the calibration probe and the calibration block provided with the robot. Follow the on-screen steps in the Opentrons App — the arm will touch three points on the calibration block and compute the deck plane.

### Labware calibration

Each distinct labware type must be calibrated in each deck slot it will be used in. The robot moves its probe to the reference corner of the labware and you jog the Z-axis until the probe just touches the surface.

To calibrate labware:

1. Load the labware in its deck slot.
2. In the App, go to **More** → **Labware** → select the labware → **Calibrate**.
3. Follow on-screen jogging instructions to touch the probe to the A1 well reference point.
4. Save calibration.

### Pipette calibration (OT-2)

After installing a new pipette, run pipette calibration via **Instruments** → **Pipettes** → **Calibrate**.

### Tip length calibration (OT-2)

Each tip type requires its own calibration offset. When you first use a new tip lot or brand, run tip length calibration from the calibration menu.

---

## 5. Custom Labware — Step-by-Step Guide

Opentrons ships definitions for common labware (NEST plates, Falcon tubes, standard reservoirs). When you use labware that is not in the Opentrons library — custom tube racks, non-standard plates, in-house fabricated racks — you must create a custom labware definition file (JSON) and upload it to the robot.

This section walks through the complete process.

---

### Step 5.1 — Measure your labware

Before opening any software, gather precise measurements with calipers. You will need:

**Plate/rack footprint:**

| Measurement | Description |
|---|---|
| Overall X (width) | Outer edge to outer edge, left to right |
| Overall Y (length) | Outer edge to outer edge, front to back |
| Overall Z (height) | Bottom of plate to tallest point |

**Well geometry (measure 3–5 wells and average):**

| Measurement | Description |
|---|---|
| Well diameter | Inner diameter at the top opening (circular wells) |
| Well X × Y | Opening dimensions (rectangular wells) |
| Well depth | From the top lip to the bottom of the well |
| Well bottom shape | Flat, round (U), or conical (V) |
| Well A1 X offset | Distance from left edge of plate to center of A1 well |
| Well A1 Y offset | Distance from front edge of plate to center of A1 well |
| Well-to-well spacing (X) | Center-to-center distance between adjacent columns |
| Well-to-well spacing (Y) | Center-to-center distance between adjacent rows |

**For tube racks, additionally measure:**

| Measurement | Description |
|---|---|
| Tube inner diameter | At the top of the tube |
| Tube total height | Bottom of the tube to top rim |
| Max volume | From the manufacturer's spec sheet |

Write all measurements in a table before proceeding. Errors in labware definition lead to collisions or missed aspiration — double-check before continuing.

---

### Step 5.2 — Open the Labware Creator

Opentrons provides a browser-based tool for creating labware definitions without writing JSON by hand.

Navigate to: **[labware.opentrons.com](https://labware.opentrons.com)**

You will see a step-by-step wizard. Select the labware category that matches your labware:

- **Well plate** — any flat-bottom multi-well plate
- **Tube rack** — a rack holding individual tubes
- **Reservoir** — single or multi-channel troughs
- **Tip rack** — only needed if using non-Opentrons tips

---

### Step 5.3 — Enter footprint dimensions

In the **Footprint** section:

- Set **X** (width in mm) to your outer width measurement.
- Set **Y** (length in mm) to your outer length measurement.
- Set **Z** (height in mm) to your overall labware height.

> **Important:** Opentrons uses SBS/ANSI footprint dimensions (127.76 mm × 85.48 mm) as the standard deck slot size. If your labware has a non-standard footprint, it may not seat correctly in the deck slots or may interfere with the pipette arm. Confirm the footprint before ordering custom labware.

---

### Step 5.4 — Define well layout

In the **Well** section:

1. Set the **number of rows** and **columns**.
2. Enter the **A1 X offset** and **A1 Y offset** — this is the distance from the labware's left front corner to the center of well A1.
3. Enter **column spacing** (center-to-center X) and **row spacing** (center-to-center Y).
4. Set well **shape**: circular (enter diameter) or rectangular (enter X × Y).
5. Enter **well depth**.
6. Select **bottom shape**: flat, U-bottom, or V-bottom.
7. Enter **max volume** per well in µL.

For tube racks, enter the tube's inner diameter as the well diameter and the tube's internal depth as the well depth.

---

### Step 5.5 — Review the 3D preview

The Labware Creator shows a 3D render of your labware based on the values entered. Verify:

- Well count matches what you expect
- Well spacing looks correct — no overlapping, no gaps that are too large
- The A1 well is in the correct corner (top-left when viewed from above)
- The overall footprint looks proportionate

Rotate the 3D view to check the well depth and labware height.

---

### Step 5.6 — Set the brand and name

In the **Details** section:

- **Brand:** your lab name, vendor name, or "custom"
- **Display name:** a descriptive name (e.g., "Lab XYZ 24-tube rack 1.5 mL")
- **Load name:** a short, lowercase, underscore-separated identifier with no spaces (e.g., `labxyz_24_tuberack_1.5ml`). This is the string you will use in your protocol code: `protocol.load_labware("labxyz_24_tuberack_1.5ml", "1")`.

---

### Step 5.7 — Export the JSON file

Click **Export** to download the `.json` definition file. The file name will match your load name.

Open the file in a text editor and verify:
- The `"loadName"` field matches what you intend to use in your protocol code.
- `"wells"` section contains the correct number of entries.
- `"dimensions"` at the top level matches your footprint measurements.

---

### Step 5.8 — Upload to the Opentrons App

1. In the Opentrons App, go to **More** → **Labware**.
2. Click **Import**.
3. Select your `.json` file.
4. The labware will appear in the list under **Custom Labware**.

The labware definition is stored locally on the computer running the App and synced to the robot when you connect. If you move to a different computer, you will need to re-import the JSON.

---

### Step 5.9 — Use in a protocol

Reference the labware by its `loadName` string exactly:

```python
# OT-2
my_rack = protocol.load_labware("labxyz_24_tuberack_1.5ml", "2")

# Flex
my_rack = protocol.load_labware("labxyz_24_tuberack_1.5ml", "D2")
```

If the labware name does not match the uploaded definition exactly (including underscores and capitalization), the protocol will fail with a `LabwareNotFoundError`.

---

### Step 5.10 — Calibrate the custom labware

After loading the custom labware in a protocol run, calibrate it just as you would standard labware (see [Section 4](#4-deck-and-pipette-calibration)). Custom labware requires calibration even if you have calibrated a physically identical piece of labware before — the robot stores calibrations per labware definition ID.

---

### Validating a custom labware definition

After calibration, run a test protocol before using the labware with real reagents:

```python
# Test protocol — checks that arm reaches all corners without collision
from opentrons import protocol_api

metadata = {"protocolName": "Labware validation test"}
requirements = {"robotType": "OT-2", "apiLevel": "2.24"}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware("opentrons_96_filtertiprack_20ul", "7")
    custom = protocol.load_labware("your_custom_labware_name", "2")
    p20 = protocol.load_instrument("p20_single_gen2", mount="right", tip_racks=[tiprack])

    # Visit corners and center well
    test_wells = ["A1", "A12", "H1", "H12", "D6"]
    for well in test_wells:
        try:
            p20.pick_up_tip()
            p20.move_to(custom[well].top())
            p20.drop_tip()
            protocol.comment(f"✓ Reached {well}")
        except Exception as e:
            protocol.comment(f"✗ Failed at {well}: {e}")
```

Run this without reagents first. If the arm reaches all wells without error, your definition is accurate. If the arm collides with the labware or misses the well, re-check your A1 offset and spacing values.

---

### Common custom labware mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| A1 offset too small | Arm hits labware wall on A1 approach | Increase A1 X and/or Y offset |
| Well depth too large | Tip crashes into well bottom | Reduce well depth in definition |
| Wrong bottom shape | Aspirate misses liquid at bottom of V-bottom tube | Change bottom shape to V |
| Spacing wrong | Wells visited in wrong order or tip misses | Re-measure center-to-center distance |
| Load name mismatch | `LabwareNotFoundError` at runtime | Ensure protocol string matches JSON `loadName` exactly |
| Forgot to calibrate | Incorrect Z height, crashes or misses | Calibrate the custom labware in the App |

---

## 6. Troubleshooting

### Robot not found in App

- Verify USB cable is firmly seated at both ends.
- On Windows, check Device Manager for the robot's COM port.
- Try a different USB port or cable.
- Restart the Opentrons App.

### Protocol fails with `LabwareNotFoundError`

- Confirm the labware definition was imported into the App (More → Labware).
- Check that the load name in the protocol code exactly matches the JSON `loadName` field.
- For custom labware, re-import the JSON and reconnect the robot.

### Pipette misses wells consistently in one direction

- Run deck calibration again.
- Check that the labware is seated flat and fully into the deck slot clips.
- Re-calibrate the labware.

### Tip pops off during aspiration

- Reduce aspirate flow rate in the protocol code (see flow rate examples in individual protocol READMEs).
- Check tip compatibility with the pipette mount — Opentrons recommends matching tip lot numbers to the pipette generation.
- For large volumes, reduce `aspirate` rate to ≤50% of default.

### Small-volume transfers are inaccurate

- Perform a tip length calibration for the specific tip type in use.
- Verify flow rates are set to low values (20 µL/s or less for P20/P50 transfers under 5 µL).
- Check for bubbles in the tip after aspiration — this indicates the aspiration rate is too high.

### Robot arm makes clicking noise during movement

- Stop the protocol immediately.
- Check for labware that is too tall for the slot (exceeds the Z height in the labware definition).
- Verify no tip racks have been loaded in slots that conflict with the arm travel path.
- Contact Opentrons support if the clicking continues after clearing labware conflicts.
