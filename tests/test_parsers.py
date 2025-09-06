"""
Comprehensive tests for the robot format converter.
"""

import unittest
import tempfile
from pathlib import Path

from robot_format_converter.parsers import URDFParser, MJCFParser
from robot_format_converter.schema import JointType, ActuatorType, Inertia


class TestURDFParser(unittest.TestCase):
    """Test cases for URDF parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = URDFParser()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_temp_urdf(self, content: str) -> Path:
        """Create a temporary URDF file with given content."""
        urdf_file = self.temp_path / "test_robot.urdf"
        with open(urdf_file, 'w') as f:
            f.write(content)
        return urdf_file
    
    def test_can_parse_valid_urdf(self):
        """Test parsing detection for valid URDF."""
        urdf_content = '''<?xml version="1.0"?>
        <robot name="test_robot">
            <link name="base_link"/>
        </robot>'''
        
        urdf_file = self.create_temp_urdf(urdf_content)
        self.assertTrue(self.parser.can_parse(urdf_file))
    
    def test_can_parse_invalid_xml(self):
        """Test parsing detection for invalid XML."""
        invalid_content = '''<?xml version="1.0"?>
        <robot name="test_robot">
            <link name="base_link"
        </robot>'''
        
        urdf_file = self.create_temp_urdf(invalid_content)
        self.assertFalse(self.parser.can_parse(urdf_file))
    
    def test_can_parse_non_urdf(self):
        """Test parsing detection for non-URDF XML."""
        non_urdf_content = '''<?xml version="1.0"?>
        <mujoco>
            <worldbody/>
        </mujoco>'''
        
        urdf_file = self.create_temp_urdf(non_urdf_content)
        self.assertFalse(self.parser.can_parse(urdf_file))
    
    def test_parse_basic_robot(self):
        """Test parsing a basic robot with link and joint."""
        urdf_content = '''<?xml version="1.0"?>
        <robot name="simple_robot">
            <link name="base_link">
                <inertial>
                    <mass value="1.0"/>
                    <origin xyz="0 0 0"/>
                    <inertia ixx="0.1" iyy="0.1" izz="0.1" ixy="0" ixz="0" iyz="0"/>
                </inertial>
            </link>
            
            <link name="child_link">
                <inertial>
                    <mass value="0.5"/>
                    <inertia ixx="0.05" iyy="0.05" izz="0.05" ixy="0" ixz="0" iyz="0"/>
                </inertial>
            </link>
            
            <joint name="joint1" type="revolute">
                <parent link="base_link"/>
                <child link="child_link"/>
                <origin xyz="0 0 0.1" rpy="0 0 0"/>
                <axis xyz="0 0 1"/>
                <limit lower="-1.57" upper="1.57" effort="10" velocity="1"/>
            </joint>
        </robot>'''
        
        urdf_file = self.create_temp_urdf(urdf_content)
        schema = self.parser.parse(urdf_file)
        
        # Verify basic structure
        self.assertEqual(schema.metadata.name, "simple_robot")
        self.assertEqual(len(schema.links), 2)
        self.assertEqual(len(schema.joints), 1)
        
        # Verify link properties
        base_link = schema.get_link("base_link")
        self.assertIsNotNone(base_link)
        self.assertEqual(base_link.mass, 1.0)
        self.assertEqual(base_link.inertia.ixx, 0.1)
        
        # Verify joint properties
        joint = schema.get_joint("joint1")
        self.assertIsNotNone(joint)
        self.assertEqual(joint.type, JointType.REVOLUTE)
        self.assertEqual(joint.parent_link, "base_link")
        self.assertEqual(joint.child_link, "child_link")
        self.assertIsNotNone(joint.limits)
        self.assertEqual(joint.limits.lower, -1.57)
        self.assertEqual(joint.limits.upper, 1.57)
    
    def test_parse_with_warnings(self):
        """Test parsing with validation warnings."""
        urdf_content = '''<?xml version="1.0"?>
        <robot name="warning_robot">
            <link name="base_link">
                <inertial>
                    <mass value="-1.0"/>  <!-- Negative mass -->
                    <inertia ixx="-0.1" iyy="0.1" izz="0.1" ixy="0" ixz="0" iyz="0"/>
                </inertial>
            </link>
            
            <joint name="joint1" type="revolute">
                <parent link="base_link"/>
                <child link="nonexistent_link"/>  <!-- Missing link -->
                <limit lower="1.57" upper="-1.57"/>  <!-- Invalid limits -->
            </joint>
        </robot>'''
        
        urdf_file = self.create_temp_urdf(urdf_content)
        schema = self.parser.parse(urdf_file)
        
        # Check that warnings were generated
        context = schema.extensions.get('parse_context', {})
        warnings = context.get('warnings', [])
        errors = context.get('errors', [])
        
        self.assertTrue(len(warnings) > 0 or len(errors) > 0)
    
    def test_inertia_validation(self):
        """Test inertia tensor validation."""
        # Valid inertia
        valid_inertia = Inertia(ixx=1.0, iyy=1.0, izz=1.0)
        self.assertTrue(self.parser._validate_inertia(valid_inertia))
        
        # Invalid inertia (negative diagonal element)
        invalid_inertia = Inertia(ixx=-1.0, iyy=1.0, izz=1.0)
        self.assertFalse(self.parser._validate_inertia(invalid_inertia))
        
        # Invalid inertia (triangle inequality violation)
        invalid_inertia2 = Inertia(ixx=1.0, iyy=1.0, izz=3.0)
        self.assertFalse(self.parser._validate_inertia(invalid_inertia2))


class TestMJCFParser(unittest.TestCase):
    """Test cases for MJCF parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = MJCFParser()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_temp_mjcf(self, content: str) -> Path:
        """Create a temporary MJCF file with given content."""
        mjcf_file = self.temp_path / "test_robot.xml"
        with open(mjcf_file, 'w') as f:
            f.write(content)
        return mjcf_file
    
    def test_can_parse_valid_mjcf(self):
        """Test parsing detection for valid MJCF."""
        mjcf_content = '''<?xml version="1.0"?>
        <mujoco model="test_robot">
            <worldbody>
                <body name="base"/>
            </worldbody>
        </mujoco>'''
        
        mjcf_file = self.create_temp_mjcf(mjcf_content)
        self.assertTrue(self.parser.can_parse(mjcf_file))
    
    def test_can_parse_non_mjcf(self):
        """Test parsing detection for non-MJCF XML."""
        non_mjcf_content = '''<?xml version="1.0"?>
        <robot name="test_robot">
            <link name="base"/>
        </robot>'''
        
        mjcf_file = self.create_temp_mjcf(non_mjcf_content)
        self.assertFalse(self.parser.can_parse(mjcf_file))
    
    def test_parse_basic_mjcf(self):
        """Test parsing a basic MJCF model."""
        mjcf_content = '''<?xml version="1.0"?>
        <mujoco model="simple_robot">
            <asset>
                <material name="red" rgba="1 0 0 1"/>
            </asset>
            
            <worldbody>
                <body name="base_link" pos="0 0 0">
                    <inertial mass="1.0" pos="0 0 0" diaginertia="0.1 0.1 0.1"/>
                    <geom type="box" size="0.1 0.1 0.1" material="red"/>
                    
                    <body name="child_link" pos="0 0 0.2">
                        <joint name="joint1" type="hinge" axis="0 0 1" range="-90 90"/>
                        <inertial mass="0.5" pos="0 0 0" diaginertia="0.05 0.05 0.05"/>
                        <geom type="cylinder" size="0.05 0.1"/>
                    </body>
                </body>
            </worldbody>
            
            <actuator>
                <motor name="motor1" joint="joint1" gear="1"/>
            </actuator>
        </mujoco>'''
        
        mjcf_file = self.create_temp_mjcf(mjcf_content)
        schema = self.parser.parse(mjcf_file)
        
        # Verify basic structure
        self.assertEqual(schema.metadata.name, "simple_robot")
        self.assertEqual(len(schema.links), 2)
        self.assertEqual(len(schema.joints), 1)
        self.assertEqual(len(schema.actuators), 1)
        
        # Verify materials were parsed
        context = schema.extensions.get('parse_context', {})
        materials = context.get('materials', {})
        self.assertIn('red', materials)
        
        # Verify actuator
        actuator = schema.actuators[0]
        self.assertEqual(actuator.name, "motor1")
        self.assertEqual(actuator.joint, "joint1")
        self.assertEqual(actuator.type, ActuatorType.DC_MOTOR)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complex scenarios."""
    
    def test_urdf_to_mjcf_conversion_pipeline(self):
        """Test complete URDF to MJCF conversion pipeline."""
        # This would test the full conversion from URDF -> CommonSchema -> MJCF
        # Implementation would involve creating exporters as well
        pass
    
    def test_error_recovery(self):
        """Test parser error recovery and partial parsing."""
        # Test that parsers can recover from errors and continue parsing
        pass
    
    def test_large_model_performance(self):
        """Test performance with large robot models."""
        # Test parsing performance with models containing many links/joints
        pass


class TestValidationHelpers(unittest.TestCase):
    """Test validation helper functions."""
    
    def test_xyz_parsing(self):
        """Test XYZ coordinate parsing."""
        parser = URDFParser()
        
        # Valid cases
        self.assertEqual(parser._parse_xyz("1 2 3"), [1.0, 2.0, 3.0])
        self.assertEqual(parser._parse_xyz("0.1 -0.2 0.3"), [0.1, -0.2, 0.3])
        
        # Invalid cases
        self.assertIsNone(parser._parse_xyz("1 2"))  # Too few values
        self.assertIsNone(parser._parse_xyz("1 2 3 4"))  # Too many values
        self.assertIsNone(parser._parse_xyz("a b c"))  # Non-numeric
        self.assertIsNone(parser._parse_xyz(""))  # Empty string
    
    def test_rpy_parsing(self):
        """Test RPY angle parsing."""
        parser = URDFParser()
        
        # Valid cases
        self.assertEqual(parser._parse_rpy("0 0 0"), [0.0, 0.0, 0.0])
        self.assertEqual(parser._parse_rpy("1.57 0 -1.57"), [1.57, 0.0, -1.57])
        
        # Invalid cases
        self.assertIsNone(parser._parse_rpy("1 2"))  # Too few values
        self.assertIsNone(parser._parse_rpy("invalid"))  # Non-numeric
    
    def test_float_parsing(self):
        """Test float value parsing."""
        parser = URDFParser()
        
        # Valid cases
        self.assertEqual(parser._parse_float("1.5"), 1.5)
        self.assertEqual(parser._parse_float("-2.3"), -2.3)
        self.assertEqual(parser._parse_float("0"), 0.0)
        
        # Invalid cases
        self.assertIsNone(parser._parse_float(None))
        self.assertIsNone(parser._parse_float("invalid"))
        self.assertIsNone(parser._parse_float(""))


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
