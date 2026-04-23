from opentrons import protocol_api

metadata = {
    "protocolName": "Media Distribution into Culturing Labware",
    "author": "Angie",
    "description": "The dispense of media/solvent into 96-well, 1.5/15/50 ml tubes and 12-well reservoirs"
}

requirements = {"robotType": "OT-2", "apiLevel": "2.24"}

MIX_BEFORE_REPS = 3
MIX_AFTER_REPS = 3
MIX_AFTER_VOLUME = 50  # µL

P300_ASPIRATE_RATE = 46
P300_DISPENSE_RATE = 46
P300_BLOWOUT_RATE = 50

def add_parameters(parameters):
    parameters.add_str(
        variable_name="fnl_type",
        display_name="Final Destination Plate Type",
        default="thomsoninstrumentcompany_96_wellplate_2000ul",
        choices=[
            {"display_name": "PCR Cooler", "value": "brand_pcr_cooler_96"},
            {"display_name": "Custom 15 mL Rack", "value": "opentrons_15_tuberack_eppendorf_15ml_conical"},
            {"display_name": "Custom 15mL & 50mL Rack", "value": "opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical"},
            {"display_name": "Custom 1.5 mL Rack", "value": "opentrons_24_tuberack_nest_1.5ml_snapcap"},
            {"display_name": "2000ul 96-well plate", "value": "thomsoninstrumentcompany_96_wellplate_2000ul"},
            {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"}
        ]
    )
    
    parameters.add_int(
        variable_name="fnl_num",
        display_name="Number of sample plates",
        minimum=1,
        maximum=4,
        default=1
    )
    
    parameters.add_str(
        variable_name="res_type",
        display_name="Type of reservoir with media",
        choices=[
            {"display_name": "150 mL reservoir", "value": "integra_reservoir_150ml"},
            {"display_name": "300 mL reservoir", "value": "integra_reservoir_300ml"}
        ],
        default="integra_reservoir_150ml"
    )
    
    parameters.add_int(
        variable_name="res_num",
        display_name="Number of different media",
        minimum=1,
        maximum=2,
        default=1
    )
    
    parameters.add_bool(
        variable_name="pattern",
        display_name="Media Distribution Pattern",
        description="Use more than one media in a singular prep",
        default=False
    )
    
    parameters.add_str(
        variable_name="well_pattern",
        display_name="Pattern for plate prep",
        description="Distribution of media on a plate",
        choices=[
            {"display_name": "Half & half (Vertical)", "value": "1,2,3,4,5,6,7,8,9,10,11,12"},
            {"display_name": "Half & half (Horizontal)", "value": "A,B,C,D,E,F,G,H"},
            {"display_name": "None", "value": "none"}
        ],
        default="none"
    )
    
    # Volume input parameter
    parameters.add_int(
        variable_name="transfer_volume",
        display_name="Transfer Volume (µL)",
        description="Volume to transfer per well (1-50,000 µL)",
        minimum=1,
        maximum=50000,
        default=900
    )

def run(protocol: protocol_api.ProtocolContext):
    # Access runtime parameters
    num_plates = protocol.params.fnl_num
    num_res = protocol.params.res_num
    plate_type = protocol.params.fnl_type
    reservoir_type = protocol.params.res_type
    use_pattern = protocol.params.pattern
    pattern_type = protocol.params.well_pattern
    transfer_vol = protocol.params.transfer_volume
    
    # Load tip racks
    tiprack300 = [
        protocol.load_labware("opentrons_96_tiprack_300ul", slot)
        for slot in ["10", "7"]
    ]
    tiprack1000 = [
        protocol.load_labware("opentrons_96_tiprack_1000ul", slot)
        for slot in ["11", "8"]
    ]
    
    # Load reservoirs based on parameter
    reservoirs = [
        protocol.load_labware(reservoir_type, slot)
        for slot in ["1", "4"]
    ]
    
    # Load culture plates based on number specified
    culture_plates = []
    plate_slots = [2, 3, 5, 6]
    for i in range(num_plates):
        plate = protocol.load_labware(plate_type, plate_slots[i])
        culture_plates.append(plate)
    
    # Load pipettes
    right = protocol.load_instrument("p300_multi_gen2", mount="right", tip_racks=tiprack300)
    left = protocol.load_instrument("p1000_single_gen2", mount="left", tip_racks=tiprack1000)
    
    # Distribute media based on pattern settings
    if use_pattern and pattern_type != "none":
        # Handle patterned distribution
        if "," in pattern_type:
            # Parse pattern
            pattern_elements = pattern_type.split(",")
            
            # Check if it's a column pattern (numbers) or row pattern (letters)
            if pattern_elements[0].isdigit():
                # Vertical (column) pattern
                mid_point = len(pattern_elements) // 2
                
                for plate in culture_plates:
                    # First media to first half of columns
                    left.pick_up_tip()
                    for col_idx in range(mid_point):
                        left.transfer(
                            transfer_vol,
                            reservoirs[0].wells()[0],
                            plate.rows()[0][col_idx:col_idx+1],
                            mix_after=(MIX_AFTER_REPS, MIX_AFTER_VOLUME),
                            new_tip="never"
                        )
                    left.drop_tip()
                    
                    # Second media to second half (if available)
                    if num_res > 1:
                        left.pick_up_tip()
                        for col_idx in range(mid_point, len(pattern_elements)):
                            left.transfer(
                                transfer_vol,
                                reservoirs[1].wells()[0],
                                plate.rows()[0][col_idx:col_idx+1],
                                mix_after=(MIX_AFTER_REPS, MIX_AFTER_VOLUME),
                                new_tip="never"
                            )
                        left.drop_tip()
            else:
                # Horizontal (row) pattern
                mid_point = len(pattern_elements) // 2
                
                for plate in culture_plates:
                    # First media to first half of rows
                    left.pick_up_tip()
                    for row_idx in range(mid_point):
                        left.transfer(
                            transfer_vol,
                            reservoirs[0].wells()[0],
                            plate.rows()[row_idx],
                            mix_after=(MIX_AFTER_REPS, MIX_AFTER_VOLUME),
                            new_tip="never"
                        )
                    left.drop_tip()
                    
                    # Second media to second half (if available)
                    if num_res > 1:
                        left.pick_up_tip()
                        for row_idx in range(mid_point, len(pattern_elements)):
                            left.transfer(
                                transfer_vol,
                                reservoirs[1].wells()[0],
                                plate.rows()[row_idx],
                                mix_after=(MIX_AFTER_REPS, MIX_AFTER_VOLUME),
                                new_tip="never"
                            )
                        left.drop_tip()
    else:
        # Standard distribution without pattern
        for plate_idx, plate in enumerate(culture_plates):
            # Determine which reservoir to use
            reservoir_idx = min(plate_idx, num_res - 1)
            
            # Distribute to all rows
            left.pick_up_tip()
            for i in range(8):
                culture_row = plate.rows()[i]
                left.transfer(
                    transfer_vol,
                    reservoirs[reservoir_idx].wells()[0],
                    culture_row[:],
                    mix_after=(MIX_AFTER_REPS, MIX_AFTER_VOLUME),
                    new_tip="never"
                )
            left.drop_tip()