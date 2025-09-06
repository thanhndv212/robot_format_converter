#!/usr/bin/env python3
# Copyright [2021-2025] Thanh Nguyen

"""
CLI Usage Examples

This script demonstrates various ways to use the robot_format_converter
command-line interface with the UR robot examples.
"""

import subprocess
import sys
from pathlib import Path
import time


def run_command(cmd, description):
    """Run a command and capture output."""
    print(f"\n{description}")
    print("-" * len(description))
    print(f"Command: {' '.join(cmd)}")
    print("Output:")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent.parent,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        print(f"Exit code: {result.returncode} (Time: {elapsed:.2f}s)")
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        print("Command timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Demonstrate CLI usage examples."""
    
    print("Robot Format Converter - CLI Usage Examples")
    print("=" * 50)
    
    # Setup paths
    examples_dir = Path(__file__).parent
    ur_description_path = examples_dir / "ur_description"
    urdf_dir = ur_description_path / "urdf"
    
    # Create output directory
    cli_output_dir = examples_dir / "cli_outputs"
    cli_output_dir.mkdir(exist_ok=True)
    
    # Files to use for examples
    ur10_urdf = urdf_dir / "ur10_robot.urdf"
    example_schema = examples_dir / "example_schema.yaml"
    
    # Python CLI command
    cli_cmd = [sys.executable, "-m", "robot_format_converter"]
    
    success_count = 0
    total_commands = 0
    
    # 1. Show help
    total_commands += 1
    if run_command(cli_cmd + ["--help"], "1. Show CLI Help"):
        success_count += 1
    
    # 2. List supported formats
    total_commands += 1
    if run_command(cli_cmd + ["list-formats"], "2. List Supported Formats"):
        success_count += 1
    
    # 3. Show file information
    if ur10_urdf.exists():
        total_commands += 1
        if run_command(cli_cmd + ["info", str(ur10_urdf)], "3. Show UR10 URDF Information"):
            success_count += 1
    
    # 4. Convert single file (URDF to Schema)
    if ur10_urdf.exists():
        output_schema = cli_output_dir / "ur10_cli_schema.yaml"
        total_commands += 1
        if run_command(
            cli_cmd + ["convert", str(ur10_urdf), str(output_schema)], 
            "4. Convert UR10 URDF to Schema"
        ):
            success_count += 1
    
    # 5. Convert single file (Schema to URDF)
    if example_schema.exists():
        output_urdf = cli_output_dir / "example_cli_robot.urdf"
        total_commands += 1
        if run_command(
            cli_cmd + ["convert", str(example_schema), str(output_urdf)], 
            "5. Convert Example Schema to URDF"
        ):
            success_count += 1
    
    # 6. Convert with explicit format specification
    if ur10_urdf.exists():
        output_schema2 = cli_output_dir / "ur10_explicit_schema.yaml"
        total_commands += 1
        if run_command(
            cli_cmd + [
                "convert", 
                "--source", "urdf", 
                "--target", "schema", 
                str(ur10_urdf), 
                str(output_schema2)
            ], 
            "6. Convert with Explicit Format Specification"
        ):
            success_count += 1
    
    # 7. Validate schema file
    if example_schema.exists():
        total_commands += 1
        if run_command(cli_cmd + ["validate", str(example_schema)], "7. Validate Example Schema"):
            success_count += 1
    
    # 8. Batch convert (if we have multiple files)
    urdf_files = list(urdf_dir.glob("*.urdf")) if urdf_dir.exists() else []
    if len(urdf_files) > 1:
        batch_output_dir = cli_output_dir / "batch_schemas"
        batch_output_dir.mkdir(exist_ok=True)
        total_commands += 1
        if run_command(
            cli_cmd + [
                "batch-convert", 
                str(urdf_dir), 
                str(batch_output_dir), 
                "urdf", 
                "schema",
                "--pattern", "*.urdf"
            ], 
            "8. Batch Convert URDF Files to Schema"
        ):
            success_count += 1
    
    # 9. Show verbose output
    if ur10_urdf.exists():
        output_verbose = cli_output_dir / "ur10_verbose_schema.yaml"
        total_commands += 1
        if run_command(
            cli_cmd + [
                "--verbose", 
                "convert", 
                str(ur10_urdf), 
                str(output_verbose)
            ], 
            "9. Convert with Verbose Output"
        ):
            success_count += 1
    
    # 10. Show conversion without validation
    if example_schema.exists():
        output_no_validation = cli_output_dir / "example_no_validation.urdf"
        total_commands += 1
        if run_command(
            cli_cmd + [
                "convert", 
                "--no-validation", 
                str(example_schema), 
                str(output_no_validation)
            ], 
            "10. Convert without Validation"
        ):
            success_count += 1
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"CLI Examples Summary")
    print(f"=" * 50)
    print(f"Total commands executed: {total_commands}")
    print(f"Successful commands: {success_count}")
    print(f"Failed commands: {total_commands - success_count}")
    print(f"Success rate: {(success_count/total_commands)*100:.1f}%")
    
    # Show generated files
    output_files = list(cli_output_dir.rglob("*"))
    output_files = [f for f in output_files if f.is_file()]
    
    if output_files:
        print(f"\nGenerated Files ({len(output_files)}):")
        print("-" * 25)
        for file_path in sorted(output_files):
            rel_path = file_path.relative_to(cli_output_dir)
            size = file_path.stat().st_size
            print(f"  {rel_path} ({size:,} bytes)")
    
    # CLI cheat sheet
    print(f"\nCLI Cheat Sheet:")
    print("-" * 20)
    print("# Basic conversion")
    print("python -m robot_format_converter convert input.urdf output.yaml")
    print("")
    print("# With format specification")
    print("python -m robot_format_converter convert --source urdf --target schema input.urdf output.yaml")
    print("")
    print("# Batch conversion")
    print("python -m robot_format_converter batch-convert input_dir/ output_dir/ urdf schema")
    print("")
    print("# File information")
    print("python -m robot_format_converter info robot.urdf")
    print("")
    print("# Validate schema")
    print("python -m robot_format_converter validate schema.yaml")
    print("")
    print("# List formats")
    print("python -m robot_format_converter list-formats")
    print("")
    print("# Verbose mode")
    print("python -m robot_format_converter --verbose convert input.urdf output.yaml")
    print("")
    print("# Skip validation")
    print("python -m robot_format_converter convert --no-validation input.yaml output.urdf")
    
    print(f"\n✓ CLI examples completed!")
    print(f"Output files saved to: {cli_output_dir}")
    
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
