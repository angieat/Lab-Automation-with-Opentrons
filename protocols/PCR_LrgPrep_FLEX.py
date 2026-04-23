from opentrons import protocol_api

# metadata
metadata = {
    "protocolName": "Large-scale PCR Reactions on FLEX",
    "description": "A small volume transfer program to prepare for PCR. Meant to utilize prepared PCR Master mix and DNA samples. Adapted for Flex with P50 pipette.",
    "author": "Angie Aguirre-Tobar (Adapted for Flex by OpentronsAI)",
    "source": "OpentronsAI"
}

requirements = {"robotType": "Flex", "apiLevel": "2.25"}


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
        description="Labware containing PCR reagents (Master Mix, Primers, etc.)",
        choices=[
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"},
            {"display_name": "IsoFreeze 1.5 mL tuberack", "value": "isofreeze_24_tuberack"}
        ],
        default="opentrons_24_tuberack_nest_1.5ml_snapcap"
    )

    parameters.add_str(
        variable_name="dna",
        display_name="DNA source labware",
        description="Labware containing amplification DNA material",
        choices=[
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"},
            {"display_name": "PCR Cooler", "value": "brand_pcr_cooler_96"},
            {"display_name": "IsoFreeze 1.5 mL tuberack", "value": "isofreeze_24_tuberack"}
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
        description="Enter volume needed for forward primer",
        default=2.5,
        minimum=0,
        maximum=25,
        unit="uL"
    )

    # Volume of reverse primer
    parameters.add_float(
        variable_name="rev_prime",
        display_name="Volume of Reverse Primer",
        description="Enter volume needed for reverse primer",
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

    # Control parameters
    parameters.add_bool(
        variable_name="include_neg_ctrl",
        display_name="Include Negative Control",
        description="Include negative control (water instead of DNA)",
        default=True
    )

    parameters.add_bool(
        variable_name="include_pos_ctrl",
        display_name="Include Positive Control",
        description="Include positive control (DNA from A1 of plasmid rack)",
        default=True
    )

    # Volume of plasmids based on ctrl/experimental status
    parameters.add_float(
        variable_name="ctrl_vol",
        display_name="Volume of Control DNA/Water",
        description="Volume for controls (water for neg, DNA for pos)",
        default=1,
        minimum=0,
        maximum=50,
        unit="uL"
    )

    parameters.add_float(
        variable_name="plas_vol",
        display_name="Volume of Experimental DNA",
        description="Volume of experimental DNA",
        default=1,
        minimum=0,
        maximum=50,
        unit="uL"
    )

    # Number of experimental samples
    parameters.add_int(
        variable_name="sample_num",
        display_name="Number of experimental samples",
        description="Number of experimental samples (excluding controls)",
        default=2,
        minimum=1,
        maximum=94
    )


def run(protocol: protocol_api.ProtocolContext):

    # Load labware - using Flex deck slots
    source_plate = protocol.load_labware(protocol.params.src, "D2")
    dna_plate = protocol.load_labware(protocol.params.dna, "C3")
    location_plate = protocol.load_labware(protocol.params.fnl, "D3")
    water_reservoir = protocol.load_labware(protocol.params.water, "D1")

    # Load trash bin
    trash = protocol.load_trash_bin("A3")

    # Loading tip racks for Flex P50 pipette - 6 racks for 96 samples
    tipracks_50 = [
        protocol.load_labware("opentrons_flex_96_tiprack_50ul", slot)
        for slot in ["C1", "C2", "B1", "B2", "A1", "A2"]
    ]

    # Load P50 single-channel pipette
    p50 = protocol.load_instrument(
        "flex_1channel_50",
        mount="left",
        tip_racks=tipracks_50
    )

    # Configure all of the user inputs
    samp_num = protocol.params.sample_num
    include_neg = protocol.params.include_neg_ctrl
    include_pos = protocol.params.include_pos_ctrl
    primetime = protocol.params.prime
    mmix = protocol.params.vol_mm
    target_vol = protocol.params.final_vol
    ctrl_vol = protocol.params.ctrl_vol
    exp_vol = protocol.params.plas_vol

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

    water = water_reservoir["A1"]

    # Set pipette flow rate
    p50.flow_rate.aspirate = 20
    p50.flow_rate.dispense = 20
    p50.flow_rate.blow_out = 100

    # Calculate total number of samples including controls
    total_samples = samp_num
    if include_neg:
        total_samples += 1
    if include_pos:
        total_samples += 1

    # Primer sources
    primer_sources = {
        "prime_mix": source_plate["A2"],
        "fwd_prime": source_plate["A3"],
        "rev_prime": source_plate["A4"]
    }

    # Collect all destination wells and water volumes for batch water addition
    water_destinations = []
    water_volumes = []
    
    # Track current well index
    current_well = 0

    # Calculate water volumes for all samples
    if include_neg:
        # Negative control: all water (no DNA)
        non_water_volume = mmix + total_primer_volume
        total_water = target_vol - non_water_volume
        water_destinations.append(location_plate.wells()[current_well])
        water_volumes.append(total_water)
        current_well += 1

    if include_pos:
        # Positive control: water + DNA
        non_water_volume = mmix + total_primer_volume + ctrl_vol
        water_volume = target_vol - non_water_volume
        water_destinations.append(location_plate.wells()[current_well])
        water_volumes.append(water_volume)
        current_well += 1

    # Experimental samples
    for i in range(samp_num):
        non_water_volume = mmix + total_primer_volume + exp_vol
        water_volume = target_vol - non_water_volume
        water_destinations.append(location_plate.wells()[current_well])
        water_volumes.append(water_volume)
        current_well += 1

    # STEP 1: Add all water using ONE tip (major tip savings!)
    p50.transfer(water_volumes, water, water_destinations, new_tip="once")

    # Reset well counter
    current_well = 0

    # STEP 2: Process negative control (if included)
    if include_neg:
        dest = location_plate.wells()[current_well]

        # Add Master Mix with new tip
        p50.transfer(mmix, source_plate["A1"], dest, new_tip="always")

        # Add primers with new tips
        for primer_name, vol in primer_vols.items():
            if vol > 0:
                p50.transfer(vol, primer_sources[primer_name], dest, new_tip="always")
       
        p50.pick_up_tip()
        mix_volume = min(50, target_vol * 0.8)
        p50.mix(5, mix_volume, dest)
        p50.drop_tip()
        
        current_well += 1

    # STEP 3: Process positive control (if included)
    if include_pos:
        dest = location_plate.wells()[current_well]

        # Add Master Mix with new tip
        p50.transfer(mmix, source_plate["A1"], dest, new_tip="always")

        # Add primers with new tips
        for primer_name, vol in primer_vols.items():
            if vol > 0:
                p50.transfer(vol, primer_sources[primer_name], dest, new_tip="always")

        # Add positive control DNA from A1 of DNA plate
        if ctrl_vol > 0:
            p50.transfer(ctrl_vol, dna_plate["A1"], dest, new_tip="always")

        p50.pick_up_tip()
        mix_volume = min(50, target_vol * 0.8)
        p50.mix(5, mix_volume, dest)
        p50.drop_tip()

        current_well += 1

    # STEP 4: Process experimental samples
    # DNA plate indexing: A1 is positive control, A2-onwards are experimental samples
    dna_start_index = 1  # Start from A2 (index 1) for experimental samples

    for i in range(samp_num):
        dest = location_plate.wells()[current_well]

        # Add Master Mix with new tip
        p50.transfer(mmix, source_plate["A1"], dest, new_tip="always")

        # Add primers with new tips
        for primer_name, vol in primer_vols.items():
            if vol > 0:
                p50.transfer(vol, primer_sources[primer_name], dest, new_tip="always")

        # Add experimental DNA from DNA plate (starting from A2)
        if exp_vol > 0:
            dna_source = dna_plate.wells()[dna_start_index]
            p50.transfer(exp_vol, dna_source, dest, new_tip="always")

        # Mix final reaction
        p50.pick_up_tip()
        mix_volume = min(50, target_vol*0.8)
        p50.mix(5, mix_volume, dest)
        p50.drop_tip()

        current_well += 1