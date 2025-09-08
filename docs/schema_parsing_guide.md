# Unified Schema Parsing Guide

This guide explains how to use the unified schema parsing functionality in the robot format converter.

## Overview

The robot format converter includes comprehensive support for parsing unified schema files (YAML/JSON format) that define robot descriptions using a common intermediate format. This allows you to:

- Parse robot descriptions from YAML or JSON files
- Create robot schemas programmatically from dictionaries  
- Validate schema structure and content
- Convert between different robot description formats

## Quick Start

### Basic Schema Parsing

```python
from robot_format_converter.examples.parser_examples import parse_unified_schema

# Parse a schema file
schema = parse_unified_schema('my_robot.yaml')

# Access robot data
print(f"Robot: {schema.metadata.name}")
print(f"Links: {len(schema.links)}")
print(f"Joints: {len(schema.joints)}")
```

### Create Schema from Dictionary

```python
from robot_format_converter.examples.parser_examples import create_schema_from_dict

robot_data = {
    'metadata': {
        'name': 'my_robot',
        'version': '1.0',
        'description': 'My custom robot'
    },
    'links': [...],
    'joints': [...]
}

schema = create_schema_from_dict(robot_data)
```

## Utility Functions

### `parse_unified_schema(schema_file_path, validate=True, verbose=True)`

Parse a unified schema file and return a CommonSchema object.

**Parameters:**
- `schema_file_path` (str or Path): Path to YAML or JSON schema file
- `validate` (bool): Whether to perform validation after parsing  
- `verbose` (bool): Whether to print parsing progress

**Returns:**
- `CommonSchema`: Parsed robot schema object

**Examples:**
```python
# Basic parsing with validation and verbose output
schema = parse_unified_schema('robot.yaml')

# Parse silently without validation  
schema = parse_unified_schema('robot.yaml', validate=False, verbose=False)

# Parse with validation but silent
schema = parse_unified_schema('robot.yaml', verbose=False)
```

### `create_schema_from_dict(schema_dict, validate=True)`

Create a CommonSchema object from a dictionary.

**Parameters:**
- `schema_dict` (dict): Dictionary containing schema data
- `validate` (bool): Whether to validate the resulting schema

**Returns:**
- `CommonSchema`: Created schema object

## Schema File Format

### Basic Structure

```yaml
metadata:
  name: robot_name
  version: "1.0"
  author: "Author Name"
  description: "Robot description"
  source_format: schema

links:
  - name: base_link
    mass: 10.0
    center_of_mass: [0.0, 0.0, 0.0]
    inertia:
      ixx: 1.0
      iyy: 1.0  
      izz: 1.0
      ixy: 0.0
      ixz: 0.0
      iyz: 0.0

joints:
  - name: joint1
    type: revolute
    parent_link: base_link
    child_link: link1
    pose:
      position: [0.0, 0.0, 0.1]
      orientation: [0.0, 0.0, 0.0, 1.0]  # quaternion w,x,y,z
    axis: [0.0, 0.0, 1.0]
    limits:
      lower: -3.14159
      upper: 3.14159
      effort: 100.0
      velocity: 2.0

actuators:
  - name: motor1
    type: position
    joint: joint1
    gear_ratio: 100.0
    control_range: [-1.0, 1.0]

sensors:
  - name: encoder1
    type: position
    parent_link: link1
    joint: joint1
    noise_std: 0.001

contacts:
  - name: ground_contact
    link1: base_link
    link2: ground
    surface_properties:
      friction: [1.0, 1.0, 0.01]
      restitution: 0.3
```

### Advanced Features

The schema format supports many advanced features:

#### Assets and Materials
```yaml
assets:
  meshes:
    - name: base_mesh
      file: "meshes/base.stl"
      scale: [1.0, 1.0, 1.0]
      
  materials:
    - name: aluminum
      visual:
        color: [0.7, 0.7, 0.8, 1.0]
        metallic: 0.8
        roughness: 0.3
      physical:
        friction: [1.2, 1.2, 0.01]
        density: 2700.0
```

#### Complex Joint Types
```yaml
joints:
  - name: prismatic_joint
    type: prismatic
    parent_link: base_link
    child_link: slider_link
    axis: [0.0, 0.0, 1.0]
    limits:
      lower: 0.0
      upper: 0.5
      effort: 100.0
      velocity: 1.0
    dynamics:
      damping: 0.1
      friction: 0.05
```

