from opentrons import protocol_api

# metadata
metadata = {
    "protocolName": "General_PCR_Prep_Flex",
    "description": "A small volume transfer program to prepare for PCR. Meant to utilize prepared PCR Master mix and DNA samples. Adapted for Flex with P50 pipette.",
    "author": "Angie Aguirre-Tobar (Adapted for Flex by OpentronsAI)"
}

requirements = {"robotType": "Flex", "apiLevel": "2.24"}


def add_parameters(parameters):

    # Choice of racks and plates used to store reagents & prepare samples
    parameters.add_str(
        variable_name="fnl",
        display_name="Final sample labware",
        description="Labware holding assembled IVTT reaction",
        choices=[
            {"display_name": "PCR Cooler", "value": "brand_pcr_cooler_96"},
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"}
        ],
        default="brand_pcr_cooler_96"
    )

    parameters.add_str(
        variable_name="src",
        display_name="Reagent source labware",
        description="Labware containing PCR reagents (Master Mix, Primers, dNTPs, etc.)",
        choices=[
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"}
        ],
        default="opentrons_24_tuberack_nest_1.5ml_snapcap"
    )

    # Type of reservoir for water
    parameters.add_str(
        variable_name="water",
        display_name="Water reservoir",
        description="Reservoir holding nuclease-free water",
        choices=[
            {"display_name": "150 mL reservoir", "value": "integra_reservoir_150ml"},
            {"display_name": "300 mL reservoir", "value": "integra_reservoir_300ml"}
        ],
        default="integra_reservoir_150ml"
    )

    # Volume of mastermix
    parameters.add_int(
        variable_name="vol_mm",
        display_name="Volume of Master Mix",
        description="Enter volume of master mix that will be used",
        default=10,
        minimum=2,
        maximum=25,
        unit="uL"
    )

    # T/F for primer set up
    parameters.add_bool(
        variable_name="prime",
        display_name="Primer Type",
        description="Do you have separate forward and reverse primers",
        default=True
    )

    # Volume of primer solution
    parameters.add_float(
        variable_name="prime_mix",
        display_name="Volume of Primer Mix",
        description="Enter volume of Primer mix",
        default=5.0,
        minimum=0,
        maximum=10,
        unit="uL"
    )

    # Volume of forward primer
    parameters.add_float(
        variable_name="fwd_prime",
        display_name="Volume of Forward Primer",
        description="Enter the volume needed for your forward primer",
        default=2.5,
        minimum=0,
        maximum=25,
        unit="uL"
    )

    # Volume of reverse primer
    parameters.add_float(
        variable_name="rev_prime",
        display_name="Volume of Reverse Primer",
        description="Enter the volume needed for your reverse primer",
        default=2.5,
        minimum=0,
        maximum=25,
        unit="uL"
    )

    # Final reaction volume
    parameters.add_float(
        variable_name="final_vol",
        display_name="Final reaction volume",
        default=25,
        minimum=12.5,
        maximum=50,
        unit="uL"
    )

    # Number of final samples (minimum need (-) control and plasmid)
    parameters.add_int(
        variable_name="sample_num",
        display_name="Number of samples to prepare",
        default=2,
        minimum=2,
        maximum=96
    )

    # Volume of plasmid add-ins
    for i in range(1, 8):
        parameters.add_float(
            variable_name=f"vol{i}",
            display_name=f"Volume of {i}th plasmid",
            default=1,
            minimum=0,
            maximum=50
        )


def run(protocol: protocol_api.ProtocolContext):

    # Load labware - using Flex deck slots
    source_plate = protocol.load_labware(protocol.params.src, "D2")
    location_plate = protocol.load_labware(protocol.params.fnl, "D3")
    water_reservoir = protocol.load_labware(protocol.params.water, "D1")

    # Load trash bin
    trash = protocol.load_trash_bin("A3")

    # Loading tip racks for Flex P50 pipette
    tipracks_50 = [
        protocol.load_labware("opentrons_flex_96_tiprack_50ul", slot)
        for slot in ["C1", "C2"]
    ]

    # Load P50 single-channel pipette
    p50 = protocol.load_instrument(
        "flex_1channel_50",
        mount="left",
        tip_racks=tipracks_50
    )

    # Configure all of the user inputs
    samp_num = protocol.params.sample_num
    primetime = protocol.params.prime
    mmix = protocol.params.vol_mm
    target_vol = protocol.params.final_vol

    primer_vols = {
        "prime_mix": protocol.params.prime_mix,
        "fwd_prime": protocol.params.fwd_prime,
        "rev_prime": protocol.params.rev_prime
    }

    # Determine what kind of primer mix is used
    if primetime:  # separate primers
        primer_vols["prime_mix"] = 0
    else:  # premixed primers
        primer_vols["fwd_prime"] = 0
        primer_vols["rev_prime"] = 0

    total_primer_volume = sum(primer_vols.values())

    plasmid_vols = [
        getattr(protocol.params, f"vol{i}") for i in range(1, 9)
    ]

    water = water_reservoir["A1"]

    # Set pipette flow rate
    p50.flow_rate.aspirate = 20
    p50.flow_rate.dispense = 20
    p50.flow_rate.blow_out = 100

    # Actual run - all transfers use P50 pipette
    for i in range(samp_num):

        dest = location_plate.wells()[i]
        plasmid_volume = plasmid_vols[i]

        # Calculate water per sample
        non_water_volume = mmix + total_primer_volume + plasmid_volume
        water_volume = target_vol - non_water_volume

        if water_volume < 0:
            raise RuntimeError(
                f"Final volume too small! Sample {i+1} exceeds target volume."
            )

        primer_sources = {
            "prime_mix": source_plate["A2"],
            "fwd_prime": source_plate["A3"],
            "rev_prime": source_plate["A4"]
        }

        # Add Master Mix
        p50.transfer(mmix, source_plate["A1"], dest, new_tip="always")

        # Add primers
        for primer_name, vol in primer_vols.items():
            if vol > 0:
                p50.transfer(
                    vol,
                    primer_sources[primer_name],
                    dest,
                    new_tip="always"
                )

        # Add plasmid (B1–B8)
        if plasmid_volume > 0:
            p50.transfer(
                plasmid_volume,
                source_plate[f"B{i+1}"],
                dest,
                new_tip="always"
            )

        # Add water
        if water_volume > 0:
            p50.transfer(
                water_volume,
                water,
                dest,
                new_tip="always"
            )

        # Mix final reaction
        p50.pick_up_tip()
        mix_volume = min(50, target_vol)  # P50 max volume is 50 µL
        p50.mix(5, mix_volume, dest)
        p50.drop_tip()