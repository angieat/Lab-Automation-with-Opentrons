from opentrons import protocol_api

metadata = {
    "protocolName": "Media_Dilution_Set_V3_Modified",
    "author": "Angie",
    "description": "Dilution of compound solutions with component-specific diluent assignment using single-channel diluent distribution and multi-channel serial dilution.",
    "source": "OpentronsAI"
}

requirements = {
    "robotType": "OT-2",
    "apiLevel": "2.24"
}

MIX_BEFORE_REPS = 3
MIX_AFTER_REPS = 3
MIX_AFTER_VOLUME = 50  # µL

P300_ASPIRATE_RATE = 46
P300_DISPENSE_RATE = 46
P300_BLOWOUT_RATE = 50

def add_parameters(parameters):
    parameters.add_str(
        variable_name="fnl",
        display_name="Final 96-well labware",
        description="Labware holding assembled IVTT reaction",
        choices=[
            {"display_name": "PCR Cooler", "value": "brand_pcr_cooler_96"},
            {"display_name": "2000ul 96-well plate", "value": "thomsoninstrumentcompany_96_wellplate_2000ul"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"},
        ],
        default="axygen_96_wellplate_500ul"
    )

    parameters.add_int(
        variable_name="num_plates",
        display_name="Number of Plates",
        description="How many plates of serially diluted compounds are you prepping?",
        minimum=1,
        maximum=4,
        default=1
    )

    parameters.add_int(
        variable_name="num_components",
        display_name="Number of Components",
        description="Number of different components to dilute (rows to process)",
        minimum=1,
        maximum=8,
        default=8
    )

    parameters.add_str(
        variable_name="src",
        display_name="Reagent source labware",
        description="Labware containing IVTT reagents",
        choices=[
            {"display_name": "Custom 15 mL Rack", "value": "opentrons_15_tuberack_eppendorf_15ml_conical"},
            {"display_name": "Custom 15mL & 50mL Rack", "value": "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical"},
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "12-well 22ml Reservoir", "value": "usascientific_12_reservoir_22ml"}
        ],
        default="usascientific_12_reservoir_22ml"
    )

    parameters.add_str(
        variable_name="dilutant_src",
        display_name="Diluent Labware Type",
        description="Reservoir holding diluents (buffers & water)",
        choices=[
            {"display_name": "150 mL reservoir", "value": "integra_reservoir_150ml"},
            {"display_name": "300 mL reservoir", "value": "integra_reservoir_300ml"},
            {"display_name": "12-well 22ml Reservoir", "value": "usascientific_12_reservoir_22ml"}
        ],
        default="usascientific_12_reservoir_22ml"
    )

    parameters.add_str(
        variable_name="component_diluent_pattern",
        display_name="Diluent Pattern",
        description="Enter pattern (e.g., '1,1,1,2') mapping each component to a diluent well index (1–12).",
        choices=[
            {"display_name": "Custom Input", "value": "1,1,1,2,1,1,1,1"}
        ],
        default="1,1,1,2,1,1,1,1"
    )


def run(protocol: protocol_api.ProtocolContext):

    num_plates = protocol.params.num_plates
    num_components = protocol.params.num_components
    component_diluent_pattern = protocol.params.component_diluent_pattern

    try:
        pattern_str = component_diluent_pattern.strip()
        diluent_assignments = [int(x.strip()) - 1 for x in pattern_str.split(',')]

        if any(x < 0 for x in diluent_assignments):
            raise ValueError("All diluent numbers must be positive integers")

        if len(diluent_assignments) < num_components:
            raise ValueError(
                f"Pattern has {len(diluent_assignments)} values but {num_components} components specified."
            )

        diluent_assignments = diluent_assignments[:num_components]

        if max(diluent_assignments) >= 12:
            raise ValueError("Diluent index exceeds reservoir capacity (12 wells max).")

    except ValueError as e:
        raise ValueError(f"Invalid diluent pattern '{component_diluent_pattern}': {str(e)}")

    src_plate = protocol.load_labware(protocol.params.src, "1")

    plate_slots = ["2", "3", "6", "9"]
    final_plates = [
        protocol.load_labware(protocol.params.fnl, plate_slots[i])
        for i in range(num_plates)
    ]

    tiprack300 = [
        protocol.load_labware("opentrons_96_tiprack_300ul", slot)
        for slot in ["10", "7"]
    ]

    tiprack1000 = [
        protocol.load_labware("opentrons_96_tiprack_1000ul", slot)
        for slot in ["11", "8"]
    ]

    dilutant_reserv = protocol.load_labware(protocol.params.dilutant_src, "5")

    right = protocol.load_instrument("p300_multi_gen2", mount="right", tip_racks=tiprack300)
    left = protocol.load_instrument("p1000_single_gen2", mount="left", tip_racks=tiprack1000)

    right.flow_rate.aspirate = P300_ASPIRATE_RATE
    right.flow_rate.dispense = P300_DISPENSE_RATE
    right.flow_rate.blow_out = P300_BLOWOUT_RATE

    left.flow_rate.aspirate = 46
    left.flow_rate.dispense = 46
    left.flow_rate.blow_out = 50

    protocol.comment("Protocol started")

    for plate_idx, final_plate in enumerate(final_plates):
        protocol.comment(f"Processing plate {plate_idx + 1}")

        for i in range(num_components):
            row = final_plate.rows()[i]
            left.transfer(450, src_plate.wells()[i], row[0], new_tip="always")

        for col_idx in range(1, 12):
            col = final_plate.columns()[col_idx]

            for row_idx in range(num_components):
                diluent_well_idx = diluent_assignments[row_idx]
                diluent_source = dilutant_reserv.wells()[diluent_well_idx]

                left.transfer(200, diluent_source, col[row_idx], new_tip="always")

        right.pick_up_tip()

        for col_idx in range(0, 11):
            source_col = final_plate.columns()[col_idx]
            dest_col = final_plate.columns()[col_idx + 1]

            right.transfer(
                200,
                source_col,
                dest_col,
                mix_after=(MIX_AFTER_REPS, MIX_AFTER_VOLUME),
                new_tip="never"
            )

        right.drop_tip()

    protocol.comment("Protocol complete")
