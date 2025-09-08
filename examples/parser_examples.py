"""
Examples demonstrating robot format parser capabilities.
Shows comprehensive usage of URDF and MJCF parsing features.
"""

import tempfile
from pathlib import Path

# Import parsers
from robot_format_converter.parsers import URDFParser, MJCFParser, SchemaParser


def parse_unified_schema(schema_file_path, validate=True, verbose=True):
    """
    Parse a unified schema file (YAML/JSON) and return the CommonSchema object.
    
    This function provides a simple interface to parse robot schema files
    with optional validation and verbose output.
    
    Args:
        schema_file_path (str or Path): Path to the schema file (YAML or JSON)
        validate (bool): Whether to perform schema validation after parsing
        verbose (bool): Whether to print parsing progress and results
        
    Returns:
        CommonSchema: Parsed robot schema object
        
    Raises:
        FileNotFoundError: If the schema file doesn't exist
        ValueError: If the file format is not supported or validation fails
        Exception: For other parsing errors
        
    Examples:
        # Basic usage
        schema = parse_unified_schema('my_robot.yaml')
        
        # Parse with validation disabled
        schema = parse_unified_schema('my_robot.yaml', validate=False)
        
        # Parse silently
        schema = parse_unified_schema('my_robot.yaml', verbose=False)
        
        # Access parsed data
        print(f"Robot: {schema.metadata.name}")
        print(f"Links: {len(schema.links)}")
        print(f"Joints: {len(schema.joints)}")
    """
    schema_path = Path(schema_file_path)
    
    # Check if file exists
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    if verbose:
        print(f"📁 Loading schema file: {schema_path}")
    
    # Initialize parser
    parser = SchemaParser()
    
    # Check if parser can handle the file
    if not parser.can_parse(schema_path):
        raise ValueError(f"Unsupported file format: {schema_path.suffix}")
    
    if verbose:
        print("🔧 Parsing schema file...")
    
    try:
        # Parse the schema
        schema = parser.parse(schema_path)
        
        if verbose:
            print("✅ Schema parsed successfully!")
            print(f"  Robot: {schema.metadata.name} v{schema.metadata.version}")
            print(f"  Links: {len(schema.links)}")
            print(f"  Joints: {len(schema.joints)}")
            if schema.actuators:
                print(f"  Actuators: {len(schema.actuators)}")
            if schema.sensors:
                print(f"  Sensors: {len(schema.sensors)}")
            if schema.contacts:
                print(f"  Contacts: {len(schema.contacts)}")
        
        # Perform validation if requested
        if validate:
            if verbose:
                print("🔍 Validating schema...")
            
            issues = schema.validate()
            if issues:
                if verbose:
                    print(f"⚠️ Validation found {len(issues)} issues:")
                    for issue in issues:
                        print(f"    - {issue}")
                # Note: We don't raise an exception for validation issues
                # as they might be warnings that don't prevent usage
            else:
                if verbose:
                    print("✅ Schema validation passed!")
        
        return schema
        
    except Exception as e:
        if verbose:
            print(f"❌ Failed to parse schema: {e}")
        raise


def create_schema_from_dict(schema_dict, validate=True):
    """
    Create a CommonSchema object from a dictionary representation.
    
    This is useful when you have schema data from JSON or YAML that you've
    loaded manually, or when creating schemas programmatically.
    
    Args:
        schema_dict (dict): Dictionary containing schema data
        validate (bool): Whether to validate the resulting schema
        
    Returns:
        CommonSchema: The created schema object
        
    Example:
        schema_data = {
            'metadata': {
                'name': 'my_robot',
                'version': '1.0'
            },
            'links': [...],
            'joints': [...]
        }
        schema = create_schema_from_dict(schema_data)
    """
    parser = SchemaParser()
    schema = parser._dict_to_schema(schema_dict)
    
    if validate:
        issues = schema.validate()
        if issues:
            print(f"⚠️ Schema validation found {len(issues)} issues:")
            for issue in issues:
                print(f"    - {issue}")
    
    return schema


