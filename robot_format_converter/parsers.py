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
Format parsers for converting robot description formats to common schema.
"""

import json
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union, Dict, List, Optional
import logging

from .core import BaseParser
from .schema import (
    CommonSchema, Metadata, Link, Joint, Actuator, Sensor, Contact,
    JointType, GeometryType, ActuatorType, Vector3, Quaternion, Pose,
    Inertia, Geometry, Visual, Collision, Material, JointLimits, JointDynamics,
    ContactSurface
)
from .utils import sanitize_name

logger = logging.getLogger(__name__)


class URDFParser(BaseParser):
    """Parser for URDF (Unified Robot Description Format) files."""
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid URDF file."""
        try:
            tree = ET.parse(file_path)
            return tree.getroot().tag == 'robot'
        except Exception:
            return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse URDF file to common schema."""
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        # Extract metadata
        robot_name = root.get('name', 'robot')
        metadata = Metadata(
            name=sanitize_name(robot_name),
            source_format='urdf',
            description=f'Converted from URDF: {Path(input_path).name}'
        )
        
        # Parse links
        links = []
        for link_elem in root.findall('link'):
            link = self._parse_link(link_elem)
            if link:
                links.append(link)
        
        # Parse joints
        joints = []
        for joint_elem in root.findall('joint'):
            joint = self._parse_joint(joint_elem)
            if joint:
                joints.append(joint)
        
        return CommonSchema(
            metadata=metadata,
            links=links,
            joints=joints
        )
    
    def _parse_link(self, elem: ET.Element) -> Optional[Link]:
        """Parse URDF link element."""
        name = elem.get('name')
        if not name:
            return None
        
        link = Link(name=sanitize_name(name))
        
        # Parse inertial properties
        inertial = elem.find('inertial')
        if inertial is not None:
            mass_elem = inertial.find('mass')
            if mass_elem is not None:
                link.mass = float(mass_elem.get('value', 0.0))
            
            origin = inertial.find('origin')
            if origin is not None:
                xyz = self._parse_xyz(origin.get('xyz', '0 0 0'))
                link.center_of_mass = Vector3(xyz[0], xyz[1], xyz[2])
            
            inertia_elem = inertial.find('inertia')
            if inertia_elem is not None:
                link.inertia = Inertia(
                    ixx=float(inertia_elem.get('ixx', 0.0)),
                    iyy=float(inertia_elem.get('iyy', 0.0)),
                    izz=float(inertia_elem.get('izz', 0.0)),
                    ixy=float(inertia_elem.get('ixy', 0.0)),
                    ixz=float(inertia_elem.get('ixz', 0.0)),
                    iyz=float(inertia_elem.get('iyz', 0.0))
                )
        
        # Parse visual elements
        for visual_elem in elem.findall('visual'):
            visual = self._parse_visual(visual_elem)
            if visual:
                link.visuals.append(visual)
        
        # Parse collision elements
        for collision_elem in elem.findall('collision'):
            collision = self._parse_collision(collision_elem)
            if collision:
                link.collisions.append(collision)
        
        return link
    
    def _parse_joint(self, elem: ET.Element) -> Optional[Joint]:
        """Parse URDF joint element."""
        name = elem.get('name')
        joint_type = elem.get('type')
        if not name or not joint_type:
            return None
        
        # Map URDF joint types to common schema
        type_mapping = {
            'revolute': JointType.REVOLUTE,
            'continuous': JointType.CONTINUOUS,
            'prismatic': JointType.PRISMATIC,
            'fixed': JointType.FIXED,
            'floating': JointType.FLOATING,
            'planar': JointType.PLANAR
        }
        
        joint_type_enum = type_mapping.get(joint_type, JointType.FIXED)
        
        # Get parent and child links
        parent_elem = elem.find('parent')
        child_elem = elem.find('child')
        if parent_elem is None or child_elem is None:
            return None
        
        parent_link = parent_elem.get('link', '')
        child_link = child_elem.get('link', '')
        
        joint = Joint(
            name=sanitize_name(name),
            type=joint_type_enum,
            parent_link=sanitize_name(parent_link),
            child_link=sanitize_name(child_link)
        )
        
        # Parse origin
        origin = elem.find('origin')
        if origin is not None:
            xyz = self._parse_xyz(origin.get('xyz', '0 0 0'))
            rpy = self._parse_rpy(origin.get('rpy', '0 0 0'))
            joint.pose = Pose.from_xyzrpy(xyz, rpy)
        
        # Parse axis
        axis = elem.find('axis')
        if axis is not None:
            axis_xyz = self._parse_xyz(axis.get('xyz', '0 0 1'))
            joint.axis = Vector3(axis_xyz[0], axis_xyz[1], axis_xyz[2])
        
        # Parse limits
        limit = elem.find('limit')
        if limit is not None:
            joint.limits = JointLimits(
                lower=self._parse_float(limit.get('lower')),
                upper=self._parse_float(limit.get('upper')),
                effort=self._parse_float(limit.get('effort')),
                velocity=self._parse_float(limit.get('velocity'))
            )
        
        # Parse dynamics
        dynamics = elem.find('dynamics')
        if dynamics is not None:
            joint.dynamics = JointDynamics(
                damping=float(dynamics.get('damping', 0.0)),
                friction=float(dynamics.get('friction', 0.0))
            )
        
        return joint
    
    def _parse_visual(self, elem: ET.Element) -> Optional[Visual]:
        """Parse URDF visual element."""
        visual = Visual(name=elem.get('name'))
        
        # Parse origin
        origin = elem.find('origin')
        if origin is not None:
            xyz = self._parse_xyz(origin.get('xyz', '0 0 0'))
            rpy = self._parse_rpy(origin.get('rpy', '0 0 0'))
            visual.pose = Pose.from_xyzrpy(xyz, rpy)
        
        # Parse geometry
        geom_elem = elem.find('geometry')
        if geom_elem is not None:
            visual.geometry = self._parse_geometry(geom_elem)
        
        # Parse material
        mat_elem = elem.find('material')
        if mat_elem is not None:
            visual.material = self._parse_material(mat_elem)
        
        return visual
    
    def _parse_collision(self, elem: ET.Element) -> Optional[Collision]:
        """Parse URDF collision element."""
        collision = Collision(name=elem.get('name'))
        
        # Parse origin
        origin = elem.find('origin')
        if origin is not None:
            xyz = self._parse_xyz(origin.get('xyz', '0 0 0'))
            rpy = self._parse_rpy(origin.get('rpy', '0 0 0'))
            collision.pose = Pose.from_xyzrpy(xyz, rpy)
        
        # Parse geometry
        geom_elem = elem.find('geometry')
        if geom_elem is not None:
            collision.geometry = self._parse_geometry(geom_elem)
        
        return collision
    
    def _parse_geometry(self, elem: ET.Element) -> Optional[Geometry]:
        """Parse URDF geometry element."""
        # Check for different geometry types
        box = elem.find('box')
        if box is not None:
            size_str = box.get('size', '1 1 1')
            size = self._parse_xyz(size_str)
            return Geometry(
                type=GeometryType.BOX,
                size=Vector3(size[0], size[1], size[2])
            )
        
        cylinder = elem.find('cylinder')
        if cylinder is not None:
            return Geometry(
                type=GeometryType.CYLINDER,
                radius=float(cylinder.get('radius', 1.0)),
                length=float(cylinder.get('length', 1.0))
            )
        
        sphere = elem.find('sphere')
        if sphere is not None:
            return Geometry(
                type=GeometryType.SPHERE,
                radius=float(sphere.get('radius', 1.0))
            )
        
        mesh = elem.find('mesh')
        if mesh is not None:
            scale_str = mesh.get('scale')
            scale = None
            if scale_str:
                scale_vals = self._parse_xyz(scale_str)
                scale = Vector3(scale_vals[0], scale_vals[1], scale_vals[2])
            
            return Geometry(
                type=GeometryType.MESH,
                filename=mesh.get('filename'),
                scale=scale
            )
        
        return None
    
    def _parse_material(self, elem: ET.Element) -> Optional[Material]:
        """Parse URDF material element."""
        material = Material(name=elem.get('name'))
        
        color = elem.find('color')
        if color is not None:
            rgba_str = color.get('rgba', '0.5 0.5 0.5 1.0')
            rgba = [float(x) for x in rgba_str.split()]
            material.color = rgba
        
        texture = elem.find('texture')
        if texture is not None:
            material.texture = texture.get('filename')
        
        return material
    
    def _parse_xyz(self, xyz_str: str) -> List[float]:
        """Parse XYZ coordinate string."""
        return [float(x) for x in xyz_str.split()]
    
    def _parse_rpy(self, rpy_str: str) -> List[float]:
        """Parse RPY angle string."""
        return [float(x) for x in rpy_str.split()]
    
    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse optional float value."""
        return float(value) if value is not None else None


