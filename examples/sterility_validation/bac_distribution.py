from opentrons import protocol_api

metadata = {
    "protocolName": "E.coli Distribution - High Volume",
    "description": "A volume transfer program to distribute media to various labware including conical tubes. Supports volumes up to 15000 µL with automatic multiple transfers. Includes 1:100 bacterial dilution with well selection.",
    "author": "Angie Aguirre-Tobar"
}

requirements = {"robotType": "OT-2", "apiLevel": "2.24"}

def add_parameters(parameters):

    # Choice of racks and plates used to store reagents & prepare samples
    parameters.add_str(
        variable_name="src_rack",
        display_name="E.coli Culture Rack",
        description="Labware to distribute media to in deck slot 1",
        choices=[
            {"display_name":"15 mL conical rack","value":"opentrons_15_tuberack_falcon_15ml_conical"},
            {"display_name": "50mL & 15 mL Tube Rack", "value": "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical"},
            {"display_name":"50 ml conical rack","value":"opentrons_6_tuberack_falcon_50ml_conical"},
        ],
        default="opentrons_10_tuberack_nest_4x50ml_6x15ml_conical"
    )
    
    # NEW PARAMETER: Number of E.coli culture tubes to use
    parameters.add_int(
        variable_name="num_bacteria_tubes",
        display_name="Number of E.coli Culture Tubes",
        description="How many tubes of E.coli culture to use for distribution",
        default=1,
        minimum=1,
        maximum=15
    )
    
    # NEW PARAMETER: Well selection for bacterial inoculation
    parameters.add_str(
        variable_name="inoculation_pattern",
        display_name="Bacterial Inoculation Pattern",
        description="Which wells receive bacteria on each plate",
        choices=[
            {"display_name": "All wells", "value": "all"},
            {"display_name": "First half of wells", "value": "first_half"},
            {"display_name": "Second half of wells", "value": "second_half"},
            {"display_name": "Every other well", "value": "alternating"},
            {"display_name": "First column only", "value": "first_column"},
            {"display_name": "Custom (see description)", "value": "custom"}
        ],
        default="all"
    )
    
    # NEW PARAMETER: Custom well list (only used if pattern is "custom")
    parameters.add_str(
        variable_name="custom_wells",
        display_name="Custom Wells for Inoculation",
        description="Comma-separated well names (e.g., A1,A2,B1,B2). Used only with Custom pattern.",
        default="A1,A12,H1,H12",
        choices = [
            {"display_name":"Corners","value":"A1,A12,H1,H12"},
            {"display_name": "All the border",
"value":"A1,B1,C1,D1,E1,F1,G1,H1,H2,H3,H4,H5,H6,H7,H8,H9,H10,H11,H12,G12,F12,E12,D12,C12,B12,A12,A11,A10,A9,A8,A7,A6,A5,A4,A3,A2"},
            {"display_name":"Center","value":"C5,C6,C7,C8,D5,D6,D7,D8,E5,E6,E7,E8,F5,F6,F7,F8"}
        ]
    )
    
    parameters.add_str(
        variable_name="sam2",
        display_name="Sample labware 2",
        description="Labware to distribute media to in deck slot 2",
        choices=[
            {"display_name": "12x22mL Reservoir", "value": "usascientific_12_reservoir_22ml"},
            {"display_name": "50mL & 15 mL Tube Rack", "value": "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical"},
            {"display_name": "2mL 96-well plate", "value": "thermofischer_96_wellplate_2000ul"},
            {"display_name":"None", "value": "none"}
        ],
        default="usascientific_12_reservoir_22ml"
    )
    
    parameters.add_int(
        variable_name="vol2",
        display_name="Volume for Labware 2 (µL)",
        description="Volume of media to distribute to labware 2 (max 15000 µL)",
        default=500,
        minimum=50,
        maximum=15000
    )
    
    parameters.add_str(
        variable_name="sam3",
        display_name="Sample labware 3",
        description="Labware to distribute media to in deck slot 3",
        choices=[
            {"display_name": "12x22mL Reservoir", "value": "usascientific_12_reservoir_22ml"},
            {"display_name": "50mL & 15 mL Tube Rack", "value": "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical"},
            {"display_name": "2mL 96-well plate", "value": "thermofischer_96_wellplate_2000ul"},
            {"display_name":"None", "value": "none"}
        ],
        default="thermofischer_96_wellplate_2000ul"
    )
    
    parameters.add_int(
        variable_name="vol3",
        display_name="Volume for Labware 3 (µL)",
        description="Volume of media to distribute to labware 3 (max 15000 µL)",
        default=200,
        minimum=50,
        maximum=15000
    )
    
    parameters.add_str(
        variable_name="sam4",
        display_name="Sample labware 4",
        description="Labware to distribute media to in deck slot 5",
        choices=[
            {"display_name": "12x22mL Reservoir", "value": "usascientific_12_reservoir_22ml"},
            {"display_name": "50mL & 15 mL Tube Rack", "value": "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical"},
            {"display_name": "2mL 96-well plate", "value": "thermofischer_96_wellplate_2000ul"},
            {"display_name":"None", "value": "none"}
        ],
        default="none"
    )
    
    parameters.add_int(
        variable_name="vol4",
        display_name="Volume for Labware 4 (µL)",
        description="Volume of media to distribute to labware 4 (max 15000 µL)",
        default=1000,
        minimum=50,
        maximum=15000
    )

    # Type of reservoir for fresh media
    parameters.add_str(
        variable_name="media",
        display_name="LB Media",
        description="Reservoir holding fresh LB media",
        choices=[
            {"display_name": "150 mL reservoir", "value": "integra_reservoir_150ml"},
            {"display_name": "300 mL reservoir", "value": "integra_reservoir_300ml"}
        ],
        default="integra_reservoir_300ml"
    )

