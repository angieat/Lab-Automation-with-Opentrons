from opentrons import protocol_api

metadata = {
    "protocolName": "PURExpress In-Vitro Transcription and Translation Assemble",
    "author": "Angie Aguirre-Tobar",
    "description": "PURExpress IVTT reactants preparation. MUST BE DONE UNDER STERILE CONDITIONS",
    "source": "OpentronsAI"
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
            {"display_name": "Custom 15 mL Rack", "value": "opentrons_15_tuberack_eppendorf_15ml_conical"},
            {"display_name": "Custom 15mL & 50mL Rack", "value": "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical"},
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "2000ul 96-well plate", "value": "thomsoninstrumentcompany_96_wellplate_2000ul"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"}
        ],
        default="brand_pcr_cooler_96"
    )
    parameters.add_str(
        variable_name="src",
        display_name="Reagent source labware",
        description="Labware containing IVTT reagents",
        choices=[
            {"display_name": "PCR Cooler", "value": "brand_pcr_cooler_96"},
            {"display_name": "Custom 15 mL Rack", "value": "opentrons_15_tuberack_eppendorf_15ml_conical"},
            {"display_name": "Custom 15mL & 50mL Rack", "value": "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical"},
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "2000ul 96-well plate", "value": "thomsoninstrumentcompany_96_wellplate_2000ul"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"}
        ],
        default="brand_pcr_cooler_96"
    )
    parameters.add_str(
        variable_name="plsmd",
        display_name="Plasmid Labware",
        description="Labware containing plasmid DNA",
        choices=[
            {"display_name": "PCR Cooler", "value": "brand_pcr_cooler_96"},
            {"display_name": "Custom 15 mL Rack", "value": "opentrons_15_tuberack_eppendorf_15ml_conical"},
            {"display_name": "Custom 15mL & 50mL Rack", "value": "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical"},
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "2000ul 96-well plate", "value": "thomsoninstrumentcompany_96_wellplate_2000ul"},
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
    # Positive or Negative status for Control
    parameters.add_str(
        variable_name="pn_ctrl",
        display_name="First control type",
        description="Type of control prepared first",
        choices=[
            {"display_name": "Positive", "value": "positive"},
            {"display_name": "Negative", "value": "negative"}
        ],
        default="negative"
    )
    # T/F for a second control
    parameters.add_bool(
        variable_name="scnd_ctrl",
        display_name="Second control",
        description="Include both positive and negative controls",
        default=True
    )
    # T/F for Disulfide Bond Enhancer
    parameters.add_bool(
        variable_name="add_tf",
        display_name="Are there add-ins?",
        description="Di-sulfide enhancer, RNAse inhibitor, etc.",
        default=True
    )
    # Number of add-ins including the disulfide bond enhancer
    parameters.add_int(
        variable_name="add_ins",
        display_name="Number of vials of add-ins",
        default=2,
        minimum=1,
        maximum=4
    )
    # Volume of first add-in
    parameters.add_float(
        variable_name="vol1",
        display_name="Volume of 1st add-in",
        default=1,
        minimum=0,
        maximum=50
    )
    # Volume of second add-in
    parameters.add_float(
        variable_name="vol2",
        display_name="Volume of 2nd add-in",
        default=1,
        minimum=0,
        maximum=50
    )
    # Volume of third add-in
    parameters.add_float(
        variable_name="vol3",
        display_name="Volume of 3rd add-in",
        default=1,
        minimum=0,
        maximum=50
    )
    # Volume of fourth add-in
    parameters.add_float(
        variable_name="vol4",
        display_name="Volume of 4th add-in",
        default=1,
        minimum=0,
        maximum=50
    )


def run(protocol: protocol_api.ProtocolContext):
    # Define reagent volumes as constants
    SOLUTION_A_VOL = 10.0
    SOLUTION_B_VOL = 7.5
    PLASMID_VOL = 2.0
    
    # Load labware
    tipracks = [
        protocol.load_labware("opentrons_flex_96_tiprack_50ul", slot)
        for slot in ["A1", "A2", "B1", "B2", "C1", "C3"]  # Added more tip racks
    ]
    pipette = protocol.load_instrument(
        "flex_1channel_50",
        mount="left",
        tip_racks=tipracks
    )
    source_plate = protocol.load_labware(
        load_name=protocol.params.src,
        location="D1",
        namespace="custom_labware"
    )
    loc_plate = protocol.load_labware(
        load_name=protocol.params.fnl,
        location="D3",
        namespace="custom_labware"
    )
    plasmid_plate = protocol.load_labware(
        load_name=protocol.params.plsmd,
        location="D2",
    )
    water_source = protocol.load_labware(
        load_name=protocol.params.water,
        location="C2",
        namespace="custom_beta"
    )
    trash = protocol.load_trash_bin("A3")

    # Incorporate all of the user input variables
    addins = protocol.params.add_tf
    ctrl_type = protocol.params.pn_ctrl
    scnd_ctrl = protocol.params.scnd_ctrl
    sample_num = protocol.params.sample_num

    # Validate second control configuration
    if scnd_ctrl and sample_num < 3:
        raise RuntimeError(
            "Need at least 3 samples when using two controls "
            "(one for each control type plus at least one experiment)."
        )

    solution_a = source_plate.rows()[0]
    solution_b = source_plate.rows()[1]

    addin_rows = [
        source_plate.rows()[2],
        source_plate.rows()[3],
        source_plate.rows()[4],
        source_plate.rows()[5]
    ]

    addin_volumes = [
        protocol.params.vol1,
        protocol.params.vol2,
        protocol.params.vol3,
        protocol.params.vol4
    ]

    active_addins = list(zip(
        addin_rows[:protocol.params.add_ins],
        addin_volumes[:protocol.params.add_ins]
    ))

    # Calculate volumes
    target_vol = protocol.params.final_vol
    total_addin_volume = sum(vol for _, vol in active_addins)
    non_water_volume = (SOLUTION_A_VOL + SOLUTION_B_VOL + total_addin_volume + PLASMID_VOL)
    water_volume = target_vol - non_water_volume

    if water_volume < 0:
        raise RuntimeError(
            f"Final volume too small! "
            f"Non-water volume = {non_water_volume} µL, "
            f"final volume = {protocol.params.final_vol} µL."
        )

    # Calculate required tips
    transfers_per_sample = 3 + protocol.params.add_ins + 1  # A, B, add-ins, plasmid/water, final water
    total_tips_needed = sample_num * transfers_per_sample

    if total_tips_needed > len(tipracks) * 96:
        raise RuntimeError(
            f"Insufficient tips! Need {total_tips_needed}, have {len(tipracks) * 96}. "
            f"Add more tip racks or reduce sample number."
        )

    # Capture images throughout the run
    try:
        protocol.capture_image(home_before=True, filename="IVTT_Run")
    except Exception:
        protocol.comment("Image capture skipped")

    # Determine the type of controls and samples being prepared
    sample_roles = []
    sample_roles.append(ctrl_type)

    if scnd_ctrl:
        opposite = "positive" if ctrl_type == "negative" else "negative"
        sample_roles.append(opposite)
    remaining = sample_num - len(sample_roles)
    sample_roles.extend(["experiment"] * remaining)

    water = water_source.wells_by_name()["A1"]
    exp_idx = 0

    positive_plasmid = plasmid_plate.wells_by_name()["A1"]
    experiment_plasmids = plasmid_plate.wells()[1:]

    if len(experiment_plasmids) < sample_roles.count("experiment"):
        raise RuntimeError("Not enough plasmid wells for experiment samples.")

    # Set flow rates once before loop
    pipette.flow_rate.aspirate = 5
    pipette.flow_rate.dispense = 10
    pipette.flow_rate.blow_out = 100

    # Prepare each sample with solution a, solution b, any add-ins and water
    for i, role in enumerate(sample_roles):
        dest = loc_plate.wells()[i]

        # Add Solution A
        pipette.transfer(
            volume=SOLUTION_A_VOL,
            source=solution_a[i],
            dest=dest,
            new_tip="always"
        )
        
        # Add Solution B
        pipette.transfer(
            volume=SOLUTION_B_VOL,
            source=solution_b[i],
            dest=dest,
            new_tip="always"
        )
        
        # Add any add-ins
        if addins:
            for addin_row, addin_vol in active_addins:
                pipette.transfer(
                    addin_vol,
                    addin_row[i],
                    dest,
                    new_tip="always"
                )
        
        # Add plasmid or water substitute with fresh tip (prevents contamination)
        if role == "positive":
            pipette.transfer(
                PLASMID_VOL,
                positive_plasmid,
                dest,
                new_tip="always"
            )
        elif role == "experiment":
            pipette.transfer(
                PLASMID_VOL,
                experiment_plasmids[exp_idx],
                dest,
                new_tip="always"
            )
            exp_idx += 1
        elif role == "negative":
            pipette.transfer(
                PLASMID_VOL,
                water,
                dest,
                new_tip="always"
            )
        
        # Fill up samples to final volume with water
        pipette.transfer(
            water_volume,
            water,
            dest,
            new_tip="always"
        )

        # Mix the final reaction
        pipette.pick_up_tip()
        pipette.mix(5, 20, dest)
        pipette.drop_tip()