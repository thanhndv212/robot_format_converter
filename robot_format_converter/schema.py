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
Common schema definition for robot description format conversion.

This module defines a unified intermediate representation that can capture
the semantics of different robot description formats while preserving
format-specific information through extensions.
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class JointType(Enum):
    """Supported joint types across formats."""
    REVOLUTE = "revolute"
    PRISMATIC = "prismatic" 
    CONTINUOUS = "continuous"
    FIXED = "fixed"
    FLOATING = "floating"
    PLANAR = "planar"
    SPHERICAL = "spherical"  # SDF/USD specific
    UNIVERSAL = "universal"  # SDF/USD specific


class GeometryType(Enum):
    """Supported geometry types."""
    BOX = "box"
    CYLINDER = "cylinder"
    SPHERE = "sphere"
    MESH = "mesh"
    PLANE = "plane"
    CAPSULE = "capsule"  # MJCF/SDF specific
    ELLIPSOID = "ellipsoid"  # SDF specific


class ActuatorType(Enum):
    """Supported actuator models."""
    DC_MOTOR = "dc_motor"
    SERVO = "servo"
    VELOCITY = "velocity"
    POSITION = "position" 
    TORQUE = "torque"
    MUSCLE = "muscle"  # MJCF specific


@dataclass
class Vector3:
    """3D vector representation."""
    x: float = 0.0
    y: float = 0.0 
    z: float = 0.0
    
    def to_list(self) -> List[float]:
        """Convert to list format."""
        return [self.x, self.y, self.z]
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z])
    
    @classmethod
    def from_list(cls, values: List[float]) -> 'Vector3':
        """Create from list of values."""
        return cls(values[0], values[1], values[2])


