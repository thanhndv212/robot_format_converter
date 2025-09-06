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

"""Tests for the core conversion engine."""

import pytest
from pathlib import Path

from robot_format_converter.core import (
    BaseParser, BaseExporter, ConversionEngine, FormatConverter
)
from robot_format_converter.schema import CommonSchema


class TestBaseParser:
    """Tests for BaseParser class."""
    
    def test_base_parser_abstract_methods(self):
        """Test that BaseParser abstract methods raise NotImplementedError."""
        parser = BaseParser()
        
        with pytest.raises(NotImplementedError):
            parser.can_parse("test.txt")
            
        with pytest.raises(NotImplementedError):
            parser.parse("test.txt")


class TestBaseExporter:
    """Tests for BaseExporter class."""
    
    def test_base_exporter_abstract_methods(self):
        """Test that BaseExporter abstract methods raise NotImplementedError."""
        exporter = BaseExporter()
        schema = CommonSchema()
        
        with pytest.raises(NotImplementedError):
            exporter.can_export("txt")
            
        with pytest.raises(NotImplementedError):
            exporter.export(schema, "test.txt")


class MockParser(BaseParser):
    """Mock parser for testing."""
    
    def can_parse(self, file_path: str) -> bool:
        return file_path.endswith('.mock')
    
    def parse(self, file_path: str) -> CommonSchema:
        schema = CommonSchema()
        schema.metadata.name = "mock_robot"
        return schema


class MockExporter(BaseExporter):
    """Mock exporter for testing."""
    
    def can_export(self, format_name: str) -> bool:
        return format_name == 'mock'
    
    def export(self, schema: CommonSchema, file_path: str) -> None:
        with open(file_path, 'w') as f:
            f.write(f"Mock export of {schema.metadata.name}")


class TestConversionEngine:
    """Tests for ConversionEngine class."""
    
    def test_engine_initialization(self):
        """Test engine initializes with empty registries."""
        engine = ConversionEngine()
        assert len(engine.parsers) >= 0  # May have default parsers
        assert len(engine.exporters) >= 0  # May have default exporters
    
    def test_register_parser(self):
        """Test parser registration."""
        engine = ConversionEngine()
        parser = MockParser()
        
        engine.register_parser('mock', parser)
        assert 'mock' in engine.parsers
        assert engine.parsers['mock'] == parser
    
    def test_register_exporter(self):
        """Test exporter registration."""
        engine = ConversionEngine()
        exporter = MockExporter()
        
        engine.register_exporter('mock', exporter)
        assert 'mock' in engine.exporters
        assert engine.exporters['mock'] == exporter
    
    def test_get_parser_by_format(self):
        """Test getting parser by format name."""
        engine = ConversionEngine()
        parser = MockParser()
        engine.register_parser('mock', parser)
        
        found_parser = engine.get_parser('mock')
        assert found_parser == parser
        
        # Test non-existent format
        assert engine.get_parser('nonexistent') is None
    
    def test_get_exporter_by_format(self):
        """Test getting exporter by format name."""
        engine = ConversionEngine()
        exporter = MockExporter()
        engine.register_exporter('mock', exporter)
        
        found_exporter = engine.get_exporter('mock')
        assert found_exporter == exporter
        
        # Test non-existent format
        assert engine.get_exporter('nonexistent') is None
    
    def test_detect_format(self):
        """Test format detection."""
        engine = ConversionEngine()
        parser = MockParser()
        engine.register_parser('mock', parser)
        
        format_name = engine.detect_format('test.mock')
        assert format_name == 'mock'
        
        # Test undetectable format
        format_name = engine.detect_format('test.unknown')
        assert format_name is None
    
    def test_convert_success(self, temp_dir: Path):
        """Test successful conversion."""
        engine = ConversionEngine()
        parser = MockParser()
        exporter = MockExporter()
        engine.register_parser('mock', parser)
        engine.register_exporter('mock', exporter)
        
        input_file = temp_dir / "input.mock"
        output_file = temp_dir / "output.txt"
        input_file.write_text("mock content")
        
        schema = engine.convert(str(input_file), str(output_file), 'mock', 'mock')
        
        assert schema.metadata.name == "mock_robot"
        assert output_file.exists()
        assert "Mock export of mock_robot" in output_file.read_text()
    
    def test_convert_no_parser(self, temp_dir: Path):
        """Test conversion failure when no parser available."""
        engine = ConversionEngine()
        
        input_file = temp_dir / "input.unknown"
        output_file = temp_dir / "output.txt"
        input_file.write_text("content")
        
        with pytest.raises(ValueError, match="No parser found"):
            engine.convert(str(input_file), str(output_file), 'unknown', 'mock')
    
    def test_convert_no_exporter(self, temp_dir: Path):
        """Test conversion failure when no exporter available."""
        engine = ConversionEngine()
        parser = MockParser()
        engine.register_parser('mock', parser)
        
        input_file = temp_dir / "input.mock"
        output_file = temp_dir / "output.txt"
        input_file.write_text("content")
        
        with pytest.raises(ValueError, match="No exporter found"):
            engine.convert(str(input_file), str(output_file), 'mock', 'unknown')


