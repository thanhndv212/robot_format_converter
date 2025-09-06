# Copyright [2021-2025] Thanh Nguyen
# Copyright [2022-2023] [CNRS, Toward SAS]

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Robot Format Converter Package

A comprehensive package for converting between different robot description formats
and a unified common schema. Supports bidirectional conversion between:

- URDF (Unified Robot Description Format)
- SDF (Simulation Description Format) 
- MJCF (MuJoCo Model Format)
- USD (Universal Scene Description)
- Custom FIGAROH Schema

Features:
- Format detection and validation
- Semantic preservation across conversions
- Extensible converter architecture
- Command-line tools for batch processing
- Integration with FIGAROH calibration workflows
"""

__version__ = "1.0.0"
__author__ = "Thanh D. V. Nguyen"

from .core import FormatConverter, ConversionEngine
from .parsers import URDFParser, SDFParser, MJCFParser, USDParser, SchemaParser
from .exporters import URDFExporter, SDFExporter, MJCFExporter, USDExporter, SchemaExporter
from .schema import CommonSchema, Metadata, Link, Joint, Actuator, Sensor
from .utils import detect_format, get_format_info, format_file_size

__all__ = [
    # Core classes
    "FormatConverter",
    "ConversionEngine",
    
    # Parsers
    "URDFParser", 
    "SDFParser",
    "MJCFParser",
    "USDParser", 
    "SchemaParser",
    
    # Exporters
    "URDFExporter",
    "SDFExporter", 
    "MJCFExporter",
    "USDExporter",
    "SchemaExporter",
    
    # Schema components
    "CommonSchema",
    "RobotModel",
    "Joint",
    "Link", 
    "Actuator",
    "Sensor",
    
    # Utilities
    "detect_format",
    "validate_schema", 
    "conversion_matrix",
]
