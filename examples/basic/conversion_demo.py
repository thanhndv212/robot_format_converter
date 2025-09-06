"""
Robot format conversion examples with validation and error handling.
"""

import logging
from pathlib import Path
import json
from typing import Dict, List, Any

# Import parsers
from robot_format_converter.parsers import URDFParser, MJCFParser
from robot_format_converter.exporters import URDFExporter, MJCFExporter
from robot_format_converter.schema import CommonSchema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def conversion_example():
    """Demonstrate conversion with validation and error reporting."""
    
    # Create sample URDF with various elements
    sample_urdf = """<?xml version="1.0"?>
    <robot name="enhanced_test_robot">
        <!-- Define materials -->
        <material name="blue">
            <color rgba="0.0 0.0 1.0 1.0"/>
        </material>
        
        <material name="red">
            <color rgba="1.0 0.0 0.0 1.0"/>
        </material>
        
        <!-- Base link -->
        <link name="base_link">
            <inertial>
                <mass value="10.0"/>
                <origin xyz="0 0 0.1"/>
                <inertia ixx="0.8" iyy="0.8" izz="0.1" ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <origin xyz="0 0 0" rpy="0 0 0"/>
                <geometry>
                    <box size="0.4 0.3 0.2"/>
                </geometry>
                <material name="blue"/>
            </visual>
            <collision>
                <origin xyz="0 0 0" rpy="0 0 0"/>
                <geometry>
                    <box size="0.4 0.3 0.2"/>
                </geometry>
            </collision>
        </link>
        
        <!-- First joint and link -->
        <joint name="joint1" type="revolute">
            <parent link="base_link"/>
            <child link="link1"/>
            <origin xyz="0.2 0 0.1" rpy="0 0 0"/>
            <axis xyz="0 0 1"/>
            <limit lower="-3.14159" upper="3.14159" effort="50" velocity="2.0"/>
            <dynamics damping="0.1" friction="0.05"/>
        </joint>
        
        <link name="link1">
            <inertial>
                <mass value="2.0"/>
                <origin xyz="0 0 0.15"/>
                <inertia ixx="0.1" iyy="0.1" izz="0.02" ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <origin xyz="0 0 0.15" rpy="0 0 0"/>
                <geometry>
                    <cylinder radius="0.05" length="0.3"/>
                </geometry>
                <material name="red"/>
            </visual>
            <collision>
                <origin xyz="0 0 0.15" rpy="0 0 0"/>
                <geometry>
                    <cylinder radius="0.05" length="0.3"/>
                </geometry>
            </collision>
        </link>
        
        <!-- Second joint and link -->
        <joint name="joint2" type="prismatic">
            <parent link="link1"/>
            <child link="link2"/>
            <origin xyz="0 0 0.3" rpy="0 0 0"/>
            <axis xyz="0 0 1"/>
            <limit lower="0" upper="0.2" effort="100" velocity="0.5"/>
            <dynamics damping="0.05"/>
        </joint>
        
        <link name="link2">
            <inertial>
                <mass value="1.0"/>
                <origin xyz="0 0 0.05"/>
                <inertia ixx="0.02" iyy="0.02" izz="0.01" ixy="0" ixz="0" iyz="0"/>
            </inertial>
            <visual>
                <origin xyz="0 0 0.05" rpy="0 0 0"/>
                <geometry>
                    <sphere radius="0.08"/>
                </geometry>
                <material name="blue"/>
            </visual>
            <collision>
                <origin xyz="0 0 0.05" rpy="0 0 0"/>
                <geometry>
                    <sphere radius="0.08"/>
                </geometry>
            </collision>
        </link>
    </robot>"""
    
    # Save sample URDF
    urdf_path = Path("enhanced_test_robot.urdf")
    with open(urdf_path, 'w') as f:
        f.write(sample_urdf)
    
    print("=== Robot Format Conversion Demo ===\\n")
    
    try:
        # Parse URDF with parser
        print("1. Parsing URDF with validation...")
        urdf_parser = URDFParser()
        
        if not urdf_parser.can_parse(urdf_path):
            print("❌ File is not a valid URDF!")
            return
        
        schema = urdf_parser.parse(urdf_path)
        
        # Report parsing results
        context = schema.extensions.get('parse_context', {})
        warnings = context.get('warnings', [])
        errors = context.get('errors', [])
        
        print(f"✅ Parsing completed:")
        print(f"   - Links: {len(schema.links)}")
        print(f"   - Joints: {len(schema.joints)}")
        print(f"   - Warnings: {len(warnings)}")
        print(f"   - Errors: {len(errors)}")
        
        if warnings:
            print("\\n⚠️  Warnings:")
            for warning in warnings[:5]:  # Show first 5 warnings
                print(f"   - {warning}")
        
        if errors:
            print("\\n❌ Errors:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
        
        # Analyze robot structure
        print("\\n2. Robot Structure Analysis:")
        analyze_robot_structure(schema)
        
        # Convert to MJCF
        print("\\n3. Converting to MJCF format...")
        mjcf_exporter = MJCFExporter()
        mjcf_content = mjcf_exporter.export(schema, "enhanced_test_robot.xml")
        
        with open("enhanced_test_robot.xml", 'w') as f:
            f.write(mjcf_content)
        
        print("✅ MJCF export completed: enhanced_test_robot.xml")
        
        # Validate round-trip conversion
        print("\\n4. Validating round-trip conversion...")
        validate_round_trip_conversion("enhanced_test_robot.xml", schema)
        
        # Generate conversion report
        print("\\n5. Generating conversion report...")
        generate_conversion_report(schema, warnings, errors)
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        logger.exception("Conversion error")
    
    finally:
        # Clean up
        for file_path in ["enhanced_test_robot.urdf", "enhanced_test_robot.xml"]:
            if Path(file_path).exists():
                Path(file_path).unlink()


def analyze_robot_structure(schema: CommonSchema):
    """Analyze and report robot structure."""
    
    # Build kinematic tree
    parent_child_map = {}
    for joint in schema.joints:
        parent_child_map[joint.child_link] = joint.parent_link
    
    # Find root links (no parent or parent is 'world')
    all_links = {link.name for link in schema.links}
    child_links = set(parent_child_map.keys())
    root_links = all_links - child_links
    
    # Add 'world' parents to root
    for joint in schema.joints:
        if joint.parent_link == 'world' or joint.parent_link not in all_links:
            root_links.add(joint.parent_link)
    
    print(f"   - Root links: {list(root_links)}")
    
    # Calculate tree depth
    def get_depth(link_name, visited=None):
        if visited is None:
            visited = set()
        
        if link_name in visited or link_name == 'world':
            return 0
        
        visited.add(link_name)
        
        if link_name not in parent_child_map:
            return 1
        
        return 1 + get_depth(parent_child_map[link_name], visited)
    
    max_depth = max((get_depth(link.name) for link in schema.links), default=0)
    print(f"   - Maximum tree depth: {max_depth}")
    
    # Joint type distribution
    joint_types = {}
    for joint in schema.joints:
        joint_type = joint.type.value
        joint_types[joint_type] = joint_types.get(joint_type, 0) + 1
    
    print(f"   - Joint types: {joint_types}")
    
    # Mass distribution
    total_mass = sum(link.mass for link in schema.links)
    print(f"   - Total mass: {total_mass:.2f} kg")
    
    # Identify potential issues
    issues = []
    
    # Check for zero-mass links
    zero_mass_links = [link.name for link in schema.links if link.mass <= 0]
    if zero_mass_links:
        issues.append(f"Zero-mass links: {zero_mass_links}")
    
    # Check for missing visual/collision geometry
    no_visual_links = [link.name for link in schema.links if not link.visuals]
    no_collision_links = [link.name for link in schema.links if not link.collisions]
    
    if no_visual_links:
        issues.append(f"Links without visual geometry: {no_visual_links}")
    if no_collision_links:
        issues.append(f"Links without collision geometry: {no_collision_links}")
    
    if issues:
        print("\\n   ⚠️  Potential issues:")
        for issue in issues:
            print(f"      - {issue}")


def validate_round_trip_conversion(mjcf_file: str, original_schema: CommonSchema):
    """Validate round-trip conversion by parsing the exported MJCF."""
    
    try:
        mjcf_parser = MJCFParser()
        
        if not mjcf_parser.can_parse(mjcf_file):
            print("❌ Generated MJCF is not valid")
            return
        
        converted_schema = mjcf_parser.parse(mjcf_file)
        
        # Compare basic structure
        print("   Comparing structures:")
        print(f"   - Original links: {len(original_schema.links)}")
        print(f"   - Converted links: {len(converted_schema.links)}")
        print(f"   - Original joints: {len(original_schema.joints)}")
        print(f"   - Converted joints: {len(converted_schema.joints)}")
        
        # Check for preserved link names
        original_names = {link.name for link in original_schema.links}
        converted_names = {link.name for link in converted_schema.links}
        
        missing_links = original_names - converted_names
        extra_links = converted_names - original_names
        
        if missing_links:
            print(f"   ⚠️  Missing links in conversion: {missing_links}")
        if extra_links:
            print(f"   ℹ️  Extra links in conversion: {extra_links}")
        
        if not missing_links and not extra_links:
            print("   ✅ All links preserved in conversion")
        
    except Exception as e:
        print(f"   ❌ Round-trip validation failed: {e}")


def generate_conversion_report(schema: CommonSchema, warnings: List[str], errors: List[str]):
    """Generate a comprehensive conversion report."""
    
    report = {
        "conversion_summary": {
            "robot_name": schema.metadata.name,
            "source_format": schema.metadata.source_format,
            "total_links": len(schema.links),
            "total_joints": len(schema.joints),
            "total_actuators": len(schema.actuators),
            "total_sensors": len(schema.sensors),
            "warnings_count": len(warnings),
            "errors_count": len(errors)
        },
        
        "robot_structure": {
            "links": [
                {
                    "name": link.name,
                    "mass": link.mass,
                    "visual_count": len(link.visuals),
                    "collision_count": len(link.collisions)
                }
                for link in schema.links
            ],
            
            "joints": [
                {
                    "name": joint.name,
                    "type": joint.type.value,
                    "parent_link": joint.parent_link,
                    "child_link": joint.child_link,
                    "has_limits": joint.limits is not None
                }
                for joint in schema.joints
            ]
        },
        
        "validation_results": {
            "warnings": warnings,
            "errors": errors
        }
    }
    
    # Save report
    with open("conversion_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print("   ✅ Conversion report saved: conversion_report.json")
    
    # Clean up report file
    if Path("conversion_report.json").exists():
        Path("conversion_report.json").unlink()


def batch_conversion_example():
    """Demonstrate batch conversion of multiple robot files."""
    
    print("\\n=== Batch Conversion Example ===\\n")
    
    # Create multiple sample robot files
    sample_robots = {
        "simple_robot.urdf": """<?xml version="1.0"?>
        <robot name="simple_robot">
            <link name="base_link">
                <inertial>
                    <mass value="1.0"/>
                    <inertia ixx="0.1" iyy="0.1" izz="0.1" ixy="0" ixz="0" iyz="0"/>
                </inertial>
            </link>
        </robot>""",
        
        "arm_robot.urdf": """<?xml version="1.0"?>
        <robot name="arm_robot">
            <link name="base_link">
                <inertial>
                    <mass value="5.0"/>
                    <inertia ixx="0.5" iyy="0.5" izz="0.1" ixy="0" ixz="0" iyz="0"/>
                </inertial>
            </link>
            
            <link name="arm_link">
                <inertial>
                    <mass value="2.0"/>
                    <inertia ixx="0.2" iyy="0.2" izz="0.05" ixy="0" ixz="0" iyz="0"/>
                </inertial>
            </link>
            
            <joint name="arm_joint" type="revolute">
                <parent link="base_link"/>
                <child link="arm_link"/>
                <axis xyz="0 0 1"/>
                <limit lower="-3.14" upper="3.14" effort="10" velocity="1"/>
            </joint>
        </robot>"""
    }
    
    # Process each robot
    results = {}
    
    for filename, content in sample_robots.items():
        print(f"Processing {filename}...")
        
        # Save file
        with open(filename, 'w') as f:
            f.write(content)
        
        try:
            # Parse
            parser = URDFParser()
            schema = parser.parse(filename)
            
            # Convert to MJCF
            exporter = MJCFExporter()
            mjcf_filename = filename.replace('.urdf', '.xml')
            mjcf_content = exporter.export(schema, mjcf_filename)
            
            with open(mjcf_filename, 'w') as f:
                f.write(mjcf_content)
            
            # Record results
            context = schema.extensions.get('parse_context', {})
            results[filename] = {
                "status": "success",
                "links": len(schema.links),
                "joints": len(schema.joints),
                "warnings": len(context.get('warnings', [])),
                "errors": len(context.get('errors', [])),
                "output_file": mjcf_filename
            }
            
            print(f"   ✅ Success - {len(schema.links)} links, {len(schema.joints)} joints")
            
        except Exception as e:
            results[filename] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"   ❌ Failed: {e}")
        
        finally:
            # Clean up
            for file_path in [filename, filename.replace('.urdf', '.xml')]:
                if Path(file_path).exists():
                    Path(file_path).unlink()
    
    # Summary
    successful = sum(1 for r in results.values() if r["status"] == "success")
    print(f"\\nBatch conversion completed:")
    print(f"   - Successful: {successful}/{len(results)}")
    print(f"   - Failed: {len(results) - successful}/{len(results)}")


if __name__ == "__main__":
    # Run examples
    conversion_example()
    batch_conversion_example()
    
    print("\\n✅ All examples completed!")
