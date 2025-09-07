#!/usr/bin/env python3
"""
Project cleanup and organization script.
"""

import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_project():
    """Clean up the robot format converter project."""
    
    project_root = Path(__file__).parent.parent
    logger.info(f"Cleaning up project at: {project_root}")
    
    # Files and directories to remove
    cleanup_targets = [
        # Python cache
        "**/__pycache__",
        "**/*.pyc", 
        "**/*.pyo",
        "**/*.pyd",
        
        # Build artifacts
        "build/",
        "dist/",
        "*.egg-info/",
        
        # IDE files
        ".vscode/",
        ".idea/",
        "*.sublime-*",
        
        # OS files
        ".DS_Store",
        "Thumbs.db",
        
        # Temporary files
        "*.tmp",
        "*.temp",
        "*.log",
        
        # Example outputs (keep organized outputs)
        "examples/*.urdf",
        "examples/*.xml", 
        "examples/*.json",
        "examples/*.txt",
    ]
    
    # Specific files to remove
    specific_files = [
        "examples/ur_description",  # Redundant with universal_robots_ur10e
        "examples/example_schema.yaml",  # Use example_schema.yaml
        "examples/basic_conversion.py",  # Superseded by enhanced_conversion_demo.py
        "examples/mjcf_conversion_example.py",  # Integrated into comprehensive examples
        "examples/mjcf_batch_conversion.py",  # Integrated into enhanced demo
        "examples/schema_conversion_example.py",  # Basic functionality covered elsewhere
    ]
    
    files_removed = 0
    dirs_removed = 0
    
    # Remove matching patterns
    for pattern in cleanup_targets:
        for path in project_root.glob(pattern):
            try:
                if path.is_file():
                    path.unlink()
                    files_removed += 1
                    logger.debug(f"Removed file: {path.relative_to(project_root)}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    dirs_removed += 1
                    logger.debug(f"Removed directory: {path.relative_to(project_root)}")
            except Exception as e:
                logger.warning(f"Failed to remove {path}: {e}")
    
    # Remove specific files
    for file_path in specific_files:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                if full_path.is_file():
                    full_path.unlink()
                    files_removed += 1
                    logger.info(f"Removed redundant file: {file_path}")
                elif full_path.is_dir():
                    shutil.rmtree(full_path)
                    dirs_removed += 1
                    logger.info(f"Removed redundant directory: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove {full_path}: {e}")
    
    logger.info(f"Cleanup completed: {files_removed} files, {dirs_removed} directories removed")


def organize_examples():
    """Organize examples into logical categories."""
    
    project_root = Path(__file__).parent.parent
    examples_dir = project_root / "examples"
    
    # Create organized structure
    categories = {
        "basic/": [
            "comprehensive_demo.py",
            "enhanced_conversion_demo.py"
        ],
        "advanced/": [
            "batch_conversion_example.py",
            "cli_usage_examples.py"
        ],
        "robot_models/": [
            "universal_robots_ur10e/",
            "ur10_conversion_example.py"
        ],
        "config/": [
            "example_schema.yaml"
        ]
    }
    
    # Create category directories
    for category in categories:
        category_dir = examples_dir / category
        category_dir.mkdir(exist_ok=True)
    
    # Move files to appropriate categories
    for category, files in categories.items():
        for file_name in files:
            src = examples_dir / file_name
            dst = examples_dir / category / file_name
            
            if src.exists() and src != dst:
                try:
                    if src.is_dir():
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.move(str(src), str(dst))
                    else:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(src), str(dst))
                    
                    logger.info(f"Moved {file_name} to {category}")
                except Exception as e:
                    logger.warning(f"Failed to move {file_name}: {e}")


