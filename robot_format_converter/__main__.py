#!/usr/bin/env python3
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
Command-line interface for robot format conversion.

Usage:
    python -m format_converter convert robot.urdf robot.sdf
    python -m format_converter batch-convert input_dir/ output_dir/ urdf sdf
    python -m format_converter info robot.urdf
    python -m format_converter validate schema.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from robot_format_converter import FormatConverter, __version__
from robot_format_converter.utils import detect_format, get_format_info, format_file_size


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Robot Format Converter - Convert between robot description formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s convert robot.urdf robot.sdf
  %(prog)s convert --source urdf --target mjcf robot.urdf robot.xml  
  %(prog)s batch-convert models/ output/ urdf sdf
  %(prog)s info robot.urdf
  %(prog)s validate schema.yaml
  %(prog)s list-formats
        """
    )
    
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert single file')
    convert_parser.add_argument('input', help='Input file path')
    convert_parser.add_argument('output', help='Output file path')
    convert_parser.add_argument('--source', help='Source format (auto-detected if not specified)')
    convert_parser.add_argument('--target', help='Target format (inferred from extension if not specified)')
    convert_parser.add_argument('--no-validation', action='store_true', help='Skip validation')
    
    # Batch convert command
    batch_parser = subparsers.add_parser('batch-convert', help='Batch convert files')
    batch_parser.add_argument('input_dir', help='Input directory')
    batch_parser.add_argument('output_dir', help='Output directory')
    batch_parser.add_argument('source_format', help='Source format')
    batch_parser.add_argument('target_format', help='Target format')
    batch_parser.add_argument('--pattern', default='*', help='File pattern (default: *)')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show file information')
    info_parser.add_argument('file', help='File to analyze')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate schema file')
    validate_parser.add_argument('file', help='Schema file to validate')
    
    # List formats command
    list_parser = subparsers.add_parser('list-formats', help='List supported formats')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set up logging
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    try:
        converter = FormatConverter()
        
        if args.command == 'convert':
            return cmd_convert(converter, args)
        elif args.command == 'batch-convert':
            return cmd_batch_convert(converter, args)
        elif args.command == 'info':
            return cmd_info(args)
        elif args.command == 'validate':
            return cmd_validate(converter, args)
        elif args.command == 'list-formats':
            return cmd_list_formats(converter)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def cmd_convert(converter: FormatConverter, args) -> int:
    """Handle convert command."""
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1
    
    try:
        schema = converter.convert(
            input_path, 
            output_path,
            source_format=args.source,
            target_format=args.target,
            validation=not args.no_validation
        )
        
        print(f"Successfully converted: {input_path} -> {output_path}")
        print(f"Robot: {schema.metadata.name}")
        print(f"Links: {len(schema.links)}, Joints: {len(schema.joints)}")
        
        if schema.actuators:
            print(f"Actuators: {len(schema.actuators)}")
        if schema.sensors:
            print(f"Sensors: {len(schema.sensors)}")
        
        return 0
        
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return 1


def cmd_batch_convert(converter: FormatConverter, args) -> int:
    """Handle batch-convert command."""
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        return 1
    
    try:
        converted_files = converter.batch_convert(
            input_dir,
            output_dir,
            args.source_format,
            args.target_format,
            args.pattern
        )
        
        print(f"Batch conversion completed: {len(converted_files)} files converted")
        for file_path in converted_files:
            print(f"  -> {file_path}")
        
        return 0
        
    except Exception as e:
        print(f"Batch conversion failed: {e}", file=sys.stderr)
        return 1


def cmd_info(args) -> int:
    """Handle info command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    # Detect format
    format_name = detect_format(file_path)
    if format_name is None:
        print(f"Warning: Cannot detect format for: {file_path}")
        format_name = "unknown"
    
    # Get file info
    file_size = file_path.stat().st_size
    format_info = get_format_info(format_name)
    
    print(f"File: {file_path}")
    print(f"Format: {format_name}")
    print(f"Size: {format_file_size(file_size)}")
    
    if format_info:
        print(f"Description: {format_info.get('description', 'N/A')}")
        print(f"Type: {format_info.get('type', 'N/A')}")
        features = format_info.get('features', [])
        if features:
            print(f"Features: {', '.join(features)}")
    
    # Try to parse and get more info
    try:
        from robot_format_converter import FormatConverter
        converter = FormatConverter()
        schema = converter.engine.parsers.get(format_name)
        if schema:
            # This would require parsing the file
            print("Additional analysis available with parsing...")
    except:
        pass
    
    return 0


def cmd_validate(converter: FormatConverter, args) -> int:
    """Handle validate command."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    try:
        # Parse file to schema
        schema = converter.to_schema(str(file_path), '/tmp/temp_schema.yaml')
        
        # Validate schema
        issues = schema.validate()
        
        if not issues:
            print(f"✓ Schema validation passed: {file_path}")
            print(f"  Robot: {schema.metadata.name}")
            print(f"  Links: {len(schema.links)}")
            print(f"  Joints: {len(schema.joints)}")
            return 0
        else:
            print(f"✗ Schema validation failed: {file_path}")
            print("Issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
            
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1


def cmd_list_formats(converter: FormatConverter) -> int:
    """Handle list-formats command."""
    formats = converter.engine.get_supported_formats()
    conversion_matrix = converter.get_conversion_matrix()
    
    print("Supported Formats:")
    print("==================")
    
    all_formats = set(formats['parsers'] + formats['exporters'])
    
    for fmt in sorted(all_formats):
        info = get_format_info(fmt)
        name = info.get('name', fmt.upper())
        desc = info.get('description', '')
        
        can_parse = fmt in formats['parsers']
        can_export = fmt in formats['exporters']
        
        status = []
        if can_parse:
            status.append('read')
        if can_export:
            status.append('write')
        
        status_str = ', '.join(status)
        print(f"{fmt:8} - {name} ({status_str})")
        if desc:
            print(f"         {desc}")
    
    print(f"\nTotal formats supported: {len(all_formats)}")
    
    # Show conversion matrix
    print(f"\nConversion Matrix:")
    print(f"=================")
    print("Source -> Target formats:")
    
    for source, targets in sorted(conversion_matrix.items()):
        target_list = [t for t in sorted(targets) if t != source]
        if target_list:
            print(f"{source:8} -> {', '.join(target_list)}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
