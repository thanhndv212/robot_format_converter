#!/usr/bin/env python3
"""
Run all consolidated parser tests.
This replaces the individual test files with a comprehensive test suite.
"""

import sys
import unittest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test modules
from tests.test_consolidated_parsers import *

if __name__ == '__main__':
    # Discover and run all tests
    loader = unittest.TestLoader()
    
    # Load tests from consolidated test module
    suite = unittest.TestSuite()
    
    # Add all test cases from consolidated parsers
    suite.addTests(loader.loadTestsFromModule(sys.modules['tests.test_consolidated_parsers']))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
