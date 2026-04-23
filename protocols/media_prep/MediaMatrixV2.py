from opentrons import protocol_api
import random

metadata = {
    "protocolName": "Media Prep with Water Top-up",
    "author": "Angie",
    "description": "Culture Media Preparation with CSV upload and plate-type input" 
}

requirements = {"robotType": "Flex", "apiLevel": "2.24"}

def add_parameters(parameters):
    parameters.add_str(
        variable_name="plate_type",
        display_name="Source Plate Type",
        choices=[
        {"display_name": "500ul 96-well plate", "value": "axygen_96_wellplate_500ul"},
        {"display_name": "2000ul 96-well plate", "value": "thomsoninstrumentcompany_96_wellplate_2000ul"},
    ],
        default="thomsoninstrumentcompany_96_wellplate_2000ul",
    )
    parameters.add_csv_file(
        variable_name="cherrypicking_wells",
        display_name="Cherrypicking Wells",
        description="CSV with columns: wel.num, volume, dest"
    )
    parameters.add_float(
        variable_name="target_volume",
        display_name="Target Well Volume (µL)",
        description="Final desired volume in each well after water addition",
        default=100.0,
        minimum = 1,
        maximum = 100
    )

def run(protocol: protocol_api.ProtocolContext):
    tipracks = [
        protocol.load_labware("opentrons_flex_96_tiprack_50ul", slot)
        for slot in ["D1","C1", "B1", "A1"]
    ]
    pipette = protocol.load_instrument("flex_1channel_50", mount="left", tip_racks=tipracks)

    source_plate = protocol.load_labware(protocol.params.plate_type, "D2")
    dest_plate = protocol.load_labware("thomsoninstrumentcompany_96_wellplate_2000ul", "C2")
    water_reservoir = protocol.load_labware("usascientific_12_reservoir_22ml", "C3")
    water = water_reservoir.wells()[11]

    trash = protocol.load_trash_bin("A3")

    well_data = protocol.params.cherrypicking_wells.parse_as_csv()
    target_vol = protocol.params.target_volume

    # Identify source plates
    #source_slots = list(set(row[0] for row in final_well_data[1:]))  # skip header
    #source_plates = {slot: protocol.load_labware(protocol.params.plate_type, slot) for slot in source_slots}
    
    # Prepare destination wells
    dest_wells = dest_plate.wells()[:len(well_data)-1]  # skip header
    well_tracking = {}

    # Transfer stock solution + water top-up
    pipette.pick_up_tip()
    prev_well = ""
    for i, row in enumerate(well_data[1:]):  # skip header
        source_well, vol, dest_well = row
        vol = float(vol)
        #source_plate = source_plates[source_slot]
        #source_well = source_plate.wells_by_name()[source_well_name]

        
        if source_well != "WATER":
            if prev_well == "WATER":
                pipette.drop_tip()
            pipette.pick_up_tip()
            # Transfer stock solution
            pipette.transfer(vol, source_plate.wells(source_well), dest_plate.wells(dest_well), new_tip="never")
            pipette.drop_tip()
        else:
            # Add water to reach target volume
            pipette.transfer(vol, water, dest_plate.wells(dest_well), new_tip="never")


        # Log well contents
        well_tracking[dest_well] = {
            "source_well": source_well,
            "stock_volume": vol,
            "dest_well": dest_well
        }
        prev_well = source_well