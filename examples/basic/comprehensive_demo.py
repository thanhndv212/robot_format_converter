#!/usr/bin/env python3
# Copyright [2021-2025] Thanh Nguyen

"""
Comprehensive Robot Format Converter Demo

This master example demonstrates all major capabilities of the robot_format_converter:
- URDF to Schema conversion (UR10 robot)
- Schema to URDF conversion (custom example)
- Bidirectional conversion validation
- Batch processing
- CLI interface usage
- Format detection and validation
- Error handling and recovery
"""

import sys
from pathlib import Path
import time
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import parsers
from robot_format_converter import FormatConverter


def print_section(title, level=1):
    """Print a formatted section header."""
    if level == 1:
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
    else:
        print(f"\n{'-'*40}")
        print(f"{title}")
        print(f"{'-'*40}")


def demonstrate_format_detection():
    """Demonstrate automatic format detection."""
    print_section("Format Detection Capabilities", 2)
    
    from robot_format_converter.utils import detect_format, get_format_info
    
    # Test files
    test_files = [
        "robot.urdf",
        "robot.sdf", 
        "robot.xml",
        "robot.yaml",
        "robot.json",
        "unknown.txt"
    ]
    
    print("Testing format detection:")
    for filename in test_files:
        detected = detect_format(filename)
        info = get_format_info(detected) if detected else {}
        print(f"  {filename:<15} -> {detected or 'Unknown'}")
        if info:
            print(f"                    Description: {info.get('description', 'N/A')}")


def demonstrate_converter_capabilities():
    """Show converter architecture and capabilities."""
    print_section("Converter Architecture", 2)
    
    converter = FormatConverter()
    
    # Show supported formats
    formats = converter.engine.get_supported_formats()
    print(f"Supported input formats:  {', '.join(formats['parsers'])}")
    print(f"Supported output formats: {', '.join(formats['exporters'])}")
    
    # Show conversion matrix
    print(f"\nConversion Matrix:")
    matrix = converter.get_conversion_matrix()
    for source, targets in sorted(matrix.items()):
        if targets:
            target_list = [t for t in sorted(targets) if t != source]
            if target_list:
                print(f"  {source:8} -> {', '.join(target_list)}")


def demonstrate_urdf_conversion():
    """Demonstrate UR10 URDF conversion."""
    print_section("UR10 URDF Conversion", 2)
    
    ur_description_path = Path(__file__).parent / "ur_description"
    ur10_urdf = ur_description_path / "urdf" / "ur10_robot.urdf"
    
    if not ur10_urdf.exists():
        print("UR10 URDF not found, skipping this demonstration")
        return False
    
    output_dir = Path(__file__).parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)
    
    converter = FormatConverter()
    
    try:
        print(f"Converting {ur10_urdf.name} to schema format...")
        
        schema_file = output_dir / "ur10_demo.yaml"
        schema = converter.to_schema(str(ur10_urdf), str(schema_file))
        
        print(f"✓ Conversion successful!")
        print(f"  Robot: {schema.metadata.name}")
        print(f"  Links: {len(schema.links)}")
        print(f"  Joints: {len(schema.joints)}")
        print(f"  Schema file: {schema_file} ({schema_file.stat().st_size:,} bytes)")
        
        # Convert back to URDF
        print(f"\nConverting schema back to URDF...")
        urdf_file = output_dir / "ur10_reconstructed.urdf"
        converter.from_schema(str(schema_file), str(urdf_file))
        
        print(f"✓ Back-conversion successful!")
        print(f"  URDF file: {urdf_file} ({urdf_file.stat().st_size:,} bytes)")
        
        return True
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False


