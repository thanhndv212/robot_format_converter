#!/usr/bin/env python3
# Copyright [2021-2025] Thanh Nguyen

"""
UR10 Robot Format Conversion Example

This example demonstrates converting the UR10 robot URDF to our unified schema format
and then converting it back to URDF, showcasing the robot format converter capabilities.
"""

import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from robot_format_converter import FormatConverter


def main():
    """Demonstrate UR10 robot format conversion."""
    
    print("UR10 Robot Format Conversion Example")
    print("=" * 50)
    
    # Get the UR10 URDF path
    ur_description_path = Path(__file__).parent / "ur_description"
    ur10_urdf_path = ur_description_path / "urdf" / "ur10_robot.urdf"
    
    if not ur10_urdf_path.exists():
        print(f"Error: UR10 URDF not found at {ur10_urdf_path}")
        return 1
    
    print(f"Using UR10 URDF: {ur10_urdf_path}")
    
    # Create output directory
    output_dir = Path(__file__).parent / "conversion_outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize converter
    converter = FormatConverter()
    
    try:
        # 1. Convert URDF to Schema
        print(f"\n1. Converting URDF to Schema format...")
        schema_file = output_dir / "ur10_robot_schema.yaml"
        
        schema = converter.to_schema(str(ur10_urdf_path), str(schema_file))
        
        print(f"✓ Schema conversion successful!")
        print(f"  Schema file: {schema_file}")
        print(f"  Robot name: {schema.metadata.name}")
        print(f"  Links: {len(schema.links)}")
        print(f"  Joints: {len(schema.joints)}")
        
        # Show some detailed information about the robot
        print(f"\n  Link details:")
        for i, link in enumerate(schema.links[:5]):  # Show first 5 links
            print(f"    {i+1}. {link.name}")
            if hasattr(link, 'mass') and link.mass:
                print(f"       Mass: {link.mass} kg")
        if len(schema.links) > 5:
            print(f"    ... and {len(schema.links) - 5} more links")
        
        print(f"\n  Joint details:")
        for i, joint in enumerate(schema.joints[:6]):  # Show first 6 joints
            print(f"    {i+1}. {joint.name} ({joint.type})")
            print(f"       Parent: {joint.parent_link} -> Child: {joint.child_link}")
        if len(schema.joints) > 6:
            print(f"    ... and {len(schema.joints) - 6} more joints")
        
        # 2. Convert Schema back to URDF
        print(f"\n2. Converting Schema back to URDF...")
        converted_urdf_file = output_dir / "ur10_converted.urdf"
        
        converter.from_schema(str(schema_file), str(converted_urdf_file))
        
        print(f"✓ URDF conversion successful!")
        print(f"  Converted URDF: {converted_urdf_file}")
        
        # 3. Show file sizes and comparison
        print(f"\n3. File Comparison:")
        original_size = ur10_urdf_path.stat().st_size
        schema_size = schema_file.stat().st_size
        converted_size = converted_urdf_file.stat().st_size
        
        print(f"  Original URDF:    {original_size:,} bytes")
        print(f"  Schema format:    {schema_size:,} bytes")
        print(f"  Converted URDF:   {converted_size:,} bytes")
        
        # 4. Show schema content preview
        if schema_file.exists():
            print(f"\n4. Schema Content Preview:")
            print("-" * 30)
            with open(schema_file, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:20]):  # Show first 20 lines
                    print(f"  {line.rstrip()}")
                if len(lines) > 20:
                    print(f"  ... ({len(lines) - 20} more lines)")
        
        # 5. Show supported formats
        print(f"\n5. Format Converter Capabilities:")
        print("-" * 30)
        formats = converter.engine.get_supported_formats()
        print(f"Input formats (parsers):  {', '.join(formats['parsers'])}")
        print(f"Output formats (exporters): {', '.join(formats['exporters'])}")
        
        # 6. Show conversion matrix
        print(f"\n6. Available Conversions:")
        print("-" * 30)
        matrix = converter.get_conversion_matrix()
        for source, targets in sorted(matrix.items()):
            if targets:
                target_list = [t for t in sorted(targets) if t != source]
                if target_list:
                    print(f"  {source:8} -> {', '.join(target_list)}")
        
        print(f"\n✓ UR10 conversion example completed successfully!")
        print(f"Check the output files in: {output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