#### Sensor Definitions
```yaml
sensors:
  - name: imu_sensor
    type: imu
    parent_link: base_link
    pose:
      position: [0.0, 0.0, 0.1]
      orientation: [0.0, 0.0, 0.0, 1.0]
    noise_std:
      acceleration: [0.01, 0.01, 0.01]
      angular_velocity: [0.001, 0.001, 0.001]
    update_rate: 100.0
    
  - name: camera
    type: camera  
    parent_link: head_link
    resolution: [640, 480]
    field_of_view: [1.0472, 0.7854]  # radians
    update_rate: 30.0
```

## Working with Parsed Schemas

### Accessing Schema Data

```python
schema = parse_unified_schema('robot.yaml')

# Metadata
print(f"Name: {schema.metadata.name}")
print(f"Version: {schema.metadata.version}")
print(f"Description: {schema.metadata.description}")

# Links
for link in schema.links:
    print(f"Link: {link.name}, Mass: {link.mass}kg")
    print(f"  CoM: ({link.center_of_mass.x}, {link.center_of_mass.y}, {link.center_of_mass.z})")

# Joints  
for joint in schema.joints:
    print(f"Joint: {joint.name} ({joint.type.value})")
    print(f"  Connects: {joint.parent_link} -> {joint.child_link}")
    if joint.limits:
        print(f"  Limits: [{joint.limits.lower}, {joint.limits.upper}]")

# Actuators
for actuator in schema.actuators:
    print(f"Actuator: {actuator.name} ({actuator.type}) -> {actuator.joint}")

# Sensors
for sensor in schema.sensors:
    print(f"Sensor: {sensor.name} ({sensor.type}) on {sensor.parent_link}")
```

### Schema Validation

```python
# Validate schema structure
issues = schema.validate()
if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Schema validation passed!")

# Get root links (links with no parent joints)
try:
    root_links = schema.get_root_links()
    print(f"Root links: {[link.name for link in root_links]}")
except Exception as e:
    print(f"Error finding root links: {e}")
```

### Finding Schema Elements

```python
# Find specific links and joints
base_link = schema.get_link('base_link')
shoulder_joint = schema.get_joint('shoulder_joint')

if base_link:
    print(f"Found link: {base_link.name} with mass {base_link.mass}kg")

if shoulder_joint:
    print(f"Found joint: {shoulder_joint.name} of type {shoulder_joint.type.value}")
```

## Error Handling

The parsing functions provide comprehensive error handling:

```python
try:
    schema = parse_unified_schema('robot.yaml')
except FileNotFoundError:
    print("Schema file not found")
except ValueError as e:
    print(f"Invalid file format: {e}")
except Exception as e:
    print(f"Parsing error: {e}")
```

## Integration with Format Converters

Once you have a parsed schema, you can convert it to other formats:

```python
from robot_format_converter.exporters import URDFExporter, MJCFExporter

# Parse schema
schema = parse_unified_schema('robot.yaml')

# Export to URDF
urdf_exporter = URDFExporter()
urdf_content = urdf_exporter.export(schema)

# Export to MJCF  
mjcf_exporter = MJCFExporter()
mjcf_content = mjcf_exporter.export(schema)
```

## Examples

The `examples/` directory contains several demonstration scripts:

- `parser_examples.py` - Comprehensive examples of all parser capabilities
- `simple_schema_parsing_demo.py` - Simple demonstration of utility functions
- `config/example_schema.yaml` - Basic schema example
- `config/comprehensive_robot_schema.yaml` - Advanced schema with all features

To run the examples:

```bash
cd examples/
python parser_examples.py
python simple_schema_parsing_demo.py
```

## Best Practices

1. **Use validation**: Always validate schemas after parsing to catch structural issues
2. **Handle errors gracefully**: Wrap parsing calls in try-catch blocks
3. **Check file existence**: Verify files exist before attempting to parse
4. **Use appropriate verbosity**: Enable verbose mode during development, disable in production
5. **Follow schema conventions**: Use SI units (meters, radians, kg, seconds)
6. **Validate your schema files**: Use the comprehensive schema as a reference for proper structure

## Troubleshooting

### Common Issues

1. **"YAML module not available"**: Install PyYAML: `pip install pyyaml`
2. **"Unsupported file format"**: Ensure file has `.yaml`, `.yml`, or `.json` extension
3. **"Validation issues found"**: Check for missing required fields or invalid references
4. **"No root links found"**: Verify joint parent/child relationships form a valid tree

### Debug Tips

1. Use `verbose=True` to see detailed parsing progress
2. Check validation output for structural issues  
3. Verify file syntax with a YAML/JSON validator
4. Compare against working example schemas
5. Check that all joint parent/child links exist in the links list

## API Reference

For complete API documentation, see the docstrings in:
- `robot_format_converter.parsers.SchemaParser`
- `robot_format_converter.schema.CommonSchema`
- Example utility functions in `examples/parser_examples.py`