def create_project_structure_doc():
    """Create documentation of the organized project structure."""
    
    project_root = Path(__file__).parent.parent
    
    structure_doc = """# Robot Format Converter - Project Structure

## Overview
This document describes the organized structure of the robot format converter project.

## Directory Structure

```
robot_format_converter/
├── docs/                           # Documentation
│   ├── mujoco_xml_schema.md        # MuJoCo MJCF schema documentation  
│   └── unified_schema_design.md    # Unified schema design proposals
├── robot_format_converter/         # Main package
│   ├── __init__.py
│   ├── core.py                     # Core classes and interfaces
│   ├── schema.py                   # Unified robot schema
│   ├── parsers.py                  # Format parsers (URDF, MJCF, etc.)
│   ├── enhanced_parsers.py         # Enhanced parsers with validation
│   ├── exporters.py               # Format exporters
│   └── utils.py                   # Utility functions
├── examples/                      # Usage examples
│   ├── basic/                     # Basic conversion examples
│   ├── advanced/                  # Advanced usage patterns
│   ├── robot_models/             # Sample robot models
│   ├── config/                   # Configuration examples
│   └── outputs/                  # Organized conversion outputs
├── tests/                        # Test suite
│   ├── test_core.py              # Core functionality tests
│   ├── test_enhanced_parsers.py  # Enhanced parser tests
│   └── conftest.py               # Test configuration
└── scripts/                      # Utility scripts
    └── cleanup.py                # Project cleanup script
```

## Key Features

### Enhanced Parsers
- **EnhancedURDFParser**: URDF parser with validation and error reporting
- **EnhancedMJCFParser**: MuJoCo MJCF parser with comprehensive feature support

### Validation and Error Handling
- Comprehensive validation of robot models
- Detailed error reporting and warnings
- Round-trip conversion validation

### Organized Examples
- **basic/**: Simple conversion examples for getting started
- **advanced/**: Batch processing and complex scenarios  
- **robot_models/**: Real robot model examples
- **config/**: Configuration and schema examples

### Documentation
- Complete MuJoCo XML schema reference
- Unified schema design proposals
- API documentation and usage guides

## Usage Patterns

### Basic Conversion
```python
from robot_format_converter.enhanced_parsers import EnhancedURDFParser
from robot_format_converter.exporters import MJCFExporter

# Parse URDF with validation
parser = EnhancedURDFParser()
schema = parser.parse("robot.urdf")

# Export to MJCF
exporter = MJCFExporter()
mjcf_content = exporter.export(schema, "robot.xml")
```

### Validation and Error Handling
```python
# Get parsing context with warnings and errors
context = schema.extensions.get('parse_context', {})
warnings = context.get('warnings', [])
errors = context.get('errors', [])

# Handle validation results
if errors:
    print("Conversion errors detected:")
    for error in errors:
        print(f"  - {error}")
```

## Maintenance

- Use `scripts/cleanup.py` to clean up build artifacts and temporary files
- Run tests with `pytest tests/` to validate functionality
- Check code quality with linting tools

## Extension Points

The converter is designed for extensibility:
- Add new format parsers by extending `BaseParser`
- Add new exporters by implementing export interfaces
- Extend the unified schema for new robot features
- Add validation rules through the enhanced parsers

## Dependencies

- **Core**: Python 3.8+, lxml, numpy
- **Testing**: pytest, unittest
- **Development**: black, flake8, mypy
"""
    
    # Save structure documentation
    structure_file = project_root / "PROJECT_STRUCTURE.md"
    with open(structure_file, 'w') as f:
        f.write(structure_doc)
    
    logger.info("Created project structure documentation: PROJECT_STRUCTURE.md")


def main():
    """Main cleanup and organization routine."""
    
    print("=== Robot Format Converter Project Cleanup ===\n")
    
    # Step 1: Clean up unnecessary files
    print("1. Cleaning up unnecessary files...")
    cleanup_project()
    
    # Step 2: Organize examples
    print("\n2. Organizing examples...")
    organize_examples()
    
    # Step 3: Create structure documentation
    print("\n3. Creating project structure documentation...")
    create_project_structure_doc()
    
    print("\n✅ Project cleanup and organization completed!")
    print("\nProject is now organized with:")
    print("  - Clean directory structure")
    print("  - Categorized examples")
    print("  - Comprehensive documentation")
    print("  - Enhanced validation and error handling")


if __name__ == "__main__":
    main()