def example_basic_urdf_parsing():
    """Example: Basic URDF parsing with a simple robot."""
    print("=== Basic URDF Parsing Example ===")
    
    # Create a simple URDF file
    urdf_content = '''<?xml version="1.0"?>
    <robot name="simple_arm">
        <material name="blue">
            <color rgba="0 0 1 1"/>
        </material>
        
        <link name="base_link">
            <inertial>
                <mass value="10.0"/>
                <origin xyz="0 0 0.05"/>
                <inertia ixx="1.0" iyy="1.0" izz="1.0" 
                         ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <geometry>
                    <box size="0.4 0.4 0.1"/>
                </geometry>
                <material name="blue"/>
            </visual>
            <collision>
                <geometry>
                    <box size="0.4 0.4 0.1"/>
                </geometry>
            </collision>
        </link>
        
        <link name="arm_link">
            <inertial>
                <mass value="5.0"/>
                <origin xyz="0 0 0.25"/>
                <inertia ixx="0.5" iyy="0.5" izz="0.1" 
                         ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <geometry>
                    <cylinder radius="0.05" length="0.5"/>
                </geometry>
            </visual>
        </link>
        
        <link name="end_effector">
            <inertial>
                <mass value="1.0"/>
                <inertia ixx="0.1" iyy="0.1" izz="0.1" 
                         ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <geometry>
                    <sphere radius="0.08"/>
                </geometry>
            </visual>
        </link>
        
        <joint name="base_to_arm" type="revolute">
            <parent link="base_link"/>
            <child link="arm_link"/>
            <origin xyz="0 0 0.05" rpy="0 0 0"/>
            <axis xyz="0 0 1"/>
            <limit lower="-3.14" upper="3.14" 
                   effort="50.0" velocity="2.0"/>
            <dynamics damping="0.5" friction="0.1"/>
        </joint>
        
        <joint name="arm_to_end" type="prismatic">
            <parent link="arm_link"/>
            <child link="end_effector"/>
            <origin xyz="0 0 0.5"/>
            <axis xyz="0 0 1"/>
            <limit lower="0" upper="0.3" 
                   effort="20.0" velocity="1.0"/>
        </joint>
    </robot>'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', 
                                     delete=False) as f:
        f.write(urdf_content)
        urdf_path = Path(f.name)
    
    try:
        # Parse the URDF
        parser = URDFParser()
        
        # Check if can parse
        print(f"Can parse {urdf_path.name}: {parser.can_parse(urdf_path)}")
        
        # Parse the file
        schema = parser.parse(urdf_path)
        
        # Display results
        print(f"Robot name: {schema.metadata.name}")
        print(f"Source format: {schema.metadata.source_format}")
        print(f"Number of links: {len(schema.links)}")
        print(f"Number of joints: {len(schema.joints)}")
        
        # Show link details
        print("\nLinks:")
        for link in schema.links:
            print(f"  - {link.name}")
            if link.mass > 0:
                print(f"    Mass: {link.mass}")
            print(f"    Visual elements: {len(link.visuals)}")
            print(f"    Collision elements: {len(link.collisions)}")
        
        # Show joint details
        print("\nJoints:")
        for joint in schema.joints:
            print(f"  - {joint.name} ({joint.type})")
            print(f"    Parent: {joint.parent_link}")
            print(f"    Child: {joint.child_link}")
            if joint.limits:
                print(f"    Limits: {joint.limits.lower} to "
                      f"{joint.limits.upper}")
        
        # Show parsing context (enhanced feature)
        if 'parse_context' in schema.extensions:
            context = schema.extensions['parse_context']
            warnings = context.get('warnings', [])
            errors = context.get('errors', [])
            
            if warnings:
                print(f"\nWarnings ({len(warnings)}):")
                for warning in warnings[:3]:  # Show first 3
                    print(f"  - {warning}")
                if len(warnings) > 3:
                    print(f"  ... and {len(warnings) - 3} more")
            
            if errors:
                print(f"\nErrors ({len(errors)}):")
                for error in errors[:3]:  # Show first 3
                    print(f"  - {error}")
                if len(errors) > 3:
                    print(f"  ... and {len(errors) - 3} more")
        
        print("✓ URDF parsing completed successfully\n")
        
    finally:
        # Clean up
        if urdf_path.exists():
            urdf_path.unlink()


def example_basic_mjcf_parsing():
    """Example: Basic MJCF parsing with a simple robot."""
    print("=== Basic MJCF Parsing Example ===")
    
    # Create a simple MJCF file
    mjcf_content = '''<?xml version="1.0"?>
    <mujoco model="simple_manipulator">
        <compiler angle="radian" meshdir="../meshes/"/>
        
        <option timestep="0.002"/>
        
        <asset>
            <material name="red" rgba="1 0 0 1"/>
            <material name="green" rgba="0 1 0 1"/>
            <material name="blue" rgba="0 0 1 1"/>
        </asset>
        
        <worldbody>
            <light diffuse=".5 .5 .5" pos="0 0 3" 
                   dir="0 0 -1"/>
            <geom name="floor" pos="0 0 -0.5" size="2 2 0.1" 
                  type="box" material="green"/>
            
            <body name="base" pos="0 0 0">
                <inertial mass="5.0" pos="0 0 0.05" 
                          diaginertia="0.1 0.1 0.05"/>
                <geom name="base_geom" type="cylinder" 
                      size="0.15 0.1" material="blue"/>
                
                <body name="link1" pos="0 0 0.1">
                    <inertial mass="2.0" pos="0 0 0.15" 
                              diaginertia="0.05 0.05 0.02"/>
                    <joint name="joint1" type="hinge" axis="0 0 1" 
                           range="-3.14 3.14" damping="0.1"/>
                    <geom name="link1_geom" type="box" 
                          size="0.05 0.05 0.15" material="red"/>
                    
                    <body name="link2" pos="0 0 0.3">
                        <inertial mass="1.5" pos="0 0 0.1" 
                                  diaginertia="0.02 0.02 0.01"/>
                        <joint name="joint2" type="hinge" axis="1 0 0" 
                               range="-1.57 1.57" damping="0.05"/>
                        <geom name="link2_geom" type="cylinder" 
                              size="0.03 0.1" material="red"/>
                        
                        <body name="end_effector" pos="0 0 0.2">
                            <inertial mass="0.5" pos="0 0 0" 
                                      diaginertia="0.01 0.01 0.01"/>
                            <joint name="gripper" type="slide" axis="0 1 0" 
                                   range="-0.05 0.05"/>
                            <geom name="gripper_geom" type="sphere" 
                                  size="0.05" material="blue"/>
                        </body>
                    </body>
                </body>
            </body>
        </worldbody>
        
        <actuator>
            <motor name="motor1" joint="joint1" gear="100"/>
            <motor name="motor2" joint="joint2" gear="50"/>
            <motor name="gripper_motor" joint="gripper" gear="10"/>
        </actuator>
        
        <sensor>
            <accelerometer name="base_accel" site="base"/>
            <gyro name="base_gyro" site="base"/>
        </sensor>
    </mujoco>'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', 
                                     delete=False) as f:
        f.write(mjcf_content)
        mjcf_path = Path(f.name)
    
    try:
        # Parse the MJCF
        parser = MJCFParser()
        
        # Check if can parse
        print(f"Can parse {mjcf_path.name}: {parser.can_parse(mjcf_path)}")
        
        # Parse the file
        schema = parser.parse(mjcf_path)
        
        # Display results
        print(f"Model name: {schema.metadata.name}")
        print(f"Source format: {schema.metadata.source_format}")
        print(f"Number of links: {len(schema.links)}")
        print(f"Number of joints: {len(schema.joints)}")
        print(f"Number of actuators: {len(schema.actuators)}")
        print(f"Number of sensors: {len(schema.sensors)}")
        
        # Show link details
        print("\nLinks:")
        for link in schema.links:
            print(f"  - {link.name}")
            if link.mass > 0:
                print(f"    Mass: {link.mass}")
            print(f"    Visual elements: {len(link.visuals)}")
        
        # Show joint details
        print("\nJoints:")
        for joint in schema.joints:
            print(f"  - {joint.name} ({joint.type})")
            if hasattr(joint, 'parent_link'):
                print(f"    Parent: {joint.parent_link}")
            if hasattr(joint, 'child_link'):
                print(f"    Child: {joint.child_link}")
        
        # Show actuators
        print("\nActuators:")
        for actuator in schema.actuators:
            print(f"  - {actuator.name}")
        
        # Show sensors
        print("\nSensors:")
        for sensor in schema.sensors:
            print(f"  - {sensor.name}")
        
        print("✓ MJCF parsing completed successfully\n")
        
    finally:
        # Clean up
        if mjcf_path.exists():
            mjcf_path.unlink()