def run(protocol: protocol_api.ProtocolContext):

    # Access runtime parameters
    num_bacteria_tubes = protocol.params.num_bacteria_tubes
    inoculation_pattern = protocol.params.inoculation_pattern
    custom_wells = protocol.params.custom_wells

    # Load media reservoir
    media = protocol.load_labware(protocol.params.media, "5")

    # Load in bacteria samples
    bacteria = protocol.load_labware(protocol.params.src_rack, "1")
    
    # Load sample labware only if not "none" and store with corresponding volumes
    sample_data = []
    sample_params = [
        (protocol.params.sam2, "2", protocol.params.vol2),
        (protocol.params.sam3, "3", protocol.params.vol3),
        (protocol.params.sam4, "6", protocol.params.vol4)
    ]
    
    for labware_type, slot, volume in sample_params:
        if labware_type != "none":
            labware = protocol.load_labware(labware_type, slot)
            sample_data.append((labware, volume))

    # Loading tip racks - more tip racks for high volume transfers
    tipracks_300 = [
        protocol.load_labware("opentrons_96_tiprack_300ul", slot)
        for slot in ["7", "10","4"]
    ]

    tipracks_1000 = [
        protocol.load_labware("opentrons_96_filtertiprack_1000ul", slot)
        for slot in ["8", "9","11"]
    ]

    # Loading pipettes
    s_300_pip = protocol.load_instrument(
        "p300_single_gen2",
        mount="right",
        tip_racks=tipracks_300
    )

    s_1000_pip = protocol.load_instrument(
        "p1000_single_gen2",
        mount="left",
        tip_racks=tipracks_1000
    )

    # Set faster flow rates for large volume transfers
    s_300_pip.flow_rate.aspirate = 150
    s_300_pip.flow_rate.dispense = 200
    s_300_pip.flow_rate.blow_out = 300
    
    s_1000_pip.flow_rate.aspirate = 150
    s_1000_pip.flow_rate.dispense = 200
    s_1000_pip.flow_rate.blow_out = 300

    # Function to select appropriate pipette based on volume
    def select_pipette(volume):
        return s_300_pip if volume <= 300 else s_1000_pip
    
    # Function to determine which wells should receive bacteria based on pattern
    def get_inoculation_wells(labware, pattern, custom_well_list):
        """
        Returns a list of wells that should receive bacterial inoculation
        based on the selected pattern.
        """
        all_wells = labware.wells()
        
        if pattern == "all":
            return all_wells
        
        elif pattern == "first_half":
            half_point = len(all_wells) // 2
            return all_wells[:half_point]
        
        elif pattern == "second_half":
            half_point = len(all_wells) // 2
            return all_wells[half_point:]
        
        elif pattern == "alternating":
            return [well for i, well in enumerate(all_wells) if i % 2 == 0]
        
        elif pattern == "first_column":
            # Get first column (works for plates and reservoirs)
            if hasattr(labware, 'columns'):
                return labware.columns()[0]
            else:
                # For tube racks, return first row
                return labware.rows()[0]
        
        elif pattern == "custom":
            # Parse custom well list
            well_names = [name.strip() for name in custom_well_list.split(',')]
            selected_wells = []
            for well_name in well_names:
                try:
                    selected_wells.append(labware.wells_by_name()[well_name])
                except KeyError:
                    protocol.comment(f"Warning: Well {well_name} not found in labware, skipping")
            return selected_wells
        
        else:
            # Default to all wells if pattern not recognized
            return all_wells
        
    # Function to distribute large volumes with multiple transfers
    def distribute_large_volume(pipette, volume, source, destination_wells):
        """
        Distributes large volumes by splitting into multiple transfers if needed.
        For volumes > 1000 µL, makes multiple 1000 µL transfers.
        """
        max_transfer = 1000 if pipette == s_1000_pip else 300
        
        # Calculate number of full transfers and remainder
        num_full_transfers = volume // max_transfer
        remainder = volume % max_transfer
        
        # Perform full transfers
        if num_full_transfers > 0:
            for well in destination_wells:
                pipette.pick_up_tip()
                for _ in range(num_full_transfers):
                    pipette.aspirate(max_transfer, source)
                    pipette.dispense(max_transfer, well)
                # Add remainder if exists
                if remainder > 0:
                    pipette.aspirate(remainder, source)
                    pipette.dispense(remainder, well)
                pipette.drop_tip()
        else:
            # Volume is less than max_transfer, do single transfer
            pipette.transfer(
                volume,
                source,
                destination_wells,
                new_tip='always'
            )
    
    # Distribute media to all loaded sample labware with their specific volumes
    for sample_labware, media_volume in sample_data:
        # Get all wells from the labware
        destination_wells = sample_labware.wells()
        
        for well in destination_wells:
             if media_volume > well.max_volume:
                 raise ValueError(
                     f"Requested volume {media_volume} µL exceeds max volume "
                     f"of {well.max_volume} µL for well {well.display_name}"
                 )

        # Select appropriate pipette for this volume
        pipette = select_pipette(media_volume)
        
        protocol.comment(f"Starting distribution of {media_volume} µL to {len(destination_wells)} wells")
        
        # Use the large volume distribution function
        distribute_large_volume(pipette, media_volume, media.wells()[0], destination_wells)
        
        protocol.comment(f"Completed distribution of {media_volume} µL to {len(destination_wells)} wells")
    
    # Distribute bacteria from liquid cultures with 1:100 dilution
    protocol.comment(f"Starting bacterial distribution with 1:100 dilution using {num_bacteria_tubes} bacteria tube(s)")
    protocol.comment(f"Inoculation pattern: {inoculation_pattern}")
    
    # Get specified number of bacteria source wells
    bacteria_wells = bacteria.wells()[:num_bacteria_tubes]
    
    # For each sample labware, calculate the 1:100 dilution volume and distribute bacteria
    for sample_labware, media_volume in sample_data:
        # Get wells that should receive bacteria based on selected pattern
        inoculation_wells = get_inoculation_wells(sample_labware, inoculation_pattern, custom_wells)
        
        protocol.comment(f"Inoculating {len(inoculation_wells)} wells out of {len(sample_labware.wells())} total wells")
        
        # Calculate bacteria volume needed for 1:100 dilution
        # For 1:100 dilution: bacteria_volume = total_volume / 100
        bacteria_volume = round(media_volume / 99, 1)
        
        protocol.comment(f"Distributing {bacteria_volume} µL bacteria for 1:100 dilution (total volume: {media_volume} µL)")
        
        # Select appropriate pipette based on bacteria volume
        pipette = select_pipette(bacteria_volume)
        
        # Distribute bacteria only to selected wells
        for i, dest_well in enumerate(inoculation_wells):
            # Use modulo to cycle through the specified number of bacteria wells
            source_well = bacteria_wells[i % num_bacteria_tubes]
            
            # Transfer bacteria with mixing
            pipette.transfer(
                bacteria_volume,
                source_well,
                dest_well,
                mix_before=(3, bacteria_volume if bacteria_volume <= pipette.max_volume else pipette.max_volume),
                mix_after=(3, min(50, media_volume + bacteria_volume)),
                new_tip='always'
            )
    
    protocol.comment("Bacterial distribution complete")
    