class SDFParser(BaseParser):
    """Parser for SDF (Simulation Description Format) files."""
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid SDF file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag in ['sdf', 'world']
        except Exception:
            return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse SDF file to common schema."""
        # Simplified SDF parser - full implementation would be much more complex
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        metadata = Metadata(
            name='sdf_robot',
            source_format='sdf',
            description=f'Converted from SDF: {Path(input_path).name}'
        )
        
        # SDF parsing would need to handle models, worlds, etc.
        # This is a placeholder implementation
        return CommonSchema(metadata=metadata)


class MJCFParser(BaseParser):
    """Parser for MJCF (MuJoCo Model Format) files."""
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid MJCF file."""
        try:
            tree = ET.parse(file_path)
            return tree.getroot().tag == 'mujoco'
        except Exception:
            return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse MJCF file to common schema."""
        # Simplified MJCF parser - full implementation would be complex
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        model_name = root.get('model', 'mjcf_robot')
        metadata = Metadata(
            name=sanitize_name(model_name),
            source_format='mjcf',
            description=f'Converted from MJCF: {Path(input_path).name}'
        )
        
        # MJCF parsing would need to handle worldbody, bodies, joints, etc.
        # This is a placeholder implementation
        return CommonSchema(metadata=metadata)


class SchemaParser(BaseParser):
    """Parser for common schema YAML/JSON files."""
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid schema file."""
        try:
            path = Path(file_path)
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                return isinstance(data, dict) and 'metadata' in data
            elif path.suffix.lower() == '.json':
                with open(path, 'r') as f:
                    data = json.load(f)
                return isinstance(data, dict) and 'metadata' in data
        except Exception:
            pass
        return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse schema file to common schema."""
        path = Path(input_path)
        
        # Load data
        if path.suffix.lower() in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        else:  # JSON
            with open(path, 'r') as f:
                data = json.load(f)
        
        # Convert dictionary to CommonSchema
        return self._dict_to_schema(data)
    
    def _dict_to_schema(self, data: Dict) -> CommonSchema:
        """Convert dictionary data to CommonSchema object."""
        # This is a simplified conversion
        # Full implementation would handle all schema fields properly
        
        metadata_data = data.get('metadata', {})
        metadata = Metadata(
            name=metadata_data.get('name', 'robot'),
            version=metadata_data.get('version', '1.0'),
            author=metadata_data.get('author'),
            description=metadata_data.get('description'),
            source_format='schema'
        )
        
        # Convert links, joints, etc. from dictionaries
        # This would require comprehensive conversion logic
        links = []
        joints = []
        actuators = []
        sensors = []
        contacts = []
        
        return CommonSchema(
            metadata=metadata,
            links=links,
            joints=joints,
            actuators=actuators,
            sensors=sensors,
            contacts=contacts
        )


class USDParser(BaseParser):
    """Parser for USD (Universal Scene Description) files."""
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid USD file."""
        try:
            # This would require pxr module
            return str(file_path).endswith(('.usd', '.usda'))
        except Exception:
            return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse USD file to common schema."""
        try:
            # This would require proper USD integration
            # import pxr
            # stage = pxr.Usd.Stage.Open(str(input_path))
            
            metadata = Metadata(
                name='usd_robot',
                source_format='usd',
                description=f'Converted from USD: {Path(input_path).name}'
            )
            
            return CommonSchema(metadata=metadata)
            
        except ImportError:
            raise RuntimeError("USD support requires pxr module: pip install usd-core")
