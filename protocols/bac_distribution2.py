from opentrons import protocol_api

metadata = {
    "protocolName": "E.coli Distribution 2 - Fixed Dispensing",
    "description": "A volume transfer program to distribute media to various labware including conical tubes. Supports volumes up to 15000 µL with automatic multiple transfers. Includes 1:100 bacterial dilution with well selection. Fixed flow rates to prevent tip popping.",
    "author": "Angie Aguirre-Tobar"
}

requirements = {"robotType": "OT-2", "apiLevel": "2.24"}

# Constants for mixing parameters
MIX_BEFORE_REPS = 3
MIX_AFTER_REPS = 3
MIX_AFTER_VOLUME = 50  # µL

# Flow rate constants (µL/s) - reduced from defaults to prevent splashing
P300_ASPIRATE_RATE = 46  # 50% of default 92.86
P300_DISPENSE_RATE = 46  # 50% of default 92.86
P300_BLOWOUT_RATE = 50   # Reduced from default 92.86

P1000_ASPIRATE_RATE = 137  # 50% of default 274.7
P1000_DISPENSE_RATE = 137  # 50% of default 274.7
P1000_BLOWOUT_RATE = 150   # Reduced from default 274.7

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
    
    # Initial bacteria culture volume
    parameters.add_int(
        variable_name="bacteria_initial_volume",
        display_name="Bacteria Culture Volume (uL)",
        description="Starting volume of bacteria culture in each tube",
        default=5000,
        minimum=1000,
        maximum=15000,
    )
    
    # Bacteria tube type for height calculation
    parameters.add_str(
        variable_name="bacteria_tube_type",
        display_name="Bacteria Tube Type",
        description="Type of tube containing bacteria culture (affects aspiration height)",
        choices=[
            {"display_name": "15 mL Conical", "value": "15ml_conical"},
            {"display_name": "50 mL Conical", "value": "50ml_conical"},
            {"display_name": "2 mL Tube", "value": "2ml_tube"}
        ],
        default="15ml_conical"
    )
    
    # Number of E.coli culture tubes to use
    parameters.add_int(
        variable_name="num_bacteria_tubes",
        display_name="Number of E.coli Culture Tubes",
        description="How many tubes of E.coli culture to use for distribution",
        default=1,
        minimum=1,
        maximum=15
    )
    
    # Well selection for bacterial inoculation
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
    
    # Custom well list (only used if pattern is "custom")
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

    # Custom well list (only used if pattern is "custom")
    parameters.add_str(
        variable_name="custom_media_wells",
        display_name="Custom Wells for Media",
        description="Comma-separated well names (A1, etc). Used only when not empty pattern.",
        default="",
        choices = [
            {"display_name":"All","value":""},
            {"display_name":"Corners","value":"A1,A12,H1,H12"},
            {"display_name":"First two columns","value":"A1,B1,C1,D1,E1,F1,G1,H1,A2,B2,C2,D2,E2,F2,G2,H2"},
            {"display_name": "All the border",
"value":"A1,B1,C1,D1,E1,F1,G1,H1,H2,H3,H4,H5,H6,H7,H8,H9,H10,H11,H12,G12,F12,E12,D12,C12,B12,A12,A11,A10,A9,A8,A7,A6,A5,A4,A3,A2"},
            {"display_name":"Center","value":"C5,C6,C7,C8,D5,D6,D7,D8,E5,E6,E7,E8,F5,F6,F7,F8"}
        ]
    )
    
    
    parameters.add_str(
        variable_name="sam1",
        display_name="Sample labware 1",
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
        variable_name="vol1",
        display_name="Volume for Labware 1 (µL)",
        description="Volume of media to distribute to labware 1 (max 15000 µL)",
        default=500,
        minimum=50,
        maximum=15000
    )
    
    parameters.add_str(
        variable_name="sam2",
        display_name="Sample labware 2",
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
        variable_name="vol2",
        display_name="Volume for Labware 2 (µL)",
        description="Volume of media to distribute to labware 2 (max 15000 µL)",
        default=200,
        minimum=50,
        maximum=15000
    )
    
    parameters.add_str(
        variable_name="sam3",
        display_name="Sample labware 3",
        description="Labware to distribute media to in deck slot 6",
        choices=[
            {"display_name": "12x22mL Reservoir", "value": "usascientific_12_reservoir_22ml"},
            {"display_name": "50mL & 15 mL Tube Rack", "value": "opentrons_10_tuberack_nest_4x50ml_6x15ml_conical"},
            {"display_name": "2mL 96-well plate", "value": "thermofischer_96_wellplate_2000ul"},
            {"display_name":"None", "value": "none"}
        ],
        default="none"
    )
    
    parameters.add_int(
        variable_name="vol3",
        display_name="Volume for Labware 3 (µL)",
        description="Volume of media to distribute to labware 3 (max 15000 µL)",
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
    custom_media_wells = protocol.params.custom_media_wells
    bacteria_initial_volume = protocol.params.bacteria_initial_volume
    bacteria_tube_type = protocol.params.bacteria_tube_type
 
    # Load media reservoir
    media = protocol.load_labware(protocol.params.media, "5")
 
    # Load in bacteria samples
    bacteria = protocol.load_labware(protocol.params.src_rack, "1")
    
    # Load sample labware only if not "none" and store with corresponding volumes
    sample_data = []
    sample_params = [
        (protocol.params.sam1, "2", protocol.params.vol1),
        (protocol.params.sam2, "3", protocol.params.vol2),
        (protocol.params.sam3, "6", protocol.params.vol3)
    ]
    
    for labware_type, slot, volume in sample_params:
        if labware_type != "none":
            labware = protocol.load_labware(labware_type, slot)
            sample_data.append((labware, volume))
 
    # Loading tip racks - more tip racks for high volume transfers
    tipracks_300 = [
        protocol.load_labware("opentrons_96_tiprack_300ul", slot)
        for slot in ["7", "10", "4"]
    ]
 
    tipracks_1000 = [
        protocol.load_labware("opentrons_96_filtertiprack_1000ul", slot)
        for slot in ["8", "9", "11"]
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
    
    # Set flow rates for both pipettes to prevent splashing and tip popping
    s_300_pip.flow_rate.aspirate = P300_ASPIRATE_RATE
    s_300_pip.flow_rate.dispense = P300_DISPENSE_RATE
    s_300_pip.flow_rate.blow_out = P300_BLOWOUT_RATE
    
    s_1000_pip.flow_rate.aspirate = P1000_ASPIRATE_RATE
    s_1000_pip.flow_rate.dispense = P1000_DISPENSE_RATE
    s_1000_pip.flow_rate.blow_out = P1000_BLOWOUT_RATE
    
    protocol.comment(f"Flow rates set - P300: {P300_DISPENSE_RATE} µL/s, P1000: {P1000_DISPENSE_RATE} µL/s")
 
    # Function to select appropriate pipette based on volume
    def select_pipette(volume):
        return s_300_pip if volume <= 300 else s_1000_pip
    
    # Function to calculate aspiration height based on tube type and remaining volume
    def calculate_aspiration_height(tube_type, remaining_volume):
        """
        Calculate safe aspiration height based on tube type and remaining volume.
        Returns height in mm from bottom of tube.
        """
        if tube_type == "15ml_conical":
            # 15mL conical: height varies from ~17mm (bottom) to ~117mm (15mL mark)
            if remaining_volume > 1000:
                height = min(100, 17 + (remaining_volume / 150))
            else:
                height = max(3, 17 + (remaining_volume / 150))
        
        elif tube_type == "50ml_conical":
            # 50mL conical: larger tube, different geometry
            if remaining_volume > 5000:
                height = min(90, 20 + (remaining_volume / 500))
            else:
                height = max(5, 20 + (remaining_volume / 500))
        
        elif tube_type == "2ml_tube":
            # 2mL tube: smaller, shorter tube
            if remaining_volume > 500:
                height = min(30, 5 + (remaining_volume / 50))
            else:
                height = max(2, 5 + (remaining_volume / 50))
        
        else:
            # Default safe height
            height = 5
        
        return height
    
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
            # Parse custom well list with error handling
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
    
    # Function to validate protocol requirements before starting
    def validate_protocol_requirements():
        """Validate all requirements before starting protocol"""
        protocol.comment("=== Starting Protocol Validation ===")
        
        # Calculate total tips needed
        total_tips_300_needed = 0
        total_tips_1000_needed = 0
        
        for labware, vol in sample_data:
            wells = get_inoculation_wells(labware, inoculation_pattern, custom_wells)
            
            # Calculate tips for media distribution
            if vol <= 300:
                # Using 300 µL pipette
                total_tips_300_needed += len(labware.wells())
            elif vol <= 1000:
                # Using 1000 µL pipette
                total_tips_1000_needed += len(labware.wells())
            else:
                # Large volume requiring multiple transfers with 1000 µL pipette
                num_transfers = (vol // 1000) + (1 if vol % 1000 > 0 else 0)
                total_tips_1000_needed += len(labware.wells()) * num_transfers
            
            # Calculate tips for bacteria distribution
            bacteria_volume = round(vol / 100, 1)
            if bacteria_volume <= 300:
                total_tips_300_needed += len(wells)
            else:
                total_tips_1000_needed += len(wells)
        
        # Check tip availability
        available_tips_300 = len(tipracks_300) * 96
        available_tips_1000 = len(tipracks_1000) * 96
        
        if total_tips_300_needed > available_tips_300:
            raise ValueError(
                f"Insufficient 300 µL tips: need {total_tips_300_needed}, have {available_tips_300}. "
                f"Add more tip racks or reduce protocol scope."
            )
        
        if total_tips_1000_needed > available_tips_1000:
            raise ValueError(
                f"Insufficient 1000 µL tips: need {total_tips_1000_needed}, have {available_tips_1000}. "
                f"Add more tip racks or reduce protocol scope."
            )
        
        protocol.comment(f"✓ Tip validation passed: 300µL tips: {total_tips_300_needed}/{available_tips_300}, "
                        f"1000µL tips: {total_tips_1000_needed}/{available_tips_1000}")
        
        # Check bacteria volume
        total_bacteria_needed = sum(
            len(get_inoculation_wells(labware, inoculation_pattern, custom_wells)) * round(vol / 100, 1)
            for labware, vol in sample_data
        )
        total_bacteria_available = bacteria_initial_volume * num_bacteria_tubes
        
        if total_bacteria_needed > total_bacteria_available:
            raise ValueError(
                f"Insufficient bacteria: need {total_bacteria_needed} µL, "
                f"have {total_bacteria_available} µL. "
                f"Increase bacteria volume or reduce number of inoculations."
            )
        
        protocol.comment(f"✓ Bacteria validation passed: need {total_bacteria_needed} µL, "
                        f"have {total_bacteria_available} µL")
        
        # Validate well volumes
        for labware, vol in sample_data:
            for well in labware.wells():
                if vol > well.max_volume:
                    raise ValueError(
                        f"Requested volume {vol} µL exceeds max volume "
                        f"of {well.max_volume} µL for well {well.display_name} in {labware.load_name}"
                    )
        
        protocol.comment("✓ Volume validation passed: all volumes within well capacity")
        protocol.comment("=== Validation Complete - Starting Protocol ===")
    
    # Function to distribute large volumes with multiple transfers - IMPROVED VERSION
    def distribute_large_volume(pipette, volume, source, destination_wells):
        """
        Distribute large volumes using multiple transfers if needed.
        Uses gentler dispense with delay instead of aggressive blow_out.
        """
        max_transfer = 1000 if pipette == s_1000_pip else 300
        
        if volume <= max_transfer:
            # Single transfer per well - dispense higher in well to reduce splashing
            for dest_well in destination_wells:
                pipette.pick_up_tip()
                pipette.aspirate(volume, source)
                # Dispense 5mm from bottom instead of 1mm (default)
                pipette.dispense(volume, dest_well.bottom(5))
                # Add delay to let liquid settle before removing tip
                protocol.delay(seconds=1)
                # Touch tip gently to remove any droplets
                pipette.touch_tip(dest_well, v_offset=-2, speed=20)
                pipette.drop_tip()
        else:
            # Multiple transfers needed per well
            num_full_transfers = volume // max_transfer
            remainder = volume % max_transfer
            
            for dest_well in destination_wells:
                # Perform full transfers
                for i in range(num_full_transfers):
                    pipette.pick_up_tip()
                    pipette.aspirate(max_transfer, source)
                    pipette.dispense(max_transfer, dest_well.bottom(5))
                    protocol.delay(seconds=1)
                    pipette.touch_tip(dest_well, v_offset=-2, speed=20)
                    pipette.drop_tip()
                
                # Transfer remainder if exists
                if remainder > 0:
                    pipette.pick_up_tip()
                    pipette.aspirate(remainder, source)
                    pipette.dispense(remainder, dest_well.bottom(5))
                    protocol.delay(seconds=1)
                    pipette.touch_tip(dest_well, v_offset=-2, speed=20)
                    pipette.drop_tip()
    
    # ===== PROTOCOL EXECUTION STARTS HERE =====
    
    # Validate all requirements before starting
    validate_protocol_requirements()
    
    # Distribute media to all loaded sample labware with their specific volumes
    protocol.comment("=== Starting Media Distribution ===")
    for labware, media_volume in sample_data:
        if custom_media_wells == "":
            destination_wells = labware.wells()
        else:
            destination_wells = labware.wells(*custom_media_wells.split(","))
    
        # Select appropriate pipette for this volume
        pipette = select_pipette(media_volume)
        
        protocol.comment(f"Distributing {media_volume} µL to {len(destination_wells)} wells in {labware.load_name}")
        
        # Use the improved large volume distribution function
        distribute_large_volume(pipette, media_volume, media['A1'], destination_wells)
        
        protocol.comment(f"✓ Completed distribution to {labware.load_name}")
    
    protocol.comment("=== Media Distribution Complete ===")
    
    # Distribute bacteria from liquid cultures with 1:100 dilution
    protocol.comment("=== Starting Bacterial Distribution ===")
    protocol.comment(f"Using {num_bacteria_tubes} bacteria tube(s), {bacteria_initial_volume} µL each")
    protocol.comment(f"Tube type: {bacteria_tube_type}, Pattern: {inoculation_pattern}")
 
    # Get specified number of bacteria source wells
    bacteria_wells = bacteria.wells()[:num_bacteria_tubes]
 
    # Track liquid volume for each bacteria tube
    bacteria_volumes = {well: bacteria_initial_volume for well in bacteria_wells}
 
    # For each sample labware, calculate the 1:100 dilution volume and distribute bacteria
    for labware, vol in sample_data:
        # Get wells that should receive bacteria based on selected pattern
        inoculation_wells = get_inoculation_wells(labware, inoculation_pattern, custom_wells)
        
        protocol.comment(f"Inoculating {len(inoculation_wells)} of {len(labware.wells())} wells in {labware.load_name}")
        
        # Calculate bacteria volume needed for 1:100 dilution
        bacteria_volume = round(vol / 100, 1)
        
        protocol.comment(f"Transferring {bacteria_volume} µL bacteria per well (1:100 dilution)")
        
        # Select appropriate pipette based on bacteria volume
        pipette = select_pipette(bacteria_volume)
        
        # Distribute bacteria only to selected wells
        for i, dest_well in enumerate(inoculation_wells):
            # Use modulo to cycle through the specified number of bacteria wells
            source_well = bacteria_wells[i % num_bacteria_tubes]
            
            # Get remaining volume and calculate aspiration height
            remaining_volume = bacteria_volumes[source_well]
            aspirate_height = calculate_aspiration_height(bacteria_tube_type, remaining_volume)
            
            # Transfer bacteria with mixing - IMPROVED VERSION
            pipette.pick_up_tip()
            # Mix before aspirating
            pipette.mix(MIX_BEFORE_REPS, min(bacteria_volume, pipette.max_volume), 
                       source_well.bottom(aspirate_height))
            # Aspirate bacteria
            pipette.aspirate(bacteria_volume, source_well.bottom(aspirate_height))
            # Dispense into destination well (higher up to reduce splashing)
            pipette.dispense(bacteria_volume, dest_well.bottom(3))
            # Mix after dispensing
            pipette.mix(MIX_AFTER_REPS, min(MIX_AFTER_VOLUME, vol + bacteria_volume), 
                       dest_well.bottom(3))
            # Add delay for liquid to settle
            protocol.delay(seconds=0.5)
            # Gentle touch tip
            pipette.touch_tip(dest_well, v_offset=-2, speed=20)
            pipette.drop_tip()
            
            # Update remaining volume in source tube
            bacteria_volumes[source_well] -= bacteria_volume
        
        protocol.comment(f"✓ Completed inoculation of {labware.load_name}")
 
    protocol.comment("=== Bacterial Distribution Complete ===")
    protocol.comment("=== Protocol Finished Successfully ===")