# Robot Format Converter

[![Python Package](https://img.shields.io/pypi/v/robot-format-converter.svg)](https://pypi.org/project/robot-format-converter/)
[![Python Version](https://img.shields.io/pypi/pyversions/robot-format-converter.svg)](https://pypi.org/project/robot-format-converter/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A universal robot description format converter that enables seamless conversion between different robot modeling formats including URDF, SDF, MJCF, USD, and a unified schema format.

## Features

- **Multi-Format Support**: Convert between URDF, SDF, MJCF, USD, and custom schema formats
- **Unified Schema**: Common intermediate representation preserving robot structure and properties
- **Command-Line Interface**: Easy-to-use CLI for single file and batch conversions
- **Python API**: Programmatic access for integration into robotics pipelines
- **Format Detection**: Automatic format detection from file extensions and content
- **Validation**: Built-in schema validation and error checking
- **Extensible Architecture**: Easy to add support for new formats

## Supported Formats

| Format | Extension | Read | Write | Description |
|--------|-----------|------|-------|-------------|
| URDF   | `.urdf`   | ✅   | ✅    | Unified Robot Description Format |
| SDF    | `.sdf`    | 🚧   | 🚧    | Simulation Description Format |
| MJCF   | `.xml`    | 🚧   | 🚧    | MuJoCo Modeling Format |
| USD    | `.usd`, `.usda` | 🚧   | 🚧    | Universal Scene Description |
| Schema | `.yaml`, `.json` | ✅   | ✅    | Custom unified schema |

*Legend: ✅ Implemented, 🚧 In Development*

## Installation

### From PyPI (Recommended)

```bash
pip install robot-format-converter
```

### From Source

```bash
git clone https://github.com/thanhndv212/robot_format_converter.git
cd robot_format_converter
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/thanhndv212/robot_format_converter.git
cd robot_format_converter
pip install -e .[dev]
```

## Quick Start

### Command Line Interface

**Single File Conversion:**
```bash
# Convert URDF to SDF
robot-convert convert robot.urdf robot.sdf

# Convert with explicit format specification
robot-convert convert --source urdf --target mjcf robot.urdf robot.xml

# Get file information
robot-convert info robot.urdf
```

**Batch Conversion:**
```bash
# Convert all URDF files in a directory to SDF
robot-convert batch-convert models/ output/ urdf sdf

# Convert with file pattern
robot-convert batch-convert models/ output/ urdf sdf --pattern "*.urdf"
```

**Validation:**
```bash
# Validate a schema file
robot-convert validate robot_schema.yaml

# List supported formats
robot-convert list-formats
```

### Python API

**Basic Conversion:**
```python
from robot_format_converter import FormatConverter

# Create converter instance
converter = FormatConverter()

# Convert single file
schema = converter.convert('robot.urdf', 'robot.sdf')
print(f"Converted robot: {schema.metadata.name}")
print(f"Links: {len(schema.links)}, Joints: {len(schema.joints)}")

# Batch convert directory
converted_files = converter.batch_convert(
    'input_models/', 
    'output_models/', 
    'urdf', 
    'sdf'
)
print(f"Converted {len(converted_files)} files")
```

**Advanced Usage:**
```python
from robot_format_converter import FormatConverter, CommonSchema
from pathlib import Path

converter = FormatConverter()

# Convert to intermediate schema format
schema = converter.to_schema('robot.urdf', 'robot_schema.yaml')

# Access robot components
for link in schema.links:
    print(f"Link: {link.name}")
    if link.visual:
        print(f"  Visual: {link.visual.geometry}")
    if link.collision:
        print(f"  Collision: {link.collision.geometry}")

for joint in schema.joints:
    print(f"Joint: {joint.name} ({joint.type})")
    print(f"  Parent: {joint.parent} -> Child: {joint.child}")

# Convert from schema to target format
converter.from_schema('robot_schema.yaml', 'output.sdf')
```

**Format Detection:**
```python
from robot_format_converter.utils import detect_format, get_format_info

# Detect format from file
format_name = detect_format('robot.urdf')
print(f"Detected format: {format_name}")

# Get format information
info = get_format_info(format_name)
print(f"Format description: {info['description']}")
print(f"Supported features: {info['features']}")
```

## Schema Format

The unified schema format provides a common intermediate representation:

```yaml
metadata:
  name: "my_robot"
  version: "1.0"
  author: "Robot Designer"
  description: "A sample robot description"

links:
  - name: "base_link"
    inertial:
      mass: 1.0
      center_of_mass: [0, 0, 0]
      inertia_matrix: [1, 0, 0, 1, 0, 1]
    visual:
      geometry:
        type: "box"
        size: [0.1, 0.1, 0.1]
      material:
        color: [1, 0, 0, 1]
    collision:
      geometry:
        type: "box"
        size: [0.1, 0.1, 0.1]

joints:
  - name: "joint1"
    type: "revolute"
    parent: "base_link"
    child: "link1"
    origin:
      xyz: [0, 0, 0.1]
      rpy: [0, 0, 0]
    axis: [0, 0, 1]
    limits:
      lower: -3.14
      upper: 3.14
      effort: 10
      velocity: 1
```

## Architecture

The converter uses a modular architecture with clear separation of concerns:

```
robot_format_converter/
├── __init__.py          # Public API
├── core.py              # Core conversion engine
├── schema.py            # Unified schema definition
├── parsers.py           # Format-specific parsers
├── exporters.py         # Format-specific exporters
├── utils.py             # Utility functions
└── __main__.py          # CLI interface
```

**Key Components:**

- **FormatConverter**: Main interface for conversions
- **ConversionEngine**: Orchestrates parsing and exporting
- **CommonSchema**: Unified intermediate representation
- **BaseParser/BaseExporter**: Abstract base classes for format handlers
- **Format-specific parsers/exporters**: Handle individual format details

## Adding New Formats

To add support for a new format:

1. **Create Parser Class:**
```python
from robot_format_converter.core import BaseParser
from robot_format_converter.schema import CommonSchema

class MyFormatParser(BaseParser):
    def can_parse(self, file_path: str) -> bool:
        return file_path.endswith('.myformat')
    
    def parse(self, file_path: str) -> CommonSchema:
        # Implementation here
        pass
```

2. **Create Exporter Class:**
```python
from robot_format_converter.core import BaseExporter
from robot_format_converter.schema import CommonSchema

class MyFormatExporter(BaseExporter):
    def can_export(self, format_name: str) -> bool:
        return format_name == 'myformat'
    
    def export(self, schema: CommonSchema, file_path: str) -> None:
        # Implementation here
        pass
```

3. **Register with Engine:**
```python
from robot_format_converter import ConversionEngine

engine = ConversionEngine()
engine.register_parser('myformat', MyFormatParser())
engine.register_exporter('myformat', MyFormatExporter())
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/thanhndv212/robot_format_converter.git
cd robot_format_converter

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
flake8 robot_format_converter/
black robot_format_converter/
isort robot_format_converter/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=format_converter

# Run specific test
pytest tests/test_urdf_parser.py
```

## Examples

Check out the [examples](examples/) directory for more usage examples:

- [Basic conversion](examples/basic_conversion.py)
- [Batch processing](examples/batch_processing.py)
- [Custom format integration](examples/custom_format.py)
- [Schema validation](examples/schema_validation.py)

## Roadmap

- ✅ URDF parser and exporter
- ✅ Unified schema format
- ✅ Command-line interface
- 🚧 SDF parser and exporter
- 🚧 MJCF parser and exporter
- 🚧 USD parser and exporter
- 📋 ROS2 integration
- 📋 Gazebo integration
- 📋 MuJoCo integration
- 📋 Isaac Sim integration

*Legend: ✅ Complete, 🚧 In Progress, 📋 Planned*

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [FIGAROH](https://github.com/thanhndv212/figaroh): Robot calibration and identification library
- [URDF Parser](https://github.com/ros/urdf_parser_py): ROS URDF parsing library
- [PyBullet](https://pybullet.org/): Physics simulation supporting URDF and SDF
- [MuJoCo](https://mujoco.org/): Physics simulator with MJCF format

## Citation

If you use this package in your research, please cite:

```bibtex
@software{robot_format_converter,
  author = {Nguyen, Thanh},
  title = {Robot Format Converter: Universal Robot Description Format Converter},
  year = {2025},
  url = {https://github.com/thanhndv212/robot_format_converter},
  version = {1.0.0}
}
```
