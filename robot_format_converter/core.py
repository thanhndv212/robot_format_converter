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
Core format conversion engine and orchestration classes.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Type, List
from abc import ABC, abstractmethod

from .schema import CommonSchema
from .utils import detect_format, validate_schema

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for format parsers."""
    
    @abstractmethod
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse input file and return common schema representation."""
        pass
    
    @abstractmethod
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if this parser can handle the given file."""
        pass


class BaseExporter(ABC):
    """Abstract base class for format exporters."""
    
    @abstractmethod
    def export(self, schema: CommonSchema, output_path: Union[str, Path]) -> None:
        """Export common schema to target format."""
        pass
    
    @abstractmethod
    def get_extension(self) -> str:
        """Return the file extension for this format."""
        pass


class ConversionEngine:
    """
    Core conversion engine that orchestrates format conversions.
    
    The engine maintains a registry of parsers and exporters for different
    formats and handles the conversion workflow between them via the common
    schema intermediate representation.
    
    Example:
        >>> engine = ConversionEngine()
        >>> engine.register_parser('urdf', URDFParser())
        >>> engine.register_exporter('sdf', SDFExporter())
        >>> engine.convert('robot.urdf', 'robot.sdf')
    """
    
    def __init__(self):
        self.parsers: Dict[str, BaseParser] = {}
        self.exporters: Dict[str, BaseExporter] = {}
    
    def register_parser(self, format_name: str, parser: BaseParser) -> None:
        """Register a parser for a specific format."""
        self.parsers[format_name.lower()] = parser
        logger.debug(f"Registered parser for format: {format_name}")
    
    def register_exporter(self, format_name: str, exporter: BaseExporter) -> None:
        """Register an exporter for a specific format."""
        self.exporters[format_name.lower()] = exporter
        logger.debug(f"Registered exporter for format: {format_name}")
    
    def get_supported_formats(self) -> Dict[str, Dict[str, bool]]:
        """Return supported formats for parsing and exporting."""
        return {
            'parsers': list(self.parsers.keys()),
            'exporters': list(self.exporters.keys())
        }
    
    def convert(
        self, 
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        validation: bool = True
    ) -> CommonSchema:
        """
        Convert between robot description formats.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file  
            source_format: Source format (auto-detected if None)
            target_format: Target format (inferred from extension if None)
            validation: Whether to validate schema during conversion
            
        Returns:
            CommonSchema representation of the robot model
            
        Raises:
            ValueError: If formats are unsupported or conversion fails
            FileNotFoundError: If input file doesn't exist
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Auto-detect source format if not specified
        if source_format is None:
            source_format = detect_format(input_path)
            if source_format is None:
                raise ValueError(f"Cannot detect format for: {input_path}")
        
        # Infer target format from extension if not specified
        if target_format is None:
            target_format = output_path.suffix.lstrip('.').lower()
        
        # Get appropriate parser and exporter
        parser = self.parsers.get(source_format.lower())
        if parser is None:
            raise ValueError(f"No parser available for format: {source_format}")
        
        exporter = self.exporters.get(target_format.lower())  
        if exporter is None:
            raise ValueError(f"No exporter available for format: {target_format}")
        
        # Parse input to common schema
        logger.info(f"Parsing {source_format.upper()} file: {input_path}")
        schema = parser.parse(input_path)
        
        # Validate schema if requested
        if validation:
            logger.debug("Validating intermediate schema")
            validate_schema(schema)
        
        # Export to target format
        logger.info(f"Exporting to {target_format.upper()}: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        exporter.export(schema, output_path)
        
        logger.info(f"Conversion complete: {input_path} -> {output_path}")
        return schema


class FormatConverter:
    """
    High-level interface for robot format conversions.
    
    This class provides a simplified API for common conversion tasks,
    with built-in parsers and exporters for standard formats.
    
    Example:
        >>> converter = FormatConverter()
        >>> converter.urdf_to_sdf('robot.urdf', 'robot.sdf')
        >>> converter.batch_convert('models/', 'output/', 'urdf', 'mjcf')
    """
    
    def __init__(self):
        self.engine = ConversionEngine()
        self._register_default_processors()
    
    def _register_default_processors(self) -> None:
        """Register default parsers and exporters for standard formats."""
        # Import here to avoid circular imports
        from .parsers import URDFParser, SDFParser, MJCFParser, SchemaParser
        from .exporters import URDFExporter, SDFExporter, MJCFExporter, SchemaExporter
        
        # Register parsers
        self.engine.register_parser('urdf', URDFParser())
        self.engine.register_parser('sdf', SDFParser()) 
        self.engine.register_parser('mjcf', MJCFParser())
        self.engine.register_parser('xml', MJCFParser())  # MJCF is XML
        self.engine.register_parser('schema', SchemaParser())
        self.engine.register_parser('yaml', SchemaParser())
        self.engine.register_parser('json', SchemaParser())
        
        # Register exporters
        self.engine.register_exporter('urdf', URDFExporter())
        self.engine.register_exporter('sdf', SDFExporter())
        self.engine.register_exporter('mjcf', MJCFExporter()) 
        self.engine.register_exporter('xml', MJCFExporter())
        self.engine.register_exporter('schema', SchemaExporter())
        self.engine.register_exporter('yaml', SchemaExporter())
        self.engine.register_exporter('json', SchemaExporter())
        
        # Try to register USD support if available
        try:
            from .parsers import USDParser
            from .exporters import USDExporter
            self.engine.register_parser('usd', USDParser())
            self.engine.register_parser('usda', USDParser()) 
            self.engine.register_exporter('usd', USDExporter())
            self.engine.register_exporter('usda', USDExporter())
        except ImportError:
            logger.debug("USD support not available (missing pxr module)")
    
    def convert(
        self,
        input_path: Union[str, Path], 
        output_path: Union[str, Path],
        **kwargs
    ) -> CommonSchema:
        """Convert between formats using the conversion engine."""
        return self.engine.convert(input_path, output_path, **kwargs)
    
    def urdf_to_sdf(self, urdf_path: str, sdf_path: str) -> CommonSchema:
        """Convert URDF to SDF format."""
        return self.convert(urdf_path, sdf_path, 'urdf', 'sdf')
    
    def urdf_to_mjcf(self, urdf_path: str, mjcf_path: str) -> CommonSchema:
        """Convert URDF to MJCF format.""" 
        return self.convert(urdf_path, mjcf_path, 'urdf', 'mjcf')
    
    def sdf_to_urdf(self, sdf_path: str, urdf_path: str) -> CommonSchema:
        """Convert SDF to URDF format."""
        return self.convert(sdf_path, urdf_path, 'sdf', 'urdf')
    
    def to_schema(self, input_path: str, schema_path: str) -> CommonSchema:
        """Convert any supported format to common schema."""
        return self.convert(input_path, schema_path, target_format='schema')
    
    def from_schema(self, schema_path: str, output_path: str) -> CommonSchema:
        """Convert from common schema to any supported format."""
        return self.convert(schema_path, output_path, source_format='schema')
    
    def batch_convert(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path], 
        source_format: str,
        target_format: str,
        pattern: str = "*"
    ) -> List[Path]:
        """
        Batch convert files in a directory.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            source_format: Source file format
            target_format: Target file format  
            pattern: File pattern to match (default: "*")
            
        Returns:
            List of successfully converted output files
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find matching files
        ext = f".{source_format}"
        input_files = list(input_dir.glob(f"{pattern}{ext}"))
        
        if not input_files:
            logger.warning(f"No {source_format} files found in {input_dir}")
            return []
        
        converted_files = []
        target_ext = f".{target_format}"
        
        for input_file in input_files:
            output_file = output_dir / (input_file.stem + target_ext)
            try:
                self.convert(input_file, output_file, source_format, target_format)
                converted_files.append(output_file)
            except Exception as e:
                logger.error(f"Failed to convert {input_file}: {e}")
        
        logger.info(f"Batch conversion complete: {len(converted_files)}/{len(input_files)} files converted")
        return converted_files
    
    def get_conversion_matrix(self) -> Dict[str, List[str]]:
        """Get matrix of supported conversion paths."""
        formats = self.engine.get_supported_formats()
        matrix = {}
        
        for source_fmt in formats['parsers']:
            matrix[source_fmt] = formats['exporters']
        
        return matrix
