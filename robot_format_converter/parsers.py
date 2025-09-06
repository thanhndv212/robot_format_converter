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

import xml.etree.ElementTree as ET
import math
import logging
import json
from pathlib import Path
from typing import Union, Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .core import BaseParser
from .schema import (
    CommonSchema, Metadata, Link, Joint, Actuator, Sensor, Contact,
    JointType, GeometryType, ActuatorType, Vector3, Quaternion, Pose,
    Inertia, Geometry, Visual, Collision, Material, JointLimits, JointDynamics,
    ContactSurface
)
from .utils import sanitize_name

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Exception raised during parsing errors."""
    pass


class ValidationError(Exception):
    """Exception raised during validation errors."""
    pass


@dataclass
class ParseContext:
    """Context information for parsing operations with enhanced error tracking."""
    file_path: Path
    base_dir: Path
    materials: Dict[str, Material]
    meshes: Dict[str, str]
    warnings: List[str]
    errors: List[str]
    
    def add_warning(self, message: str, element: Optional[str] = None):
        """Add warning message with optional element context."""
        if element:
            message = f"{element}: {message}"
        self.warnings.append(message)
        logger.warning(message)
    
    def add_error(self, message: str, element: Optional[str] = None):
        """Add error message with optional element context."""
        if element:
            message = f"{element}: {message}"
        self.errors.append(message)
        logger.error(message)


class URDFParser(BaseParser):
    """ URDF parser with enhanced validation and error handling."""
    
    def __init__(self):
        super().__init__()
        self.supported_versions = ["1.0"]
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid URDF file with enhanced validation."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Basic tag validation
            if root.tag != 'robot':
                return False
            
            # Check for required elements
            if not root.get('name'):
                logger.warning(f"URDF file {file_path} missing robot name")
            
            # Validate basic structure
            links = root.findall('link')
            if not links:
                logger.warning(f"URDF file {file_path} has no links")
                return False
            
            return True
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking URDF file {file_path}: {e}")
            return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse URDF file with comprehensive validation and error handling."""
        file_path = Path(input_path)
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ParseError(f"XML parsing error: {e}")
        
        # Initialize parse context for enhanced error tracking
        context = ParseContext(
            file_path=file_path,
            base_dir=file_path.parent,
            materials={},
            meshes={},
            warnings=[],
            errors=[]
        )
        
        # Extract metadata
        robot_name = root.get('name', 'robot')
        if not robot_name:
            context.add_error("Robot name is required")
            robot_name = 'unnamed_robot'
        
        metadata = Metadata(
            name=sanitize_name(robot_name),
            source_format='urdf',
            description=f'Converted from URDF: {file_path.name}',
            version=root.get('version', '1.0')
        )
        
        # Parse global materials first
        for material_elem in root.findall('material'):
            material = self._parse_material(material_elem, context)
            if material and material.name:
                context.materials[material.name] = material
        
        # Parse links with validation
        links = []
        for link_elem in root.findall('link'):
            try:
                link = self._parse_link(link_elem, context)
                if link:
                    links.append(link)
            except Exception as e:
                context.add_error(f"Failed to parse link: {e}", 
                                link_elem.get('name'))
        
        # Parse joints with validation
        joints = []
        link_names = {link.name for link in links}
        
        for joint_elem in root.findall('joint'):
            try:
                joint = self._parse_joint(joint_elem, context, link_names)
                if joint:
                    joints.append(joint)
            except Exception as e:
                context.add_error(f"Failed to parse joint: {e}", 
                                joint_elem.get('name'))
        
        # Enhanced validation: kinematic tree structure
        self._validate_kinematic_tree(links, joints, context)
        
        # Log parsing results
        if context.warnings:
            logger.info(f"Parsing completed with {len(context.warnings)} warnings")
        if context.errors:
            logger.warning(f"Parsing completed with {len(context.errors)} errors")
        
        schema = CommonSchema(
            metadata=metadata,
            links=links,
            joints=joints
        )
        
        # Store parsing context in extensions for debugging
        schema.extensions['parse_context'] = {
            'warnings': context.warnings,
            'errors': context.errors,
            'materials': context.materials
        }
        
        return schema
    
    def _parse_link(self, elem: ET.Element, context: ParseContext) -> Optional[Link]:
        """Parse URDF link element with enhanced validation."""
        name = elem.get('name')
        if not name:
            context.add_error("Link name is required")
            return None
        
        name = sanitize_name(name)
        link = Link(name=name)
        
        # Parse inertial properties with validation
        inertial = elem.find('inertial')
        if inertial is not None:
            try:
                self._parse_inertial(inertial, link, context)
            except Exception as e:
                context.add_warning(f"Failed to parse inertial properties: {e}", name)
        
        # Parse visual elements
        for visual_elem in elem.findall('visual'):
            try:
                visual = self._parse_visual(visual_elem, context)
                if visual:
                    link.visuals.append(visual)
            except Exception as e:
                context.add_warning(f"Failed to parse visual element: {e}", name)
        
        # Parse collision elements
        for collision_elem in elem.findall('collision'):
            try:
                collision = self._parse_collision(collision_elem, context)
                if collision:
                    link.collisions.append(collision)
            except Exception as e:
                context.add_warning(f"Failed to parse collision element: {e}", name)
        
        return link
    
    def _parse_inertial(self, elem: ET.Element, link: Link, context: ParseContext):
        """Parse inertial properties with enhanced validation."""
        # Parse mass with validation
        mass_elem = elem.find('mass')
        if mass_elem is not None:
            try:
                mass = float(mass_elem.get('value', 0.0))
                if mass < 0:
                    context.add_warning("Negative mass detected", link.name)
                link.mass = mass
            except ValueError:
                context.add_error("Invalid mass value", link.name)
        
        # Parse center of mass
        origin = elem.find('origin')
        if origin is not None:
            xyz = self._parse_xyz(origin.get('xyz', '0 0 0'))
            if xyz:
                link.center_of_mass = Vector3(xyz[0], xyz[1], xyz[2])
        
        # Parse inertia tensor with validation
        inertia_elem = elem.find('inertia')
        if inertia_elem is not None:
            try:
                inertia = Inertia(
                    ixx=float(inertia_elem.get('ixx', 0.0)),
                    iyy=float(inertia_elem.get('iyy', 0.0)),
                    izz=float(inertia_elem.get('izz', 0.0)),
                    ixy=float(inertia_elem.get('ixy', 0.0)),
                    ixz=float(inertia_elem.get('ixz', 0.0)),
                    iyz=float(inertia_elem.get('iyz', 0.0))
                )
                
                # Enhanced validation: check inertia tensor validity
                if not self._validate_inertia(inertia):
                    context.add_warning("Inertia tensor may be invalid", link.name)
                
                link.inertia = inertia
                
            except ValueError as e:
                context.add_error(f"Invalid inertia values: {e}", link.name)
    
    def _validate_inertia(self, inertia: Inertia) -> bool:
        """Enhanced validation of inertia tensor for physical plausibility."""
        # Check diagonal elements are positive
        if inertia.ixx <= 0 or inertia.iyy <= 0 or inertia.izz <= 0:
            return False
        
        # Check triangle inequality for physical validity
        if (inertia.ixx + inertia.iyy <= inertia.izz or
            inertia.iyy + inertia.izz <= inertia.ixx or
            inertia.ixx + inertia.izz <= inertia.iyy):
            return False
        
        return True
    
    def _parse_joint(self, elem: ET.Element, context: ParseContext, 
                    link_names: set) -> Optional[Joint]:
        """Parse URDF joint element with enhanced validation."""
        name = elem.get('name')
        joint_type = elem.get('type')
        
        if not name:
            context.add_error("Joint name is required")
            return None
        
        if not joint_type:
            context.add_error("Joint type is required", name)
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
        
        joint_type_enum = type_mapping.get(joint_type)
        if not joint_type_enum:
            context.add_error(f"Unsupported joint type: {joint_type}", name)
            return None
        
        # Get parent and child links with validation
        parent_elem = elem.find('parent')
        child_elem = elem.find('child')
        
        if parent_elem is None or child_elem is None:
            context.add_error("Joint must have parent and child links", name)
            return None
        
        parent_link = sanitize_name(parent_elem.get('link', ''))
        child_link = sanitize_name(child_elem.get('link', ''))
        
        # Enhanced validation: check link references
        if parent_link not in link_names and parent_link != 'world':
            context.add_error(f"Parent link '{parent_link}' not found", name)
        if child_link not in link_names:
            context.add_error(f"Child link '{child_link}' not found", name)
        
        joint = Joint(
            name=sanitize_name(name),
            type=joint_type_enum,
            parent_link=parent_link,
            child_link=child_link
        )
        
        # Parse origin with validation
        origin = elem.find('origin')
        if origin is not None:
            xyz = self._parse_xyz(origin.get('xyz', '0 0 0'))
            rpy = self._parse_rpy(origin.get('rpy', '0 0 0'))
            if xyz and rpy:
                joint.pose = Pose.from_xyzrpy(xyz, rpy)
        
        # Parse axis with normalization
        axis = elem.find('axis')
        if axis is not None:
            axis_xyz = self._parse_xyz(axis.get('xyz', '0 0 1'))
            if axis_xyz:
                # Normalize axis vector
                axis_vec = Vector3(axis_xyz[0], axis_xyz[1], axis_xyz[2])
                magnitude = math.sqrt(axis_vec.x**2 + axis_vec.y**2 + axis_vec.z**2)
                if magnitude > 1e-6:
                    joint.axis = Vector3(
                        axis_vec.x / magnitude,
                        axis_vec.y / magnitude, 
                        axis_vec.z / magnitude
                    )
                else:
                    context.add_warning("Zero-magnitude joint axis", name)
        
        # Parse limits with validation
        limit = elem.find('limit')
        if limit is not None:
            try:
                lower = self._parse_float(limit.get('lower'))
                upper = self._parse_float(limit.get('upper'))
                effort = self._parse_float(limit.get('effort'))
                velocity = self._parse_float(limit.get('velocity'))
                
                # Enhanced validation: check limit consistency
                if lower is not None and upper is not None and lower > upper:
                    context.add_warning("Lower limit greater than upper limit", name)
                
                joint.limits = JointLimits(
                    lower=lower,
                    upper=upper,
                    effort=effort,
                    velocity=velocity
                )
            except ValueError as e:
                context.add_error(f"Invalid limit values: {e}", name)
        
        # Parse dynamics
        dynamics = elem.find('dynamics')
        if dynamics is not None:
            try:
                joint.dynamics = JointDynamics(
                    damping=float(dynamics.get('damping', 0.0)),
                    friction=float(dynamics.get('friction', 0.0))
                )
            except ValueError as e:
                context.add_error(f"Invalid dynamics values: {e}", name)
        
        return joint
    
    def _validate_kinematic_tree(self, links: List[Link], joints: List[Joint], 
                                context: ParseContext):
        """Enhanced kinematic tree validation."""
        link_names = {link.name for link in links}
        
        # Check for circular dependencies
        parent_child_map = {joint.child_link: joint.parent_link for joint in joints}
        
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            if node in parent_child_map:
                neighbor = parent_child_map[node]
                if neighbor != 'world':
                    if neighbor not in visited:
                        if has_cycle(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for link_name in link_names:
            if link_name not in visited:
                if has_cycle(link_name, visited, set()):
                    context.add_error("Circular dependency detected in kinematic tree")
                    break
        
        # Check for orphaned links
        connected_links = {'world'}
        for joint in joints:
            connected_links.add(joint.parent_link)
            connected_links.add(joint.child_link)
        
        orphaned = link_names - connected_links
        if orphaned:
            context.add_warning(f"Orphaned links detected: {orphaned}")
    
    def _parse_material(self, elem: ET.Element, context: ParseContext) -> Optional[Material]:
        """Parse URDF material element with validation."""
        name = elem.get('name')
        if not name:
            context.add_warning("Material missing name attribute")
            return None
        
        material = Material(name=sanitize_name(name))
        
        # Parse color with validation
        color_elem = elem.find('color')
        if color_elem is not None:
            rgba_str = color_elem.get('rgba')
            if rgba_str:
                try:
                    rgba_values = [float(x) for x in rgba_str.split()]
                    if len(rgba_values) == 4:
                        material.color = rgba_values
                    else:
                        context.add_warning(f"Invalid RGBA format for material {name}")
                except ValueError:
                    context.add_warning(f"Invalid RGBA values for material {name}")
        
        # Parse texture
        texture_elem = elem.find('texture')
        if texture_elem is not None:
            filename = texture_elem.get('filename')
            if filename:
                material.texture = filename
        
        return material
    
    def _parse_visual(self, elem: ET.Element, context: ParseContext) -> Optional[Visual]:
        """Parse URDF visual element with validation."""
        # Parse geometry
        geom_elem = elem.find('geometry')
        if geom_elem is None:
            context.add_warning("Visual element missing geometry")
            return None
        
        geometry = self._parse_geometry(geom_elem, context)
        if not geometry:
            return None
        
        # Parse material reference
        material = None
        material_elem = elem.find('material')
        if material_elem is not None:
            material_name = material_elem.get('name')
            if material_name and material_name in context.materials:
                material = context.materials[material_name]
            else:
                # Parse inline material
                material = self._parse_material(material_elem, context)
        
        # Parse origin
        pose = None
        origin_elem = elem.find('origin')
        if origin_elem is not None:
            xyz = self._parse_xyz(origin_elem.get('xyz', '0 0 0'))
            rpy = self._parse_rpy(origin_elem.get('rpy', '0 0 0'))
            if xyz and rpy:
                pose = Pose.from_xyzrpy(xyz, rpy)
        
        return Visual(
            name=elem.get('name'),
            geometry=geometry, 
            material=material, 
            pose=pose
        )
    
    def _parse_collision(self, elem: ET.Element, context: ParseContext) -> Optional[Collision]:
        """Parse URDF collision element with validation."""
        # Parse geometry
        geom_elem = elem.find('geometry')
        if geom_elem is None:
            context.add_warning("Collision element missing geometry")
            return None
        
        geometry = self._parse_geometry(geom_elem, context)
        if not geometry:
            return None
        
        # Parse origin
        pose = None
        origin_elem = elem.find('origin')
        if origin_elem is not None:
            xyz = self._parse_xyz(origin_elem.get('xyz', '0 0 0'))
            rpy = self._parse_rpy(origin_elem.get('rpy', '0 0 0'))
            if xyz and rpy:
                pose = Pose.from_xyzrpy(xyz, rpy)
        
        return Collision(
            name=elem.get('name'),
            geometry=geometry, 
            pose=pose
        )
    
    def _parse_geometry(self, elem: ET.Element, context: ParseContext) -> Optional[Geometry]:
        """Parse URDF geometry element with comprehensive type support."""
        # Box geometry
        box_elem = elem.find('box')
        if box_elem is not None:
            size_str = box_elem.get('size')
            if size_str:
                try:
                    size_values = [float(x) for x in size_str.split()]
                    if len(size_values) == 3:
                        return Geometry(
                            type=GeometryType.BOX,
                            size=Vector3(size_values[0], size_values[1], size_values[2])
                        )
                except ValueError:
                    context.add_warning("Invalid box size values")
        
        # Cylinder geometry
        cylinder_elem = elem.find('cylinder')
        if cylinder_elem is not None:
            try:
                radius = float(cylinder_elem.get('radius', 0))
                length = float(cylinder_elem.get('length', 0))
                return Geometry(
                    type=GeometryType.CYLINDER,
                    radius=radius,
                    length=length
                )
            except ValueError:
                context.add_warning("Invalid cylinder parameters")
        
        # Sphere geometry
        sphere_elem = elem.find('sphere')
        if sphere_elem is not None:
            try:
                radius = float(sphere_elem.get('radius', 0))
                return Geometry(
                    type=GeometryType.SPHERE,
                    radius=radius
                )
            except ValueError:
                context.add_warning("Invalid sphere radius")
        
        # Mesh geometry
        mesh_elem = elem.find('mesh')
        if mesh_elem is not None:
            filename = mesh_elem.get('filename')
            if filename:
                # Resolve relative paths
                if not Path(filename).is_absolute():
                    full_path = context.base_dir / filename
                    if full_path.exists():
                        filename = str(full_path)
                    else:
                        context.add_warning(f"Mesh file not found: {filename}")
                
                # Parse scale
                scale = None
                scale_str = mesh_elem.get('scale')
                if scale_str:
                    try:
                        scale_vals = [float(x) for x in scale_str.split()]
                        scale = Vector3(scale_vals[0], scale_vals[1], scale_vals[2])
                    except (ValueError, IndexError):
                        context.add_warning("Invalid mesh scale values")
                
                return Geometry(
                    type=GeometryType.MESH,
                    filename=filename,
                    scale=scale
                )
        
        context.add_warning("No valid geometry found")
        return None
    
    def _parse_xyz(self, xyz_str: str) -> Optional[List[float]]:
        """Parse XYZ coordinate string with validation."""
        if not xyz_str:
            return None
        
        try:
            values = [float(x.strip()) for x in xyz_str.split()]
            if len(values) != 3:
                return None
            return values
        except ValueError:
            return None
    
    def _parse_rpy(self, rpy_str: str) -> Optional[List[float]]:
        """Parse RPY angle string with validation."""
        if not rpy_str:
            return None
        
        try:
            values = [float(x.strip()) for x in rpy_str.split()]
            if len(values) != 3:
                return None
            return values
        except ValueError:
            return None
    
    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Parse float value with error handling."""
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None


class MJCFParser(BaseParser):
    """ MJCF parser with comprehensive MuJoCo support and enhanced validation."""
    
    def __init__(self):
        super().__init__()
        self.supported_versions = ["2.3", "2.4", "3.0"]
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid MJCF file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag == 'mujoco'
        except Exception:
            return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse MJCF file with enhanced validation and comprehensive support."""
        file_path = Path(input_path)
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ParseError(f"XML parsing error: {e}")
        
        # Initialize parse context
        context = ParseContext(
            file_path=file_path,
            base_dir=file_path.parent,
            materials={},
            meshes={},
            warnings=[],
            errors=[]
        )
        
        # Extract metadata
        model_name = root.get('model', 'mujoco_model')
        metadata = Metadata(
            name=sanitize_name(model_name),
            source_format='mjcf',
            description=f'Converted from MJCF: {file_path.name}',
            version=root.get('version', '2.3')
        )
        
        # Parse assets (materials, meshes)
        asset_elem = root.find('asset')
        if asset_elem is not None:
            context.materials = self._parse_materials(asset_elem, context)
            context.meshes = self._parse_meshes(asset_elem, context)
        
        # Parse world body and hierarchy
        worldbody = root.find('worldbody')
        if worldbody is None:
            context.add_error("MJCF file missing worldbody element")
            return CommonSchema(metadata=metadata)
        
        links = []
        joints = []
        
        # Create world link
        world_link = Link(name='world')
        links.append(world_link)
        
        # Parse body hierarchy
        for body_elem in worldbody.findall('body'):
            try:
                body_links, body_joints = self._parse_body_hierarchy(
                    body_elem, 'world', context
                )
                links.extend(body_links)
                joints.extend(body_joints)
            except Exception as e:
                context.add_error(f"Failed to parse body hierarchy: {e}")
        
        # Parse actuators
        actuators = []
        actuator_elem = root.find('actuator')
        if actuator_elem is not None:
            actuators = self._parse_actuators(actuator_elem, context)
        
        # Parse sensors
        sensors = []
        sensor_elem = root.find('sensor')
        if sensor_elem is not None:
            sensors = self._parse_sensors(sensor_elem, context)
        
        schema = CommonSchema(
            metadata=metadata,
            links=links,
            joints=joints,
            actuators=actuators,
            sensors=sensors
        )
        
        # Store parsing context
        schema.extensions['parse_context'] = {
            'warnings': context.warnings,
            'errors': context.errors,
            'materials': context.materials,
            'meshes': context.meshes
        }
        
        return schema
    
    def _parse_body_hierarchy(
            self, body_elem: ET.Element, parent_link: str,
            context: ParseContext) -> Tuple[List[Link], List[Joint]]:
        """Parse MJCF body hierarchy recursively with enhanced validation."""
        links = []
        joints = []
        
        # Get body properties
        body_name = body_elem.get('name')
        if not body_name:
            context.add_error("Body missing name attribute")
            return links, joints
        
        body_name = sanitize_name(body_name)
        
        # Create link
        link = Link(name=body_name)
        
        # Parse body position and orientation
        pos_str = body_elem.get('pos')
        if pos_str:
            try:
                pos_values = [float(x) for x in pos_str.split()]
                if len(pos_values) == 3:
                    link.pose = Pose(
                        position=Vector3(pos_values[0], pos_values[1], pos_values[2])
                    )
            except ValueError:
                context.add_warning(f"Invalid position for body {body_name}")
        
        # Parse quaternion orientation
        quat_str = body_elem.get('quat')
        if quat_str:
            try:
                quat_values = [float(x) for x in quat_str.split()]
                if len(quat_values) == 4:
                    # MuJoCo uses w x y z format
                    orientation = Quaternion(
                        quat_values[1], quat_values[2], quat_values[3], quat_values[0]
                    )
                    if link.pose is None:
                        link.pose = Pose(orientation=orientation)
                    else:
                        link.pose.orientation = orientation
            except ValueError:
                context.add_warning(f"Invalid quaternion for body {body_name}")
        
        # Parse inertial properties
        inertial_elem = body_elem.find('inertial')
        if inertial_elem is not None:
            self._parse_mjcf_inertial(inertial_elem, link, context)
        
        # Parse geometry for visualization and collision
        for geom_elem in body_elem.findall('geom'):
            self._parse_mjcf_geometry(geom_elem, link, context)
        
        links.append(link)
        
        # Create joint connecting to parent
        if parent_link != 'world':
            joint_elem = body_elem.find('joint')
            if joint_elem is not None:
                joint = self._parse_mjcf_joint(
                    joint_elem, parent_link, body_name, context
                )
                if joint:
                    joints.append(joint)
            else:
                # Create fixed joint for bodies without explicit joint
                joint = Joint(
                    name=f"{body_name}_fixed",
                    type=JointType.FIXED,
                    parent_link=parent_link,
                    child_link=body_name
                )
                joints.append(joint)
        
        # Recursively parse child bodies
        for child_body in body_elem.findall('body'):
            child_links, child_joints = self._parse_body_hierarchy(
                child_body, body_name, context
            )
            links.extend(child_links)
            joints.extend(child_joints)
        
        return links, joints
    
    def _parse_mjcf_inertial(self, inertial_elem: ET.Element, link: Link, 
                            context: ParseContext):
        """Parse MJCF inertial properties with validation."""
        # Parse mass
        mass_str = inertial_elem.get('mass')
        if mass_str:
            try:
                link.mass = float(mass_str)
                if link.mass < 0:
                    context.add_warning(f"Negative mass for link {link.name}")
            except ValueError:
                context.add_error(f"Invalid mass value for link {link.name}")
        
        # Parse center of mass position
        pos_str = inertial_elem.get('pos')
        if pos_str:
            try:
                pos_values = [float(x) for x in pos_str.split()]
                if len(pos_values) == 3:
                    link.center_of_mass = Vector3(
                        pos_values[0], pos_values[1], pos_values[2]
                    )
            except ValueError:
                context.add_warning(f"Invalid center of mass for link {link.name}")
        
        # Parse inertia matrix (diagonal elements)
        diaginertia_str = inertial_elem.get('diaginertia')
        if diaginertia_str:
            try:
                diag_values = [float(x) for x in diaginertia_str.split()]
                if len(diag_values) == 3:
                    # Convert MuJoCo diagonal inertia to full tensor
                    link.inertia = Inertia(
                        ixx=diag_values[0],
                        iyy=diag_values[1],
                        izz=diag_values[2],
                        ixy=0.0, ixz=0.0, iyz=0.0
                    )
            except ValueError:
                context.add_error(f"Invalid inertia values for link {link.name}")
        
        # Parse full inertia matrix if available
        fullinertia_str = inertial_elem.get('fullinertia')
        if fullinertia_str:
            try:
                inertia_values = [float(x) for x in fullinertia_str.split()]
                if len(inertia_values) == 6:
                    # MuJoCo fullinertia format: Ixx Iyy Izz Ixy Ixz Iyz
                    link.inertia = Inertia(
                        ixx=inertia_values[0],
                        iyy=inertia_values[1],
                        izz=inertia_values[2],
                        ixy=inertia_values[3],
                        ixz=inertia_values[4],
                        iyz=inertia_values[5]
                    )
            except ValueError:
                context.add_error(f"Invalid full inertia values for link {link.name}")
    
    def _parse_mjcf_geometry(self, geom_elem: ET.Element, link: Link, 
                            context: ParseContext):
        """Parse MJCF geometry element for visual and collision with enhanced support."""
        geom_type = geom_elem.get('type', 'sphere')
        size_str = geom_elem.get('size')
        
        if not size_str:
            context.add_warning(f"Geometry missing size for link {link.name}")
            return
        
        try:
            size_values = [float(x) for x in size_str.split()]
        except ValueError:
            context.add_warning(f"Invalid size values for geometry in link {link.name}")
            return
        
        # Create geometry based on type
        geometry = None
        
        if geom_type == 'sphere' and len(size_values) >= 1:
            geometry = Geometry(
                type=GeometryType.SPHERE,
                radius=size_values[0]
            )
        elif geom_type == 'box' and len(size_values) >= 3:
            # MuJoCo box size is half-extents, convert to full size
            geometry = Geometry(
                type=GeometryType.BOX,
                size=Vector3(
                    size_values[0] * 2, 
                    size_values[1] * 2, 
                    size_values[2] * 2
                )
            )
        elif geom_type == 'cylinder' and len(size_values) >= 2:
            geometry = Geometry(
                type=GeometryType.CYLINDER,
                radius=size_values[0],
                length=size_values[1] * 2  # Convert half-length to full
            )
        elif geom_type == 'capsule' and len(size_values) >= 2:
            # Use cylinder as approximation for capsule
            geometry = Geometry(
                type=GeometryType.CYLINDER,
                radius=size_values[0],
                length=size_values[1] * 2
            )
        elif geom_type == 'mesh':
            mesh_name = geom_elem.get('mesh')
            if mesh_name and mesh_name in context.meshes:
                geometry = Geometry(
                    type=GeometryType.MESH,
                    filename=context.meshes[mesh_name]
                )
        
        if geometry:
            # Parse material
            material_name = geom_elem.get('material')
            material = None
            if material_name and material_name in context.materials:
                material = context.materials[material_name]
            
            # Parse geometry pose
            pose = None
            pos_str = geom_elem.get('pos')
            quat_str = geom_elem.get('quat')
            
            if pos_str:
                try:
                    pos_values = [float(x) for x in pos_str.split()]
                    if len(pos_values) == 3:
                        position = Vector3(pos_values[0], pos_values[1], pos_values[2])
                        
                        orientation = Quaternion(0, 0, 0, 1)  # Default
                        if quat_str:
                            quat_values = [float(x) for x in quat_str.split()]
                            if len(quat_values) == 4:
                                # Convert MuJoCo w,x,y,z to x,y,z,w
                                orientation = Quaternion(
                                    quat_values[1], quat_values[2], 
                                    quat_values[3], quat_values[0]
                                )
                        
                        pose = Pose(position=position, orientation=orientation)
                        
                except ValueError:
                    context.add_warning(f"Invalid geometry position for link {link.name}")
            
            # Determine if visual or collision based on group
            group = geom_elem.get('group', '0')
            group_int = int(group) if group.isdigit() else 0
            
            # Create both visual and collision by default, following MJCF convention
            visual = Visual(
                name=f'{link.name}_visual_{len(link.visuals)}',
                geometry=geometry, 
                material=material, 
                pose=pose
            )
            collision = Collision(
                name=f'{link.name}_collision_{len(link.collisions)}',
                geometry=geometry, 
                pose=pose
            )
            
            link.visuals.append(visual)
            link.collisions.append(collision)
    
    def _parse_mjcf_joint(self, joint_elem: ET.Element, parent_link: str, 
                         child_link: str, context: ParseContext) -> Optional[Joint]:
        """Parse MJCF joint element with enhanced validation."""
        joint_name = joint_elem.get('name')
        if not joint_name:
            joint_name = f"{child_link}_joint"
        
        joint_name = sanitize_name(joint_name)
        
        # Parse joint type
        joint_type_str = joint_elem.get('type', 'hinge')
        type_mapping = {
            'hinge': JointType.REVOLUTE,
            'slide': JointType.PRISMATIC,
            'ball': JointType.SPHERICAL,
            'free': JointType.FLOATING
        }
        
        joint_type = type_mapping.get(joint_type_str, JointType.REVOLUTE)
        
        joint = Joint(
            name=joint_name,
            type=joint_type,
            parent_link=parent_link,
            child_link=child_link
        )
        
        # Parse joint axis with normalization
        axis_str = joint_elem.get('axis')
        if axis_str:
            try:
                axis_values = [float(x) for x in axis_str.split()]
                if len(axis_values) == 3:
                    # Normalize axis
                    magnitude = math.sqrt(sum(x**2 for x in axis_values))
                    if magnitude > 1e-6:
                        joint.axis = Vector3(
                            axis_values[0] / magnitude,
                            axis_values[1] / magnitude,
                            axis_values[2] / magnitude
                        )
                    else:
                        context.add_warning(f"Zero-magnitude joint axis for {joint_name}")
            except ValueError:
                context.add_warning(f"Invalid joint axis for {joint_name}")
        
        # Parse joint limits
        limited_str = joint_elem.get('limited')
        if limited_str == 'true':
            range_str = joint_elem.get('range')
            if range_str:
                try:
                    range_values = [float(x) for x in range_str.split()]
                    if len(range_values) == 2:
                        joint.limits = JointLimits(
                            lower=range_values[0],
                            upper=range_values[1]
                        )
                except ValueError:
                    context.add_warning(f"Invalid joint range for {joint_name}")
        
        # Parse joint dynamics
        damping = self._parse_float_attr(joint_elem, 'damping')
        frictionloss = self._parse_float_attr(joint_elem, 'frictionloss')
        
        if damping is not None or frictionloss is not None:
            joint.dynamics = JointDynamics(
                damping=damping or 0.0,
                friction=frictionloss or 0.0
            )
        
        return joint
    
    def _parse_materials(self, asset_elem: ET.Element, 
                        context: ParseContext) -> Dict[str, Material]:
        """Parse materials from asset section with validation."""
        materials = {}
        
        for mat_elem in asset_elem.findall('material'):
            name = mat_elem.get('name')
            if not name:
                context.add_warning("Material missing name attribute")
                continue
            
            material = Material(name=name)
            
            # Parse RGBA color
            rgba_str = mat_elem.get('rgba')
            if rgba_str:
                try:
                    rgba = [float(x) for x in rgba_str.split()]
                    if len(rgba) == 4:
                        material.color = rgba
                    else:
                        context.add_warning(f"Invalid RGBA format for material {name}")
                except ValueError:
                    context.add_warning(f"Invalid RGBA values for material {name}")
            
            # Parse specular properties
            specular_str = mat_elem.get('specular')
            if specular_str:
                try:
                    specular = [float(x) for x in specular_str.split()]
                    material.specular = specular
                except ValueError:
                    context.add_warning(f"Invalid specular values for material {name}")
            
            # Parse shininess
            shininess = self._parse_float_attr(mat_elem, 'shininess')
            if shininess is not None:
                material.shininess = shininess
            
            materials[name] = material
        
        return materials
    
    def _parse_meshes(self, asset_elem: ET.Element, 
                     context: ParseContext) -> Dict[str, str]:
        """Parse mesh assets with path resolution."""
        meshes = {}
        
        for mesh_elem in asset_elem.findall('mesh'):
            name = mesh_elem.get('name')
            filename = mesh_elem.get('file')
            
            if name and filename:
                # Resolve relative paths
                if not Path(filename).is_absolute():
                    full_path = context.base_dir / filename
                    if full_path.exists():
                        meshes[name] = str(full_path)
                    else:
                        context.add_warning(f"Mesh file not found: {filename}")
                        meshes[name] = filename
                else:
                    meshes[name] = filename
        
        return meshes
    
    def _parse_actuators(self, actuator_elem: ET.Element, 
                        context: ParseContext) -> List[Actuator]:
        """Parse actuator definitions with validation."""
        actuators = []
        
        for motor_elem in actuator_elem.findall('motor'):
            name = motor_elem.get('name')
            joint = motor_elem.get('joint')
            
            if not name or not joint:
                context.add_warning("Motor missing name or joint reference")
                continue
            
            actuator = Actuator(
                name=sanitize_name(name),
                joint=sanitize_name(joint),
                type=ActuatorType.DC_MOTOR
            )
            
            # Parse gear ratio
            gear_str = motor_elem.get('gear')
            if gear_str:
                try:
                    gear_values = [float(x) for x in gear_str.split()]
                    if gear_values:
                        actuator.gear_ratio = gear_values[0]
                except ValueError:
                    context.add_warning(f"Invalid gear values for motor {name}")
            
            # Parse control range
            ctrlrange_str = motor_elem.get('ctrlrange')
            if ctrlrange_str:
                try:
                    ctrl_range = [float(x) for x in ctrlrange_str.split()]
                    if len(ctrl_range) == 2:
                        actuator.control_range = (ctrl_range[0], ctrl_range[1])
                except ValueError:
                    context.add_warning(f"Invalid control range for motor {name}")
            
            actuators.append(actuator)
        
        return actuators
    
    def _parse_sensors(self, sensor_elem: ET.Element, 
                      context: ParseContext) -> List[Sensor]:
        """Parse sensor definitions with comprehensive type support."""
        sensors = []
        
        # Parse various sensor types
        sensor_types = [
            'accelerometer', 'gyro', 'force', 'torque', 
            'magnetometer', 'rangefinder', 'camera'
        ]
        
        for sensor_type in sensor_types:
            for sens_elem in sensor_elem.findall(sensor_type):
                name = sens_elem.get('name')
                site = sens_elem.get('site')
                
                if not name:
                    context.add_warning(f"Sensor {sensor_type} missing name")
                    continue
                
                sensor = Sensor(
                    name=sanitize_name(name),
                    type=sensor_type,
                    parent_link=site or 'world'
                )
                
                # Parse sensor-specific parameters
                if sensor_type == 'camera':
                    resolution = sens_elem.get('resolution')
                    if resolution:
                        try:
                            res_values = [int(x) for x in resolution.split()]
                            sensor.parameters['resolution'] = res_values
                        except ValueError:
                            context.add_warning(f"Invalid resolution for camera {name}")
                
                sensors.append(sensor)
        
        return sensors
    
    def _parse_float_attr(self, elem: ET.Element, attr: str) -> Optional[float]:
        """Parse float attribute with error handling."""
        value = elem.get(attr)
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None


class SchemaParser(BaseParser):
    """ parser for common schema YAML/JSON files."""
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid schema file."""
        try:
            path = Path(file_path)
            if path.suffix.lower() in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    return False
                with open(path, 'r') as f:
                    yaml.safe_load(f)
                return True
            elif path.suffix.lower() == '.json':
                with open(path, 'r') as f:
                    json.load(f)
                return True
        except Exception:
            pass
        return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse schema file to common schema."""
        path = Path(input_path)
        
        # Load data based on file extension
        if path.suffix.lower() in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        else:  # JSON
            with open(path, 'r') as f:
                data = json.load(f)
        
        # Convert dictionary to CommonSchema
        return self._dict_to_schema(data)
    
    def _dict_to_schema(self, data: Dict) -> CommonSchema:
        """Convert dictionary data to CommonSchema object with validation."""
        # Parse metadata
        metadata_data = data.get('metadata', {})
        metadata = Metadata(
            name=metadata_data.get('name', 'robot'),
            version=metadata_data.get('version', '1.0'),
            author=metadata_data.get('author'),
            description=metadata_data.get('description'),
            source_format='schema'
        )
        
        # Convert links from dictionaries
        links = []
        for link_data in data.get('links', []):
            link = Link(name=link_data['name'])
            link.mass = link_data.get('mass', 0.0)
            
            # Parse center of mass
            com_data = link_data.get('center_of_mass', [0, 0, 0])
            link.center_of_mass = Vector3(com_data[0], com_data[1], com_data[2])
            
            # Parse inertia
            inertia_data = link_data.get('inertia', {})
            if inertia_data:
                link.inertia = Inertia(
                    ixx=inertia_data.get('ixx', 0.0),
                    iyy=inertia_data.get('iyy', 0.0),
                    izz=inertia_data.get('izz', 0.0),
                    ixy=inertia_data.get('ixy', 0.0),
                    ixz=inertia_data.get('ixz', 0.0),
                    iyz=inertia_data.get('iyz', 0.0)
                )
            
            links.append(link)
        
        # Convert joints from dictionaries
        joints = []
        for joint_data in data.get('joints', []):
            joint_type = joint_data.get('type', 'fixed')
            
            # Map string to enum
            type_mapping = {
                'revolute': JointType.REVOLUTE,
                'continuous': JointType.CONTINUOUS,
                'prismatic': JointType.PRISMATIC,
                'fixed': JointType.FIXED,
                'floating': JointType.FLOATING,
                'planar': JointType.PLANAR
            }
            
            joint = Joint(
                name=joint_data['name'],
                type=type_mapping.get(joint_type, JointType.FIXED),
                parent_link=joint_data['parent_link'],
                child_link=joint_data['child_link']
            )
            
            # Parse pose
            pose_data = joint_data.get('pose', {})
            if pose_data:
                pos_data = pose_data.get('position', [0, 0, 0])
                orient_data = pose_data.get('orientation', [0, 0, 0, 1])
                joint.pose = Pose(
                    position=Vector3(pos_data[0], pos_data[1], pos_data[2]),
                    orientation=Quaternion(orient_data[0], orient_data[1], 
                                         orient_data[2], orient_data[3])
                )
            
            # Parse axis
            axis_data = joint_data.get('axis', [0, 0, 1])
            joint.axis = Vector3(axis_data[0], axis_data[1], axis_data[2])
            
            # Parse limits
            limits_data = joint_data.get('limits', {})
            if limits_data:
                joint.limits = JointLimits(
                    lower=limits_data.get('lower'),
                    upper=limits_data.get('upper'),
                    effort=limits_data.get('effort'),
                    velocity=limits_data.get('velocity')
                )
            
            joints.append(joint)
        
        # Convert other components
        actuators = [
            Actuator(
                name=act_data['name'],
                joint=act_data['joint'],
                type=act_data.get('type', 'motor')
            )
            for act_data in data.get('actuators', [])
        ]
        
        sensors = [
            Sensor(
                name=sens_data['name'],
                type=sens_data['type'],
                parent_link=sens_data.get('parent_link', 'world')
            )
            for sens_data in data.get('sensors', [])
        ]
        
        contacts = []
        
        return CommonSchema(
            metadata=metadata,
            links=links,
            joints=joints,
            actuators=actuators,
            sensors=sensors,
            contacts=contacts
        )


class SDFParser(BaseParser):
    """Parser for SDF (Simulation Description Format) files."""
    
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a valid SDF file."""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag in ['sdf', 'world']
        except Exception:
            return False
    
    def parse(self, input_path: Union[str, Path]) -> CommonSchema:
        """Parse SDF file to common schema."""
        # Simplified SDF parser - full implementation would be much more complex
        import xml.etree.ElementTree as ET
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


# Export all parsers
__all__ = [
    'URDFParser',
    'MJCFParser', 
    'SchemaParser',
    'SDFParser',
    'USDParser',
    'URDFParser',
    'MJCFParser',
    'SchemaParser',
    'ParseError',
    'ValidationError',
    'ParseContext'
]