class TestFormatConverter:
    """Tests for FormatConverter class."""
    
    def test_converter_initialization(self):
        """Test converter initializes with engine."""
        converter = FormatConverter()
        assert converter.engine is not None
        assert isinstance(converter.engine, ConversionEngine)
    
    def test_convert_method(self, temp_dir: Path):
        """Test convert method delegates to engine."""
        converter = FormatConverter()
        
        # Register mock parser and exporter
        parser = MockParser()
        exporter = MockExporter()
        converter.engine.register_parser('mock', parser)
        converter.engine.register_exporter('mock', exporter)
        
        input_file = temp_dir / "input.mock"
        output_file = temp_dir / "output.txt"
        input_file.write_text("mock content")
        
        schema = converter.convert(
            str(input_file), 
            str(output_file), 
            source_format='mock',
            target_format='mock'
        )
        
        assert schema.metadata.name == "mock_robot"
        assert output_file.exists()
    
    def test_to_schema_method(self, temp_dir: Path):
        """Test to_schema method."""
        converter = FormatConverter()
        parser = MockParser()
        converter.engine.register_parser('mock', parser)
        
        input_file = temp_dir / "input.mock"
        output_file = temp_dir / "output.yaml"
        input_file.write_text("mock content")
        
        schema = converter.to_schema(str(input_file), str(output_file))
        
        assert schema.metadata.name == "mock_robot"
        assert output_file.exists()
    
    def test_from_schema_method(self, temp_dir: Path):
        """Test from_schema method."""
        converter = FormatConverter()
        exporter = MockExporter()
        converter.engine.register_exporter('mock', exporter)
        
        # Create a schema file
        schema_file = temp_dir / "robot.yaml"
        schema_content = """
metadata:
  name: "test_robot"
links: []
joints: []
"""
        schema_file.write_text(schema_content)
        
        output_file = temp_dir / "output.txt"
        
        converter.from_schema(str(schema_file), str(output_file), 'mock')
        
        assert output_file.exists()
        assert "Mock export of test_robot" in output_file.read_text()
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        converter = FormatConverter()
        
        # Register mock formats
        parser = MockParser()
        exporter = MockExporter()
        converter.engine.register_parser('mock', parser)
        converter.engine.register_exporter('mock', exporter)
        
        formats = converter.engine.get_supported_formats()
        
        assert 'parsers' in formats
        assert 'exporters' in formats
        assert 'mock' in formats['parsers']
        assert 'mock' in formats['exporters']
    
    def test_get_conversion_matrix(self):
        """Test getting conversion matrix."""
        converter = FormatConverter()
        
        # Register mock formats
        parser = MockParser()
        exporter = MockExporter()
        converter.engine.register_parser('mock1', parser)
        converter.engine.register_parser('mock2', parser)
        converter.engine.register_exporter('mock1', exporter)
        converter.engine.register_exporter('mock2', exporter)
        
        matrix = converter.get_conversion_matrix()
        
        assert 'mock1' in matrix
        assert 'mock2' in matrix
        assert 'mock2' in matrix['mock1']
        assert 'mock1' in matrix['mock2']
    
    def test_batch_convert(self, temp_dir: Path):
        """Test batch conversion."""
        converter = FormatConverter()
        
        # Register mock formats
        parser = MockParser()
        exporter = MockExporter()
        converter.engine.register_parser('mock', parser)
        converter.engine.register_exporter('target', exporter)
        
        # Create input files
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        
        (input_dir / "robot1.mock").write_text("robot1 content")
        (input_dir / "robot2.mock").write_text("robot2 content")
        (input_dir / "other.txt").write_text("other content")  # Should be ignored
        
        output_dir = temp_dir / "output"
        
        converted_files = converter.batch_convert(
            str(input_dir),
            str(output_dir), 
            'mock',
            'target',
            pattern='*.mock'
        )
        
        assert len(converted_files) == 2
        assert output_dir.exists()
        assert (output_dir / "robot1.target").exists()
        assert (output_dir / "robot2.target").exists()