def example_validation_features():
    """Example: Validation features and error detection."""
    print("=== Validation Features Example ===")
    
    # Create URDF with validation issues
    problematic_urdf = '''<?xml version="1.0"?>
    <robot name="problematic_robot">
        <!-- Link with negative mass (warning) -->
        <link name="bad_mass_link">
            <inertial>
                <mass value="-1.0"/>
                <inertia ixx="1.0" iyy="1.0" izz="1.0" 
                         ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <geometry>
                    <box size="1 1 1"/>
                </geometry>
            </visual>
        </link>
        
        <!-- Link with invalid inertia tensor -->
        <link name="bad_inertia_link">
            <inertial>
                <mass value="1.0"/>
                <inertia ixx="-1.0" iyy="1.0" izz="1.0" 
                         ixy="0" ixz="0" iyz="0"/>
            </inertial>
        </link>
        
        <!-- Good link for comparison -->
        <link name="good_link">
            <inertial>
                <mass value="2.0"/>
                <inertia ixx="1.0" iyy="1.0" izz="1.0" 
                         ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <geometry>
                    <cylinder radius="0.1" length="0.5"/>
                </geometry>
            </visual>
        </link>
        
        <!-- Joint with invalid limit range -->
        <joint name="bad_limits_joint" type="revolute">
            <parent link="good_link"/>
            <child link="bad_mass_link"/>
            <limit lower="1.0" upper="-1.0"/>
        </joint>
        
        <!-- Joint referencing non-existent link -->
        <joint name="bad_ref_joint" type="revolute">
            <parent link="good_link"/>
            <child link="nonexistent_link"/>
        </joint>
        
        <!-- Valid joint -->
        <joint name="good_joint" type="prismatic">
            <parent link="good_link"/>
            <child link="bad_inertia_link"/>
            <axis xyz="0 0 1"/>
            <limit lower="0" upper="0.5"/>
        </joint>
    </robot>'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', 
                                     delete=False) as f:
        f.write(problematic_urdf)
        urdf_path = Path(f.name)
    
    try:
        # Parse with validation
        parser = URDFParser()
        schema = parser.parse(urdf_path)
        
        print(f"Parsed robot: {schema.metadata.name}")
        print(f"Links found: {len(schema.links)}")
        print(f"Joints found: {len(schema.joints)}")
        
        # Show validation results
        if 'parse_context' in schema.extensions:
            context = schema.extensions['parse_context']
            warnings = context.get('warnings', [])
            errors = context.get('errors', [])
            
            print(f"\n🟡 Validation Warnings ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
            
            print(f"\n🔴 Validation Errors ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            
            if not warnings and not errors:
                print("\n✅ No validation issues found!")
        
        print("\n✓ Validation example completed\n")
        
    finally:
        # Clean up
        if urdf_path.exists():
            urdf_path.unlink()


def example_error_recovery():
    """Example: Parser error recovery capabilities."""
    print("=== Error Recovery Example ===")
    
    # Create URDF with syntax errors
    broken_urdf = '''<?xml version="1.0"?>
    <robot name="broken_robot">
        <!-- This link is missing a name attribute -->
        <link>
            <inertial>
                <mass value="1.0"/>
            </inertial>
        </link>
        
        <!-- This is a valid link -->
        <link name="working_link">
            <inertial>
                <mass value="2.0"/>
                <inertia ixx="1.0" iyy="1.0" izz="1.0" 
                         ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <geometry>
                    <box size="0.5 0.5 0.5"/>
                </geometry>
            </visual>
        </link>
        
        <!-- Joint with missing attributes -->
        <joint type="revolute">
            <parent link="working_link"/>
            <child link="working_link"/>
        </joint>
        
        <!-- Valid joint -->
        <joint name="good_joint" type="fixed">
            <parent link="working_link"/>
            <child link="working_link"/>
        </joint>
        
        <!-- Incomplete element -->
        <link name="incomplete_link"
    </robot>'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', 
                                     delete=False) as f:
        f.write(broken_urdf)
        urdf_path = Path(f.name)
    
    try:
        # Try to parse the broken URDF
        parser = URDFParser()
        
        print("Attempting to parse broken URDF file...")
        
        # Check if parser can handle it
        can_parse = parser.can_parse(urdf_path)
        print(f"Can parse broken file: {can_parse}")
        
        if can_parse:
            schema = parser.parse(urdf_path)
            
            print(f"✓ Parser recovered successfully!")
            print(f"Robot name: {schema.metadata.name}")
            print(f"Links recovered: {len(schema.links)}")
            print(f"Joints recovered: {len(schema.joints)}")
            
            # Show what was recovered
            print("\nRecovered elements:")
            for link in schema.links:
                print(f"  Link: {link.name}")
            for joint in schema.joints:
                print(f"  Joint: {joint.name} ({joint.type})")
        else:
            print("Parser could not handle the broken file.")
        
        print("\n✓ Error recovery example completed\n")
        
    finally:
        # Clean up
        if urdf_path.exists():
            urdf_path.unlink()