def demonstrate_schema_conversion():
    """Demonstrate custom schema conversion."""
    print_section("Custom Schema Conversion", 2)
    
    example_schema = Path(__file__).parent / "proper_example_schema.yaml"
    
    if not example_schema.exists():
        print("Example schema not found, skipping this demonstration")
        return False
    
    output_dir = Path(__file__).parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)
    
    converter = FormatConverter()
    
    try:
        print(f"Converting {example_schema.name} to URDF format...")
        
        urdf_file = output_dir / "example_robot.urdf"
        converter.from_schema(str(example_schema), str(urdf_file))
        
        print(f"✓ Conversion successful!")
        print(f"  URDF file: {urdf_file} ({urdf_file.stat().st_size:,} bytes)")
        
        # Convert back to schema
        print(f"\nConverting URDF back to schema...")
        schema_file = output_dir / "example_roundtrip.yaml"
        schema = converter.to_schema(str(urdf_file), str(schema_file))
        
        print(f"✓ Round-trip conversion successful!")
        print(f"  Schema file: {schema_file} ({schema_file.stat().st_size:,} bytes)")
        print(f"  Robot: {schema.metadata.name}")
        print(f"  Links: {len(schema.links)}")
        print(f"  Joints: {len(schema.joints)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False


def demonstrate_cli_interface():
    """Demonstrate CLI interface usage."""
    print_section("Command-Line Interface Demo", 2)
    
    # Test basic CLI commands
    cli_cmd = [sys.executable, "-m", "robot_format_converter"]
    
    commands_to_test = [
        (cli_cmd + ["--version"], "Version check"),
        (cli_cmd + ["list-formats"], "List supported formats"),
        (cli_cmd + ["--help"], "Help information")
    ]
    
    for cmd, description in commands_to_test:
        print(f"\nTesting: {description}")
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10,
                cwd=Path(__file__).parent.parent
            )
            
            if result.returncode == 0:
                print(f"✓ Success - Output preview:")
                # Show first few lines of output
                lines = result.stdout.split('\n')[:5]
                for line in lines:
                    if line.strip():
                        print(f"    {line}")
                if len(result.stdout.split('\n')) > 5:
                    print("    ...")
            else:
                print(f"✗ Failed with exit code {result.returncode}")
                if result.stderr:
                    print(f"    Error: {result.stderr}")
                    
        except Exception as e:
            print(f"✗ Command failed: {e}")


def demonstrate_mjcf_conversion():
    """Demonstrate MJCF (MuJoCo) conversion."""
    print_section("MJCF (MuJoCo) Conversion", 2)
    
    mjcf_file = Path(__file__).parent / "universal_robots_ur10e" / "ur10e.xml"
    
    if not mjcf_file.exists():
        print("MJCF file not found, skipping this demonstration")
        return False
    
    output_dir = Path(__file__).parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)
    
    converter = FormatConverter()
    
    try:
        print(f"Converting {mjcf_file.name} to schema format...")
        
        schema_file = output_dir / "ur10e_mjcf_demo.yaml"
        schema = converter.to_schema(str(mjcf_file), str(schema_file))
        
        print(f"✓ Conversion successful!")
        print(f"  Robot: {schema.metadata.name}")
        print(f"  Links: {len(schema.links)}")
        print(f"  Joints: {len(schema.joints)}")
        print(f"  Actuators: {len(schema.actuators)}")
        print(f"  Schema file: {schema_file} ({schema_file.stat().st_size:,} bytes)")
        
        # Convert to URDF
        print(f"\nConverting schema to URDF...")
        urdf_file = output_dir / "ur10e_from_mjcf.urdf"
        converter.from_schema(str(schema_file), str(urdf_file))
        
        print(f"✓ URDF conversion successful!")
        print(f"  URDF file: {urdf_file} ({urdf_file.stat().st_size:,} bytes)")
        
        return True
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False


