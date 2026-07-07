from opentrons import protocol_api

metadata  = {
    "protocolName": "Multi-Plate Media Component Serial Dilution",
    "author" : "Angie",
    "description" : """Automated Prep of 4x 96-well plate that contains diluted stock solution of M9 media components.
                        This protocol allows you to use 1-8 components in dilution series, choose your dilution factor,
                        and calculates final concentration of diluted plates. To custome your intial concentration,
                        edit the protocol in Python3. For details visit: 
                        https://www.notion.so/sinnottarmstronglab/Protocol-List-28e7283b198a80d5b843c0676acde854?source=copy_link"""
    }

#load in the type of robot this protocol is for
requirements = {"robotType" : "OT-2", "apiLevel": "2.24"}

def add_parameters(parameters: protocol_api.ParameterContext):
    parameters.add_int(
        variable_name = "plate_num",
        display_name = "Number of plates (1-4)",
        description = (
            "Enter the number of plates" 
            "in dock slot 2, 3, 5, and 6." 
            "Each plate will have same dilution"
            ),
        default = 2,
        minimum = 1,
        maximum = 4,
    )
    parameters.add_int(
        variable_name = "compo_num",
        display_name = "Number of components (1-8)",
        description = (
            "The number of components well in reservoir" 
            "Should not include the water sourced used to dilute."
        ),
        default = 3,
        minimum = 1,
        maximum =8,
    )
    parameters.add_str(
        variable_name="water_well",
        display_name="Number of Water Reservoirs",
        description=(
            "The number of reservoir wells with water"
            "in a 12-well plate for wells:"
            "9,10,11 & 12"
        ),
        default = "8,9,10", #pulls from the 9th well
        choices = [
            {"display_name": "1 well", "value": "8"},
            {"display_name": "2 wells", "value": "8,9"},
            {"display_name": "3 wells", "value": "8,9,10"},
            {"display_name": "4 wells", "value": "8,9,10,11"},
        ]
    )
    parameters.add_str(
        variable_name = "starting_concentration",
        display_name = "Initial concentrations",
        description = (
            "Initial concentration (mM) of every stock component"
            "Example: 40, 800, 5000 for "
            "three components"
        ),
        default = "5000,800,40",
        choices = [
            {"display_name": "NaCl,D-Glucose,MgSO4", "value": "5000,800,40"},
            {"display_name": "Custom", "value": "40,40,40"}
        ]
    )
    parameters.add_str(
        variable_name = "well_type",
        display_name = "Well-Plate Type",
        description = "The well-plate type for the serial dilution",
        default = "axygen_96_wellplate_500ul",
        choices =[
            {"display_name":"0.5 mL well-plate", "value":"axygen_96_wellplate_500ul"},
            {"display_name":"1 mL well-plate","value":"eppendorf_96_wellplate_1000ul"},
            {"display_name":"2 mL well-plate", "value":"thomsoninstrumentcompany_96_wellplate_2000ul"}
        ]
    )
    parameters.add_float(
        variable_name = "well_volume",
        display_name = "Final Volume per well (uL)",
        description = "Desired total volume in each well after dilution series",
        default = 500.00,
        minimum = 10.00,
        maximum = 2000.00,
        unit = "uL"
    )
    parameters.add_int(
        variable_name = "dilution_factor",
        display_name = "Dilution Factor",
        description = "The desired dilution factor for the serial dilution",
        default = 2,
        minimum = 2,
        maximum = 10
    )
    
    
def run(protocol: protocol_api.ProtocolContext):
    # User Single Variable Inputs
    plate_num = protocol.params.plate_num
    plate_type = protocol.params.well_type
    compo_num = protocol.params.compo_num
    num_columns = 12
    final_volume = protocol.params.well_volume
    plate_slots = [2, 3, 5, 6][:plate_num]
    dilution_factor = protocol.params.dilution_factor
    
   # Load Labware
    plates = [protocol.load_labware(plate_type, slot) for slot in plate_slots]
    tiprack300 = protocol.load_labware("opentrons_96_tiprack_300ul", 4)
    tiprack1000 = protocol.load_labware("opentrons_96_tiprack_1000ul", 7)
    reservoir = protocol.load_labware("usascientific_12_reservoir_22ml", 1)
    
    #Load pipettes
    right = protocol.load_instrument("p300_multi_gen2", "right", tip_racks=[tiprack300])
    left = protocol.load_instrument("p1000_single_gen2", "left", tip_racks=[tiprack1000])
    
    # Dynamic User Inputs
    water_well_indices = [int(x) - 1 for x in protocol.params.water_well.split(",")]
    starting_concentration = [float(x.strip()) for x in protocol.params.starting_concentration.split(",")]
    if len(starting_concentration) != compo_num:
        raise ValueError(
            f"Number of starting concentration ({len(starting_concentration)}) "
            f"must match number of components ({compo_num})."
        )
        
    # Establish Dynamic Volumes
    transfer_volume = final_volume / dilution_factor
    water_volume = final_volume - transfer_volume
    water = [reservoir.wells()[i] for i in water_well_indices]
    WELL_CAPACITY = 20000  # µL per reservoir well
    water_remaining = [WELL_CAPACITY] * len(water)
    current_water_idx = 0

    #This function is like a switch for the water source when it runs out in one well 
    def get_water(volume_needed):
        nonlocal current_water_idx
        while current_water_idx < len(water):
            if water_remaining[current_water_idx] >= volume_needed:
                water_remaining[current_water_idx] -= volume_needed
                return water[current_water_idx]
            else:
                protocol.comment(
                    f"Water well {water[current_water_idx].display_name} depleted. "
                    f"Switching to {water[current_water_idx].display_name}"
                )
            current_water_idx += 1
        raise RuntimeError("All water wells are depleted — refill reservoir and restart.")
    
    # Main Loop the executes the dilution factor
    for n, plate in enumerate(plates, start=1):
        protocol.comment(f"Starting serial dilution for Plate {n}")
        right.pick_up_tip()
        
             # Step 1: Add water to all wells except first column
        for col in plate.columns()[1:]:
            total_col_water = len(col) * water_volume  # total µL needed for the column
            water_source = get_water(total_col_water)
            right.distribute(
                volume=water_volume,
                source=water_source,
                dest=col,
                new_tip="never",
                disposal_volume=0
            )
        right.drop_tip()
        
            # Step 2: Add stock to first column
        for i in range(compo_num):
            row = plate.rows()[i]
            left.transfer(
                volume=final_volume,
                source=reservoir.wells()[i],
                dest=row[0],
                new_tip="always"
            )
            # Step 3: Perform serial dilution across the row
        right.pick_up_tip()
        for source_col, dest_col in zip(plate.columns()[:-1], plate.columns()[1:]):
            right.transfer(
                volume=transfer_volume,
                source=source_col,
                dest= dest_col,
                mix_after=(3, 50),
                new_tip="never"
            )
        right.drop_tip()

        # Output Concentrations in comments of the run
        protocol.comment(f"Concentration table for Plate {n}")
        for comp in range(compo_num):
            row_letter = chr(65 + comp)
            start_conc = starting_concentration[comp]
            concs = [
                f"{row_letter}{col+1}: {start_conc / (dilution_factor ** col):.2f} mM"
                for col in range(num_columns)
            ]
            protocol.comment(f"Component {comp+1} ({row_letter}): " + ", ".join(concs))