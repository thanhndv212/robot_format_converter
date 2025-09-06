#!/usr/bin/env python3
# Copyright [2021-2025] Thanh Nguyen

"""Basic example demonstrating format conversion capabilities."""

import tempfile
from pathlib import Path

from robot_format_converter import FormatConverter


def main():
    """Demonstrate basic format conversion."""
    
    # Sample URDF content
    urdf_content = '''<?xml version="1.0"?>
<robot name="simple_robot">
  <link name="base_link">
    <inertial>
      <mass value="1.0"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.1" ixy="0" ixz="0" iyy="0.1" iyz="0" izz="0.1"/>
    </inertial>
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="0.1 0.1 0.1"/>
      </geometry>
      <material name="red">
        <color rgba="1 0 0 1"/>
      </material>
    </visual>
  </link>
  
  <link name="moving_link">
    <inertial>
      <mass value="0.5"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.05" ixy="0" ixz="0" iyy="0.05" iyz="0" izz="0.05"/>
    </inertial>
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="0.05" length="0.2"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 1 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="base_joint" type="revolute">
    <parent link="base_link"/>
    <child link="moving_link"/>
    <origin xyz="0 0 0.1" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="10" velocity="1"/>
  </joint>
</robot>'''

    print("Format Converter Basic Example")
    print("=" * 40)
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Write URDF file
        urdf_file = temp_path / "simple_robot.urdf"
        urdf_file.write_text(urdf_content)
        print(f"Created URDF file: {urdf_file}")
        
        # Initialize converter
        converter = FormatConverter()
        
        # Convert to schema format
        schema_file = temp_path / "simple_robot.yaml"
        print(f"\nConverting URDF to schema format...")
        
        try:
            schema = converter.to_schema(str(urdf_file), str(schema_file))
            print(f"✓ Conversion successful!")
            print(f"  Robot name: {schema.metadata.name}")
            print(f"  Links: {len(schema.links)}")
            print(f"  Joints: {len(schema.joints)}")
            
            # Show schema content
            if schema_file.exists():
                print(f"\nSchema file created: {schema_file}")
                print("Schema content preview:")
                print("-" * 20)
                content = schema_file.read_text()
                # Show first few lines
                lines = content.split('\n')[:15]
                for line in lines:
                    print(f"  {line}")
                if len(content.split('\n')) > 15:
                    print("  ...")
            
            # Try to convert back to URDF
            new_urdf_file = temp_path / "converted_robot.urdf"
            print(f"\nConverting schema back to URDF...")
            
            converter.from_schema(str(schema_file), str(new_urdf_file))
            print(f"✓ Back-conversion successful!")
            print(f"  New URDF file: {new_urdf_file}")
            
            # Show conversion info
            print(f"\nConversion Summary:")
            print(f"  Original URDF: {urdf_file.stat().st_size} bytes")
            print(f"  Schema file:   {schema_file.stat().st_size} bytes")
            print(f"  New URDF:      {new_urdf_file.stat().st_size} bytes")
            
        except Exception as e:
            print(f"✗ Conversion failed: {e}")
            return 1
        
        # Show supported formats
        print(f"\nSupported Formats:")
        print(f"-" * 20)
        formats = converter.engine.get_supported_formats()
        print(f"Parsers (can read):   {', '.join(formats['parsers'])}")
        print(f"Exporters (can write): {', '.join(formats['exporters'])}")
        
        # Show conversion matrix
        print(f"\nConversion Matrix:")
        print(f"-" * 20)
        matrix = converter.get_conversion_matrix()
        for source, targets in sorted(matrix.items()):
            if targets:
                print(f"{source:8} -> {', '.join(sorted(targets))}")
    
    print(f"\nExample completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