def example_schema_parsing():
    """Example: Parse unified schema files (YAML/JSON) with comprehensive features."""
    print("=== Schema Parsing Example ===")
    
    # Create a comprehensive schema example
    schema_content = '''
metadata:
  name: example_robot
  version: "2.0.0"
  author: Robot Format Converter
  description: "Example robot for schema parsing demonstration"
  source_format: schema
  created_date: "2025-09-08"

# Define robot links with comprehensive properties
links:
  - name: base_link
    mass: 10.0
    center_of_mass: [0.0, 0.0, 0.05]
    inertia:
      ixx: 2.5
      iyy: 2.5
      izz: 1.2
      ixy: 0.0
      ixz: 0.0
      iyz: 0.0

  - name: shoulder_link
    mass: 5.0
    center_of_mass: [0.0, 0.0, 0.12]
    inertia:
      ixx: 0.8
      iyy: 0.8
      izz: 0.4
      ixy: 0.0
      ixz: 0.0
      iyz: 0.0

  - name: arm_link
    mass: 3.0
    center_of_mass: [0.0, 0.0, 0.25]
    inertia:
      ixx: 0.5
      iyy: 0.5
      izz: 0.1
      ixy: 0.0
      ixz: 0.0
      iyz: 0.0

# Define robot joints with limits and dynamics
joints:
  - name: shoulder_joint
    type: revolute
    parent_link: base_link
    child_link: shoulder_link
    pose:
      position: [0.0, 0.0, 0.1]
      orientation: [0.0, 0.0, 0.0, 1.0]
    axis: [0.0, 0.0, 1.0]
    limits:
      lower: -3.14159
      upper: 3.14159
      effort: 100.0
      velocity: 2.0

  - name: elbow_joint
    type: revolute
    parent_link: shoulder_link
    child_link: arm_link
    pose:
      position: [0.0, 0.0, 0.2]
      orientation: [0.0, 0.0, 0.0, 1.0]
    axis: [1.0, 0.0, 0.0]
    limits:
      lower: -1.57
      upper: 1.57
      effort: 50.0
      velocity: 1.5

# Define actuators
actuators:
  - name: shoulder_motor
    type: position
    joint: shoulder_joint
    gear_ratio: 100.0
    control_range: [-1.0, 1.0]

  - name: elbow_motor
    type: position
    joint: elbow_joint
    gear_ratio: 80.0
    control_range: [-1.0, 1.0]

# Define sensors
sensors:
  - name: shoulder_encoder
    type: position
    parent_link: shoulder_link
    joint: shoulder_joint
    noise_std: 0.001

  - name: arm_force_sensor
    type: force_torque
    parent_link: arm_link
    pose:
      position: [0.0, 0.0, 0.25]
      orientation: [0.0, 0.0, 0.0, 1.0]

# Define contacts
contacts:
  - name: base_ground_contact
    link1: base_link
    link2: ground
    surface_properties:
      friction: [1.0, 1.0, 0.01]
      restitution: 0.1
'''
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_content)
        temp_file = f.name
    
    try:
        print(f"📁 Created temporary schema file: {temp_file}")
        
        # Initialize schema parser
        parser = SchemaParser()
        print("🔧 Initialized SchemaParser")
        
        # Test file detection
        can_parse = parser.can_parse(temp_file)
        print(f"✅ Can parse file: {can_parse}")
        
        if can_parse:
            # Parse the schema file
            print("🔄 Parsing schema file...")
            schema = parser.parse(temp_file)
            
            # Display parsed results
            print("📊 Parsed Schema Results:")
            print(f"  Robot Name: {schema.metadata.name}")
            print(f"  Version: {schema.metadata.version}")
            print(f"  Description: {schema.metadata.description}")
            print(f"  Links: {len(schema.links)}")
            print(f"  Joints: {len(schema.joints)}")
            print(f"  Actuators: {len(schema.actuators)}")
            print(f"  Sensors: {len(schema.sensors)}")
            print(f"  Contacts: {len(schema.contacts)}")
            
            # Display link details
            print("\n📋 Link Details:")
            for link in schema.links:
                print(f"  - {link.name}: mass={link.mass}kg, "
                      f"CoM=({link.center_of_mass.x:.3f}, {link.center_of_mass.y:.3f}, {link.center_of_mass.z:.3f})")
            
            # Display joint details
            print("\n🔗 Joint Details:")
            for joint in schema.joints:
                limits_str = ""
                if joint.limits:
                    limits_str = f" limits=({joint.limits.lower:.2f}, {joint.limits.upper:.2f})"
                print(f"  - {joint.name}: {joint.type.value} ({joint.parent_link} → {joint.child_link}){limits_str}")
            
            # Display actuator details
            print("\n⚙️ Actuator Details:")
            for actuator in schema.actuators:
                print(f"  - {actuator.name}: {actuator.type} controlling {actuator.joint}")
            
            # Display sensor details
            print("\n📡 Sensor Details:")
            for sensor in schema.sensors:
                print(f"  - {sensor.name}: {sensor.type} on {sensor.parent_link}")
            
            # Validate schema
            print("\n🔍 Schema Validation:")
            issues = schema.validate()
            if issues:
                print("  ⚠️ Validation Issues Found:")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print("  ✅ Schema validation passed!")
            
            # Demonstrate extension capabilities
            print("\n🔧 Extension Capabilities:")
            if schema.extensions:
                print("  Schema extensions:")
                for key, value in schema.extensions.items():
                    print(f"    {key}: {type(value).__name__}")
            else:
                print("  No extensions found")
            
            # Show root links
            print("\n🌳 Kinematic Structure:")
            try:
                root_links = schema.get_root_links()
                print(f"  Root links: {[link.name for link in root_links]}")
                
                # Show kinematic chains
                for root in root_links:
                    chain = schema.get_kinematic_chain(root.name)
                    print(f"  Chain from {root.name}: {[link.name for link in chain]}")
            except Exception as e:
                print(f"  Error analyzing kinematic structure: {e}")
                
            print("✅ Schema parsing example completed successfully!")
            
        else:
            print("❌ Parser cannot handle this file format")
            
    except Exception as e:
        print(f"❌ Schema parsing failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up temporary file
        try:
            Path(temp_file).unlink()
            print(f"🗑️ Cleaned up temporary file")
        except Exception:
            pass


def example_comprehensive_schema_parsing():
    """Example: Parse the comprehensive schema configuration file."""
    print("=== Comprehensive Schema Parsing Example ===")
    
    # Look for the comprehensive schema file
    schema_file = Path("config/comprehensive_robot_schema.yaml")
    if not schema_file.exists():
        print(f"❌ Comprehensive schema file not found: {schema_file}")
        print("   Please ensure the comprehensive_robot_schema.yaml file exists in the config/ directory")
        return
    
    try:
        print(f"📁 Found comprehensive schema file: {schema_file}")
        
        # Initialize parser
        parser = SchemaParser()
        print("🔧 Initialized SchemaParser")
        
        # Parse the comprehensive schema
        print("🔄 Parsing comprehensive schema file...")
        schema = parser.parse(schema_file)
        
        print("🎉 Successfully parsed comprehensive schema!")
        print(f"📊 Schema Statistics:")
        print(f"  Robot: {schema.metadata.name} v{schema.metadata.version}")
        print(f"  Links: {len(schema.links)}")
        print(f"  Joints: {len(schema.joints)}")
        print(f"  Actuators: {len(schema.actuators)}")
        print(f"  Sensors: {len(schema.sensors)}")
        print(f"  Contacts: {len(schema.contacts)}")
        
        # Show advanced features parsed
        if schema.links:
            print(f"\n🔧 Advanced Link Features Detected:")
            for link in schema.links[:3]:  # Show first 3 links
                print(f"  - {link.name}: mass={link.mass}kg")
                if hasattr(link, 'visuals') and link.visuals:
                    print(f"    Visual representations: {len(link.visuals)}")
                if hasattr(link, 'collisions') and link.collisions:
                    print(f"    Collision representations: {len(link.collisions)}")
        
        if schema.joints:
            print(f"\n⚙️ Advanced Joint Features:")
            joint_types = set(joint.type.value for joint in schema.joints)
            print(f"  Joint types: {', '.join(joint_types)}")
            joints_with_limits = sum(1 for joint in schema.joints if joint.limits)
            print(f"  Joints with limits: {joints_with_limits}/{len(schema.joints)}")
        
        # Validate comprehensive schema
        print("\n🔍 Comprehensive Schema Validation:")
        issues = schema.validate()
        if issues:
            print(f"  ⚠️ Found {len(issues)} validation issues:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more issues")
        else:
            print("  ✅ Comprehensive schema validation passed!")
            
        print("✅ Comprehensive schema parsing completed!")
        
    except Exception as e:
        print(f"❌ Comprehensive schema parsing failed: {e}")
        import traceback
        traceback.print_exc()


def example_utility_functions():
    """Example: Demonstrate the utility functions for schema parsing."""
    print("=== Schema Parsing Utility Functions Example ===")
    
    # Create a simple schema dictionary
    robot_data = {
        'metadata': {
            'name': 'utility_demo_robot',
            'version': '1.0.0',
            'author': 'Schema Parser Demo',
            'description': 'Robot created via utility function'
        },
        'links': [
            {
                'name': 'base_link',
                'mass': 5.0,
                'center_of_mass': [0.0, 0.0, 0.0],
                'inertia': {
                    'ixx': 1.0, 'iyy': 1.0, 'izz': 1.0,
                    'ixy': 0.0, 'ixz': 0.0, 'iyz': 0.0
                }
            },
            {
                'name': 'arm_link',
                'mass': 2.0,
                'center_of_mass': [0.0, 0.0, 0.2],
                'inertia': {
                    'ixx': 0.1, 'iyy': 0.1, 'izz': 0.1,
                    'ixy': 0.0, 'ixz': 0.0, 'iyz': 0.0
                }
            }
        ],
        'joints': [
            {
                'name': 'base_joint',
                'type': 'revolute',
                'parent_link': 'base_link',
                'child_link': 'arm_link',
                'pose': {
                    'position': [0.0, 0.0, 0.1],
                    'orientation': [0.0, 0.0, 0.0, 1.0]
                },
                'axis': [0.0, 0.0, 1.0],
                'limits': {
                    'lower': -1.57,
                    'upper': 1.57,
                    'effort': 10.0,
                    'velocity': 1.0
                }
            }
        ],
        'actuators': [
            {
                'name': 'base_motor',
                'type': 'position',
                'joint': 'base_joint'
            }
        ],
        'sensors': [
            {
                'name': 'base_encoder',
                'type': 'position',
                'parent_link': 'arm_link',
                'joint': 'base_joint'
            }
        ]
    }
    
    try:
        # Demonstrate create_schema_from_dict
        print("🔧 Creating schema from dictionary...")
        schema = create_schema_from_dict(robot_data)
        
        print("✅ Schema created successfully!")
        print(f"  Robot: {schema.metadata.name}")
        print(f"  Components: {len(schema.links)} links, {len(schema.joints)} joints")
        
        # Test with comprehensive schema file if available
        comprehensive_schema_path = Path("config/comprehensive_robot_schema.yaml")
        if comprehensive_schema_path.exists():
            print("\n📁 Testing with comprehensive schema file...")
            
            # Parse with utility function
            schema = parse_unified_schema(
                comprehensive_schema_path, 
                validate=True, 
                verbose=False  # Silent parsing
            )
            
            print(f"✅ Loaded {schema.metadata.name} with {len(schema.links)} links")
            
            # Parse again with verbose output
            print("\n🔄 Parsing with verbose output:")
            parse_unified_schema(
                comprehensive_schema_path, 
                validate=True, 
                verbose=True
            )
        else:
            print("ℹ️ Comprehensive schema file not found - skipping file parsing demo")
        
        print("✅ Utility functions example completed!")
        
    except Exception as e:
        print(f"❌ Utility functions example failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all examples."""
    print("🤖 Robot Format Parser Examples")
    print("=" * 50)
    
    try:
        # Run all examples
        example_basic_urdf_parsing()
        example_basic_mjcf_parsing()
        example_validation_features()
        example_error_recovery()
        example_schema_parsing()
        example_comprehensive_schema_parsing()
        example_utility_functions()
        
        print("🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