@dataclass
class Quaternion:
    """Quaternion representation for rotations."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0
    
    def to_list(self) -> List[float]:
        """Convert to list format [x, y, z, w]."""
        return [self.x, self.y, self.z, self.w]
    
    @classmethod
    def from_rpy(cls, roll: float, pitch: float, yaw: float) -> 'Quaternion':
        """Create quaternion from roll-pitch-yaw angles."""
        # Simplified conversion - full implementation would use proper math
        # This is a placeholder for demonstration
        return cls(0.0, 0.0, 0.0, 1.0)


@dataclass
class Pose:
    """6DOF pose representation."""
    position: Vector3 = field(default_factory=Vector3)
    orientation: Quaternion = field(default_factory=Quaternion)
    
    @classmethod
    def from_xyzrpy(cls, xyz: List[float], rpy: List[float]) -> 'Pose':
        """Create pose from position and RPY orientation."""
        return cls(
            position=Vector3.from_list(xyz),
            orientation=Quaternion.from_rpy(rpy[0], rpy[1], rpy[2])
        )


@dataclass
class Inertia:
    """Inertia tensor representation."""
    ixx: float = 0.0
    iyy: float = 0.0
    izz: float = 0.0
    ixy: float = 0.0
    ixz: float = 0.0
    iyz: float = 0.0
    
    def to_matrix(self) -> np.ndarray:
        """Convert to 3x3 inertia matrix."""
        return np.array([
            [self.ixx, self.ixy, self.ixz],
            [self.ixy, self.iyy, self.iyz], 
            [self.ixz, self.iyz, self.izz]
        ])


@dataclass
class Material:
    """Material properties for visual and collision elements."""
    name: Optional[str] = None
    color: Optional[List[float]] = None  # RGBA
    texture: Optional[str] = None
    specular: Optional[List[float]] = None
    emissive: Optional[List[float]] = None
    shininess: Optional[float] = None


@dataclass
class Geometry:
    """Geometric shape definition."""
    type: GeometryType
    
    # Box parameters
    size: Optional[Vector3] = None
    
    # Cylinder parameters  
    radius: Optional[float] = None
    length: Optional[float] = None
    
    # Sphere parameters
    # radius is shared
    
    # Mesh parameters
    filename: Optional[str] = None
    scale: Optional[Vector3] = None
    
    # Format-specific extensions
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Visual:
    """Visual representation of a link."""
    name: Optional[str] = None
    pose: Pose = field(default_factory=Pose) 
    geometry: Optional[Geometry] = None
    material: Optional[Material] = None
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Collision:
    """Collision representation of a link."""
    name: Optional[str] = None
    pose: Pose = field(default_factory=Pose)
    geometry: Optional[Geometry] = None
    
    # Contact properties
    mu_static: Optional[float] = None
    mu_dynamic: Optional[float] = None
    restitution: Optional[float] = None
    stiffness: Optional[float] = None
    damping: Optional[float] = None
    
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Link:
    """Robot link definition."""
    name: str
    
    # Inertial properties
    mass: float = 0.0
    center_of_mass: Vector3 = field(default_factory=Vector3)
    inertia: Inertia = field(default_factory=Inertia)
    
    # Geometric representations
    visuals: List[Visual] = field(default_factory=list)
    collisions: List[Collision] = field(default_factory=list)
    
    # Format-specific extensions
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class JointLimits:
    """Joint limit specification."""
    lower: Optional[float] = None
    upper: Optional[float] = None
    effort: Optional[float] = None
    velocity: Optional[float] = None
    
    # Additional limits for specific formats
    acceleration: Optional[float] = None  # MJCF
    jerkmax: Optional[float] = None  # MJCF


@dataclass
class JointDynamics:
    """Joint dynamics properties."""
    damping: float = 0.0
    friction: float = 0.0
    spring_reference: float = 0.0
    spring_stiffness: float = 0.0
    
    # Format-specific properties
    armature: Optional[float] = None  # MJCF
    backlash: Optional[float] = None


@dataclass
class Joint:
    """Robot joint definition."""
    name: str
    type: JointType
    parent_link: str
    child_link: str
    
    # Kinematic properties
    pose: Pose = field(default_factory=Pose)
    axis: Vector3 = field(default_factory=lambda: Vector3(0, 0, 1))
    
    # Constraints
    limits: Optional[JointLimits] = None
    dynamics: Optional[JointDynamics] = None
    
    # Safety and calibration
    safety_controller: Optional[Dict[str, float]] = None
    calibration: Optional[Dict[str, float]] = None
    
    # Format-specific extensions
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Actuator:
    """Actuator/motor definition."""
    name: str
    joint: str
    type: ActuatorType
    
    # Motor parameters
    torque_constant: Optional[float] = None
    gear_ratio: Optional[float] = None
    max_current: Optional[float] = None
    max_torque: Optional[float] = None
    max_velocity: Optional[float] = None
    
    # Control parameters
    kp: Optional[float] = None  # Proportional gain
    ki: Optional[float] = None  # Integral gain  
    kd: Optional[float] = None  # Derivative gain
    
    # Physical properties
    resistance: Optional[float] = None
    inductance: Optional[float] = None
    efficiency: Optional[float] = None
    
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Sensor:
    """Sensor definition."""
    name: str
    type: str  # IMU, camera, lidar, force_torque, etc.
    parent_link: str
    pose: Pose = field(default_factory=Pose)
    
    # Update rate
    update_rate: Optional[float] = None
    
    # Noise model
    noise: Optional[Dict[str, Union[float, List[float]]]] = None
    
    # Sensor-specific parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactSurface:
    """Contact surface properties."""
    mu_static: float = 0.8
    mu_dynamic: float = 0.7
    restitution: float = 0.1
    stiffness: float = 10000.0
    damping: float = 20.0
    
    # Advanced contact parameters
    slip_compliance: Optional[Dict[str, float]] = None
    soft_cfm: Optional[float] = None  # Constraint force mixing
    soft_erp: Optional[float] = None  # Error reduction parameter


@dataclass 
class Contact:
    """Contact definition for collision detection."""
    name: str
    link: str
    surface: ContactSurface = field(default_factory=ContactSurface)
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metadata:
    """Robot model metadata."""
    name: str
    version: str = "1.0"
    author: Optional[str] = None
    description: Optional[str] = None
    source_format: Optional[str] = None
    creation_date: Optional[str] = None
    units: str = "SI"  # meters, kg, seconds, radians
    
    # Format-specific metadata
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommonSchema:
    """
    Unified robot description schema.
    
    This schema serves as an intermediate representation that can capture
    the semantics of different robot description formats while preserving
    format-specific information through extensions.
    
    The schema follows a hierarchical structure:
    - Metadata: Robot-level information
    - Links: Physical bodies with inertial, visual, and collision properties
    - Joints: Kinematic connections between links
    - Actuators: Motors and drive systems  
    - Sensors: Sensing systems
    - Contacts: Contact surface definitions
    
    Extensions allow format-specific features to be preserved during
    conversion while maintaining compatibility across formats.
    """
    
    metadata: Metadata
    links: List[Link] = field(default_factory=list)
    joints: List[Joint] = field(default_factory=list)
    actuators: List[Actuator] = field(default_factory=list) 
    sensors: List[Sensor] = field(default_factory=list)
    contacts: List[Contact] = field(default_factory=list)
    
    # Global extensions for format-specific features
    extensions: Dict[str, Any] = field(default_factory=dict)
    
    def get_link(self, name: str) -> Optional[Link]:
        """Get link by name."""
        for link in self.links:
            if link.name == name:
                return link
        return None
    
    def get_joint(self, name: str) -> Optional[Joint]:
        """Get joint by name.""" 
        for joint in self.joints:
            if joint.name == name:
                return joint
        return None
    
    def get_actuator(self, name: str) -> Optional[Actuator]:
        """Get actuator by name."""
        for actuator in self.actuators:
            if actuator.name == name:
                return actuator
        return None
    
    def get_root_links(self) -> List[Link]:
        """Get links that are not children of any joint (root links)."""
        child_links = {joint.child_link for joint in self.joints}
        return [link for link in self.links if link.name not in child_links]
    
    def get_kinematic_tree(self) -> Dict[str, List[str]]:
        """Get kinematic tree structure as parent->children mapping."""
        tree = {}
        for joint in self.joints:
            parent = joint.parent_link
            child = joint.child_link
            if parent not in tree:
                tree[parent] = []
            tree[parent].append(child)
        return tree
    
    def validate(self) -> List[str]:
        """
        Validate schema consistency and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Check for duplicate names
        link_names = [link.name for link in self.links]
        if len(link_names) != len(set(link_names)):
            issues.append("Duplicate link names found")
        
        joint_names = [joint.name for joint in self.joints] 
        if len(joint_names) != len(set(joint_names)):
            issues.append("Duplicate joint names found")
        
        # Check joint references
        for joint in self.joints:
            if not self.get_link(joint.parent_link):
                issues.append(f"Joint '{joint.name}' references unknown parent link: {joint.parent_link}")
            if not self.get_link(joint.child_link):
                issues.append(f"Joint '{joint.name}' references unknown child link: {joint.child_link}")
        
        # Check actuator references
        for actuator in self.actuators:
            if not self.get_joint(actuator.joint):
                issues.append(f"Actuator '{actuator.name}' references unknown joint: {actuator.joint}")
        
        # Check sensor references
        for sensor in self.sensors:
            if not self.get_link(sensor.parent_link):
                issues.append(f"Sensor '{sensor.name}' references unknown parent link: {sensor.parent_link}")
        
        # Check for kinematic loops (basic check)
        try:
            roots = self.get_root_links()
            if len(roots) == 0:
                issues.append("No root links found - possible kinematic loop")
        except Exception:
            issues.append("Error analyzing kinematic structure")
        
        return issues
