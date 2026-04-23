# 🤖 Opentrons Wet Lab Automation Guide

A practical guide for integrating **Opentrons liquid handling robots** into a wet lab environment — from first setup through running your own custom protocols. Designed for both bench scientists and automation engineers. 

This repository is living and growing. This project's mission is to lower the barrier that currently exists for life scientist to integrate robotic automation technology into their labs by create an environment with all the tools, resources and suggestions created by automation engineers.

---

## 📖 Table of Contents

- [Why Automate?](#why-automate)
- [Getting Started](#getting-started)
- [Repository Structure](#repository-structure)
- [Protocols](#protocols)
- [Lab Integration Workflow](#lab-integration-workflow)
- [Hardware & Deck Setup](#hardware--deck-setup)
- [Configuration](#configuration)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## Why Automate?

Manual liquid handling is a bottleneck in modern wet labs — it's slow, variable between operators, and a leading source of experimental error. Opentrons robots offer:

- **Reproducibility** — every run executes identically
- **Throughput** — run protocols overnight or in parallel
- **Traceability** — every liquid transfer is logged
- **Accessibility** — protocols are written in plain Python; no robotics background required

This repo walks you through everything from plugging in the robot to integrating automation into your existing lab SOPs.

---

## Getting Started

### Prerequisites

| Requirement | Details |
|---|---|
| Python | 3.10 or later |
| Opentrons App | [Download here](https://opentrons.com/ot-app/) |
| opentrons SDK | `pip install opentrons` |
| Robot | OT-2 or Flex |

### Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/opentrons-lab-automation.git
cd opentrons-lab-automation

# Install dependencies
pip install -r requirements.txt

# Validate your deck layout before a run
python scripts/validate_deck.py --protocol protocols/serial_dilution/protocol.py

# Simulate a protocol (no robot needed)
opentrons_simulate protocols/serial_dilution/protocol.py
```

---

## Repository Structure

```
opentrons-lab-automation/
│
├── protocols/              # Opentrons Python protocol files
│   ├── serial_dilution/    # Serial dilution protocol
│   │   ├── protocol.py
│   │   ├── README.md
│   │   └── deck_layout.png
│   └── pcr_setup/          # PCR plate setup protocol
│       ├── protocol.py
│       ├── README.md
│       └── deck_layout.png
│
├── docs/                   # Conceptual guides (Markdown)
│   ├── getting_started.md
│   ├── hardware_setup.md
│   └── lab_integration.md
│
├── examples/               # Worked examples and demo data
│   ├── demo_workflow/
│   ├── sample_data/
│   └── notebooks/
│
├── config/                 # Shared configuration files
│   ├── labware.json        # Custom labware definitions
│   ├── robot_config.yaml   # Robot address, pipette slots, etc.
│   └── reagent_map.csv     # Reagent-to-well mapping template
│
├── scripts/                # Utility scripts
│   ├── validate_deck.py    # Pre-run deck layout checker
│   ├── run_protocol.py     # Remote protocol runner (HTTP API)
│   └── parse_results.py    # Post-run log parser
│
├── README.md               # ← You are here
├── CONTRIBUTING.md
├── requirements.txt
└── LICENSE
```

---

## Protocols

Each protocol lives in its own subfolder under `protocols/` with:
- `protocol.py` — the runnable Opentrons script
- `README.md` — purpose, reagents, deck layout, and expected output
- `deck_layout.png` — visual diagram of the deck setup

### Available protocols

| Protocol | Description | Robot | Pipettes |
|---|---|---|---|
| `serial_dilution/` | 1:2 serial dilution across a 96-well plate | OT-2 / Flex | Single or multi-channel |
| `pcr_setup/` | PCR master mix distribution + sample addition | OT-2 / Flex | Multi-channel P20 |

> **Adding your own protocol?** See [CONTRIBUTING.md](CONTRIBUTING.md) for the protocol template and submission checklist.

---

## Lab Integration Workflow

Integrating automation into an existing wet lab is as much a *process* change as a technical one. We recommend this phased approach:

### Phase 1 — Simulate and validate

Run protocols in simulation mode on your laptop before touching the robot. Use `opentrons_simulate` to catch errors early. Review the liquid movement output and confirm volumes match your SOP.

### Phase 2 — Dry run on the robot

Load the deck with empty plates and tip racks. Run the protocol without reagents to verify arm movements, tip pickup, and deck positioning. Check for labware collisions.

### Phase 3 — Wet run with dye

Replace your reagents with food dye or dyed water. Run the full protocol and visually inspect the plate against your expected layout. Quantify with a plate reader if needed.

### Phase 4 — Production run

Run with real reagents. Log the run ID, software version, and operator in your lab notebook. Archive the protocol file alongside your experimental data.

### Phase 5 — SOP integration

Once the protocol is validated, write or update your lab SOP to reference the protocol file version, required labware, and any manual steps that precede or follow the automated run.

---

## Hardware & Deck Setup

For detailed hardware instructions, see [`docs/hardware_setup.md`](docs/hardware_setup.md).

Key considerations:

- **Levelling** — the robot must be on a flat, vibration-free surface
- **Labware calibration** — calibrate each new labware type before its first use
- **Tip compatibility** — confirm tip lot numbers match the pipette spec
- **Deck slot conflicts** — use `scripts/validate_deck.py` to check for collisions before every run

---

## Configuration

Shared configuration lives in `config/`. Protocol scripts import from these files so that robot IP addresses, pipette slot assignments, and labware definitions are defined in one place.

```yaml
# config/robot_config.yaml
robot:
  ip: "169.254.xx.xx"       # OT-2 wired IP, or Flex hostname
  port: 31950

pipettes:
  left:  "p300_single_gen2"
  right: "p20_multi_gen2"

deck:
  tiprack_300:  1
  tiprack_20:   2
  source_plate: 4
  dest_plate:   5
  trash:        12
```

---

## Examples

The `examples/` folder contains:

- **`demo_workflow/`** — a full end-to-end example: protocol → run → parsed results
- **`sample_data/`** — example input CSV files and expected output layouts
- **`notebooks/`** — Jupyter notebooks for post-run analysis and visualization

---

## Contributing

We welcome new protocols, bug fixes, and documentation improvements. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

**Protocol submissions should include:**
- [ ] Working `protocol.py` (passes `opentrons_simulate` with no errors)
- [ ] `README.md` with purpose, reagents, and deck diagram
- [ ] Deck layout image or description
- [ ] Tested on at least one robot (OT-2 or Flex)

---

## License

[MIT License](LICENSE) — free to use, modify, and distribute with attribution.

---

*Maintained by Angie Aguirre-Tobar. Questions? Open an issue or email aaguirre@fredhutch.org.*