def demonstrate_error_handling():
    """Demonstrate error handling and validation."""
    print_section("Error Handling & Validation", 2)
    
    converter = FormatConverter()
    output_dir = Path(__file__).parent / "demo_outputs"
    output_dir.mkdir(exist_ok=True)
    
    # Test cases for error handling
    error_tests = [
        ("Non-existent file", "nonexistent_file.urdf", "output.yaml"),
        ("Invalid file extension", "test.xyz", "output.yaml"),
        ("Empty file", "empty.urdf", "output.yaml")
    ]
    
    # Create empty test file
    empty_file = output_dir / "empty.urdf"
    empty_file.write_text("")
    
    for test_name, input_file, output_file in error_tests:
        print(f"\nTesting: {test_name}")
        try:
            if input_file == "empty.urdf":
                input_path = str(empty_file)
            else:
                input_path = str(output_dir / input_file)
                
            output_path = str(output_dir / output_file)
            
            schema = converter.convert(input_path, output_path)
            print(f"  ✓ Unexpectedly succeeded")
            
        except Exception as e:
            print(f"  ✓ Correctly caught error: {type(e).__name__}")
            print(f"    Message: {str(e)}")


def show_performance_stats():
    """Show performance statistics."""
    print_section("Performance Statistics", 2)
    
    output_dir = Path(__file__).parent / "demo_outputs"
    if not output_dir.exists():
        print("No output files to analyze")
        return
    
    files = list(output_dir.glob("*"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        print("No output files found")
        return
    
    print(f"Generated files: {len(files)}")
    
    total_size = 0
    file_types = {}
    
    for file_path in files:
        size = file_path.stat().st_size
        total_size += size
        ext = file_path.suffix.lower()
        file_types[ext] = file_types.get(ext, 0) + 1
        
        print(f"  {file_path.name:<30} {size:>8,} bytes")
    
    print(f"\nSummary:")
    print(f"  Total files: {len(files)}")
    print(f"  Total size:  {total_size:,} bytes")
    print(f"  File types:  {dict(file_types)}")


def main():
    """Run comprehensive demonstration."""
    
    print("Robot Format Converter - Comprehensive Demo")
    print("This demo showcases all major capabilities of the robot_format_converter")
    
    start_time = time.time()
    
    # Run all demonstrations
    demos = [
        ("Format Detection", demonstrate_format_detection),
        ("Converter Capabilities", demonstrate_converter_capabilities),
        ("UR10 URDF Conversion", demonstrate_urdf_conversion),
        ("Custom Schema Conversion", demonstrate_schema_conversion),
        ("MJCF Conversion", demonstrate_mjcf_conversion),
        ("CLI Interface", demonstrate_cli_interface),
        ("Error Handling", demonstrate_error_handling),
        ("Performance Stats", show_performance_stats)
    ]
    
    successful_demos = 0
    total_demos = len(demos)
    
    for demo_name, demo_func in demos:
        print_section(demo_name, 1)
        try:
            result = demo_func()
            if result is not False:
                successful_demos += 1
                print(f"\n✓ {demo_name} completed successfully")
            else:
                print(f"\n⚠ {demo_name} completed with warnings")
        except Exception as e:
            print(f"\n✗ {demo_name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    elapsed_time = time.time() - start_time
    
    print_section("Demo Summary", 1)
    print(f"Demonstrations completed: {successful_demos}/{total_demos}")
    print(f"Total execution time: {elapsed_time:.2f} seconds")
    
    output_dir = Path(__file__).parent / "demo_outputs"
    if output_dir.exists():
        print(f"Demo outputs saved to: {output_dir}")
    
    print(f"\nNext Steps:")
    print(f"- Explore the generated files in the demo_outputs directory")
    print(f"- Try the CLI commands: python -m robot_format_converter --help")
    print(f"- Run individual example scripts:")
    print(f"  * python examples/ur10_conversion_example.py")
    print(f"  * python examples/schema_conversion_example.py")
    print(f"  * python examples/batch_conversion_example.py")
    print(f"  * python examples/cli_usage_examples.py")
    
    print(f"\n🚀 Robot Format Converter Demo Complete!")
    
    return 0 if successful_demos > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
