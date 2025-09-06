"""
Examples demonstrating robot format parser capabilities.
Shows comprehensive usage of URDF and MJCF parsing features.
"""

import tempfile
from pathlib import Path

# Import parsers
from robot_format_converter.parsers import URDFParser, MJCFParser


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
        
        print("🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
