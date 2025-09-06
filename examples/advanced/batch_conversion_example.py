#!/usr/bin/env python3
# Copyright [2021-2025] Thanh Nguyen

"""
Batch Conversion Example

This example demonstrates batch conversion capabilities:
1. Converting multiple URDF files from ur_description to schema format
2. Converting them back to URDF
3. Analyzing conversion results and showing statistics
"""

import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from robot_format_converter import FormatConverter


def analyze_urdf_files(urdf_dir):
    """Analyze URDF files in directory and return info."""
    urdf_files = list(urdf_dir.glob("*.urdf"))
    
    print(f"Found {len(urdf_files)} URDF files:")
    file_info = {}
    
    for urdf_file in urdf_files:
        size = urdf_file.stat().st_size
        file_info[urdf_file.name] = {
            'path': urdf_file,
            'size': size
        }
        print(f"  - {urdf_file.name} ({size:,} bytes)")
    
    return file_info


def main():
    """Demonstrate batch conversion capabilities."""
    
    print("Robot Format Converter - Batch Conversion Example")
    print("=" * 60)
    
    # Setup paths
    ur_description_path = Path(__file__).parent / "ur_description"
    urdf_dir = ur_description_path / "urdf"
    
    if not urdf_dir.exists():
        print(f"Error: URDF directory not found at {urdf_dir}")
        return 1
    
    # Create output directories
    output_dir = Path(__file__).parent / "batch_outputs"
    schema_dir = output_dir / "schemas"
    converted_urdf_dir = output_dir / "converted_urdfs"
    
    for dir_path in [output_dir, schema_dir, converted_urdf_dir]:
        dir_path.mkdir(exist_ok=True)
    
    print(f"Input directory: {urdf_dir}")
    print(f"Output directory: {output_dir}")
    
    # Analyze input files
    print(f"\n1. Analyzing Input URDF Files:")
    print("-" * 35)
    urdf_info = analyze_urdf_files(urdf_dir)
    
    if not urdf_info:
        print("No URDF files found for conversion.")
        return 1
    
    # Initialize converter
    converter = FormatConverter()
    
    # Track conversion statistics
    conversion_stats = {
        'successful_to_schema': 0,
        'failed_to_schema': 0,
        'successful_to_urdf': 0,
        'failed_to_urdf': 0,
        'total_files': len(urdf_info),
        'start_time': time.time()
    }
    
    conversion_results = []
    
    try:
        # 2. Batch convert URDF to Schema
        print(f"\n2. Converting URDF files to Schema format...")
        print("-" * 45)
        
        for filename, info in urdf_info.items():
            print(f"\nProcessing: {filename}")
            
            urdf_path = info['path']
            schema_filename = filename.replace('.urdf', '_schema.yaml')
            schema_path = schema_dir / schema_filename
            
            result = {
                'filename': filename,
                'original_size': info['size'],
                'schema_path': schema_path,
                'schema_size': 0,
                'converted_urdf_path': None,
                'converted_urdf_size': 0,
                'to_schema_success': False,
                'to_urdf_success': False,
                'errors': []
            }
            
            try:
                # Convert to schema
                schema = converter.to_schema(str(urdf_path), str(schema_path))
                
                result['to_schema_success'] = True
                result['schema_size'] = schema_path.stat().st_size
                conversion_stats['successful_to_schema'] += 1
                
                print(f"  ✓ Schema conversion: {result['schema_size']:,} bytes")
                print(f"    Robot: {schema.metadata.name}")
                print(f"    Links: {len(schema.links)}, Joints: {len(schema.joints)}")
                
            except Exception as e:
                result['errors'].append(f"Schema conversion: {str(e)}")
                conversion_stats['failed_to_schema'] += 1
                print(f"  ✗ Schema conversion failed: {e}")
            
            conversion_results.append(result)
        
        # 3. Convert schemas back to URDF
        print(f"\n3. Converting Schema files back to URDF...")
        print("-" * 45)
        
        for result in conversion_results:
            if not result['to_schema_success']:
                continue
                
            filename = result['filename']
            schema_path = result['schema_path']
            
            print(f"\nProcessing schema: {schema_path.name}")
            
            converted_filename = filename.replace('.urdf', '_converted.urdf')
            converted_path = converted_urdf_dir / converted_filename
            result['converted_urdf_path'] = converted_path
            
            try:
                # Convert back to URDF
                converter.from_schema(str(schema_path), str(converted_path))
                
                result['to_urdf_success'] = True
                result['converted_urdf_size'] = converted_path.stat().st_size
                conversion_stats['successful_to_urdf'] += 1
                
                print(f"  ✓ URDF conversion: {result['converted_urdf_size']:,} bytes")
                
            except Exception as e:
                result['errors'].append(f"URDF conversion: {str(e)}")
                conversion_stats['failed_to_urdf'] += 1
                print(f"  ✗ URDF conversion failed: {e}")
        
        # 4. Show conversion statistics
        elapsed_time = time.time() - conversion_stats['start_time']
        
        print(f"\n4. Batch Conversion Results:")
        print("-" * 35)
        print(f"Total files processed: {conversion_stats['total_files']}")
        print(f"Successful URDF → Schema: {conversion_stats['successful_to_schema']}")
        print(f"Failed URDF → Schema: {conversion_stats['failed_to_schema']}")
        print(f"Successful Schema → URDF: {conversion_stats['successful_to_urdf']}")
        print(f"Failed Schema → URDF: {conversion_stats['failed_to_urdf']}")
        print(f"Processing time: {elapsed_time:.2f} seconds")
        
        # 5. Show detailed file analysis
        print(f"\n5. Detailed File Analysis:")
        print("-" * 30)
        print(f"{'File':<25} {'Original':<10} {'Schema':<10} {'Converted':<12} {'Status'}")
        print("-" * 70)
        
        for result in conversion_results:
            filename = result['filename'][:23]
            original_size = f"{result['original_size']:,}"[:8]
            schema_size = f"{result['schema_size']:,}"[:8] if result['schema_size'] > 0 else "N/A"
            converted_size = f"{result['converted_urdf_size']:,}"[:10] if result['converted_urdf_size'] > 0 else "N/A"
            
            if result['to_schema_success'] and result['to_urdf_success']:
                status = "✓ Success"
            elif result['to_schema_success']:
                status = "⚠ Partial"
            else:
                status = "✗ Failed"
            
            print(f"{filename:<25} {original_size:<10} {schema_size:<10} {converted_size:<12} {status}")
        
        # 6. Show size comparisons
        total_original = sum(r['original_size'] for r in conversion_results)
        total_schema = sum(r['schema_size'] for r in conversion_results)
        total_converted = sum(r['converted_urdf_size'] for r in conversion_results)
        
        print(f"\n6. Size Summary:")
        print("-" * 20)
        print(f"Total original URDF size:  {total_original:,} bytes")
        print(f"Total schema size:         {total_schema:,} bytes")
        print(f"Total converted URDF size: {total_converted:,} bytes")
        
        if total_original > 0:
            schema_ratio = (total_schema / total_original) * 100
            converted_ratio = (total_converted / total_original) * 100
            print(f"Schema size ratio:         {schema_ratio:.1f}% of original")
            print(f"Converted size ratio:      {converted_ratio:.1f}% of original")
        
        # 7. Show errors if any
        errors_found = [r for r in conversion_results if r['errors']]
        if errors_found:
            print(f"\n7. Conversion Errors:")
            print("-" * 22)
            for result in errors_found:
                print(f"File: {result['filename']}")
                for error in result['errors']:
                    print(f"  - {error}")
        
        print(f"\n✓ Batch conversion completed!")
        print(f"Schema files: {schema_dir}")
        print(f"Converted URDF files: {converted_urdf_dir}")
        
        # Success if at least some conversions worked
        if conversion_stats['successful_to_schema'] > 0:
            return 0
        else:
            return 1
        
    except Exception as e:
        print(f"✗ Batch conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
