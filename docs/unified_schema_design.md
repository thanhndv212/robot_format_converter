# Unified Robot Format Schema Design

## Overview

This document proposes improvements to the unified robot format schema to better support conversion between URDF, MJCF, and other robot description formats while maintaining compatibility and extensibility.

## Current Schema Analysis

### Strengths
- **Format Agnostic**: Common data structures for bodies, joints, links
- **Extensible**: Plugin system for format-specific features
- **Validation**: Built-in validation capabilities
- **Metadata Support**: Rich annotation system

### Limitations
- **Limited Geometry Support**: Basic primitive shapes only
- **Missing Physics Properties**: No advanced simulation parameters
- **Coordinate System**: Single coordinate convention
- **Material System**: Basic material properties

## Proposed Unified Schema Improvements

### 1. Enhanced Geometry System

#### Current Structure
```python
@dataclass
class Geometry:
    type: str
    size: List[float]
    mesh_filename: Optional[str] = None
```

#### Improved Structure
```python
@dataclass
class Geometry:
    type: GeometryType
    primitive: Optional[PrimitiveGeometry] = None
    mesh: Optional[MeshGeometry] = None
    compound: Optional[List[Geometry]] = None
    origin: Pose = field(default_factory=Pose)
    
@dataclass  
class MeshGeometry:
    filename: str
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    convex_hull: bool = False
    vertex_data: Optional[List[float]] = None
    face_data: Optional[List[int]] = None
    texture_coords: Optional[List[float]] = None
    
@dataclass
class PrimitiveGeometry:
    shape: PrimitiveShape
    dimensions: List[float]
    
enum PrimitiveShape:
    BOX = "box"
    SPHERE = "sphere" 
    CYLINDER = "cylinder"
    CAPSULE = "capsule"
    ELLIPSOID = "ellipsoid"
    PLANE = "plane"
```

### 2. Advanced Material System

#### Current Structure
```python
@dataclass
class Material:
    name: str
    color: List[float]
```

#### Improved Structure
```python
@dataclass
class Material:
    name: str
    visual: VisualProperties
    physical: PhysicalProperties
    
@dataclass
class VisualProperties:
    color: RGBA = field(default_factory=lambda: RGBA(0.5, 0.5, 0.5, 1.0))
    texture: Optional[Texture] = None
    shininess: float = 0.0
    specular: RGB = field(default_factory=lambda: RGB(0.0, 0.0, 0.0))
    emission: RGB = field(default_factory=lambda: RGB(0.0, 0.0, 0.0))
    metallic: float = 0.0
    roughness: float = 0.5
    
@dataclass
class PhysicalProperties:
    friction: Tuple[float, float, float] = (1.0, 1.0, 0.01)  # mu1, mu2, slip
    restitution: float = 0.0
    density: Optional[float] = None
    
@dataclass
class Texture:
    filename: Optional[str] = None
    type: TextureType = TextureType.DIFFUSE
    repeat: Tuple[float, float] = (1.0, 1.0)
    offset: Tuple[float, float] = (0.0, 0.0)
    
enum TextureType:
    DIFFUSE = "diffuse"
    NORMAL = "normal" 
    SPECULAR = "specular"
    EMISSION = "emission"
```

### 3. Enhanced Physics Properties

```python
@dataclass
class InertialProperties:
    mass: float
    center_of_mass: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    inertia: InertiaMatrix = field(default_factory=InertiaMatrix)
    
@dataclass
class InertiaMatrix:
    ixx: float = 0.0
    iyy: float = 0.0  
    izz: float = 0.0
    ixy: float = 0.0
    ixz: float = 0.0
    iyz: float = 0.0
    
    def to_diagonal(self) -> Tuple[float, float, float]:
        """Convert to diagonal form for MuJoCo"""
        return (self.ixx, self.iyy, self.izz)
    
    def to_full_matrix(self) -> List[float]:
        """Convert to full 6-element format for MuJoCo"""
        return [self.ixx, self.iyy, self.izz, self.ixy, self.ixz, self.iyz]
```

### 4. Flexible Joint System

```python
@dataclass
class Joint:
    name: str
    type: JointType
    parent_link: str
    child_link: str
    origin: Pose = field(default_factory=Pose)
    axis: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    limits: Optional[JointLimits] = None
    dynamics: JointDynamics = field(default_factory=JointDynamics)
    physics: JointPhysics = field(default_factory=JointPhysics)
    
@dataclass
class JointLimits:
    lower: Optional[float] = None
    upper: Optional[float] = None
    effort: Optional[float] = None
    velocity: Optional[float] = None
    
@dataclass
class JointDynamics:
    damping: float = 0.0
    friction: float = 0.0
    stiffness: float = 0.0
    armature: float = 0.0  # For MuJoCo
    
@dataclass  
class JointPhysics:
    spring_reference: float = 0.0
    spring_stiffness: float = 0.0
    actuator_force_range: Optional[Tuple[float, float]] = None
    
enum JointType:
    REVOLUTE = "revolute"
    PRISMATIC = "prismatic" 
    CONTINUOUS = "continuous"
    FIXED = "fixed"
    FLOATING = "floating"  # 6-DOF free joint
    BALL = "ball"  # 3-DOF ball joint
    PLANAR = "planar"
```

### 5. Coordinate System Flexibility

```python
@dataclass
class Pose:
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    orientation: Orientation = field(default_factory=Orientation)
    frame: CoordinateFrame = CoordinateFrame.LOCAL
    
@dataclass
class Orientation:
    representation: OrientationType
    values: Tuple[float, ...]
    
    @classmethod
    def from_quaternion(cls, w: float, x: float, y: float, z: float):
        return cls(OrientationType.QUATERNION, (w, x, y, z))
    
    @classmethod 
    def from_euler(cls, roll: float, pitch: float, yaw: float, seq: str = "xyz"):
        return cls(OrientationType.EULER, (roll, pitch, yaw, seq))
        
    @classmethod
    def from_axis_angle(cls, x: float, y: float, z: float, angle: float):
        return cls(OrientationType.AXIS_ANGLE, (x, y, z, angle))
        
enum OrientationType:
    QUATERNION = "quaternion"
    EULER = "euler"
    AXIS_ANGLE = "axis_angle" 
    ROTATION_MATRIX = "matrix"
    
enum CoordinateFrame:
    LOCAL = "local"
    GLOBAL = "global"
```

### 6. Sensor System

```python
@dataclass
class Sensor:
    name: str
    type: SensorType
    link: str
    origin: Pose = field(default_factory=Pose)
    properties: Dict[str, Any] = field(default_factory=dict)
    
enum SensorType:
    IMU = "imu"
    FORCE_TORQUE = "force_torque"
    CAMERA = "camera"
    LIDAR = "lidar"
    JOINT_STATE = "joint_state"
    CONTACT = "contact"
```

### 7. Actuator System

```python
@dataclass
class Actuator:
    name: str
    type: ActuatorType
    joint: str
    transmission: Transmission = field(default_factory=Transmission)
    limits: ActuatorLimits = field(default_factory=ActuatorLimits)
    
@dataclass
class Transmission:
    type: TransmissionType = TransmissionType.SIMPLE
    gear_ratio: float = 1.0
    efficiency: float = 1.0
    
@dataclass
class ActuatorLimits:
    force: Optional[Tuple[float, float]] = None
    control: Optional[Tuple[float, float]] = None
    
enum ActuatorType:
    MOTOR = "motor"
    POSITION_SERVO = "position"
    VELOCITY_SERVO = "velocity"
    EFFORT_SERVO = "effort"
    
enum TransmissionType:
    SIMPLE = "simple"
    DIFFERENTIAL = "differential"
    SLIDER_CRANK = "slider_crank"
```

### 8. Asset Management System

```python
@dataclass
class AssetManager:
    meshes: Dict[str, MeshAsset] = field(default_factory=dict)
    textures: Dict[str, TextureAsset] = field(default_factory=dict)
    materials: Dict[str, Material] = field(default_factory=dict)
    
@dataclass
class MeshAsset:
    name: str
    filename: str
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    convex_hull: bool = False
    
@dataclass  
class TextureAsset:
    name: str
    filename: str
    type: TextureType = TextureType.DIFFUSE
```

## Implementation Benefits

### 1. Enhanced Format Support
- **MJCF**: Full support for MuJoCo-specific features
- **URDF**: Backward compatibility with all URDF constructs
- **SDF**: Support for Gazebo/Ignition features
- **Future Formats**: Extensible architecture

### 2. Improved Conversion Quality
- **Geometry**: Accurate mesh and primitive handling
- **Materials**: Rich material property mapping
- **Physics**: Comprehensive simulation parameters
- **Validation**: Schema-based validation for all formats

### 3. Better User Experience
- **Intuitive API**: Object-oriented interface
- **Error Handling**: Detailed validation and error reporting
- **Documentation**: Auto-generated docs from schema
- **IDE Support**: Full type hints and autocomplete

### 4. Performance Optimization
- **Lazy Loading**: Load assets only when needed
- **Caching**: Intelligent asset caching system
- **Streaming**: Support for large model streaming
- **Parallel Processing**: Multi-threaded conversion

## Migration Strategy

### Phase 1: Core Schema Enhancement
1. Implement enhanced geometry system
2. Add advanced material properties
3. Extend joint and physics systems

### Phase 2: Format-Specific Features
1. Add MuJoCo-specific elements
2. Enhance URDF compatibility
3. Add SDF format support

### Phase 3: Tooling and Integration
1. Update conversion utilities
2. Add validation tools
3. Create migration guides

### Example Usage

```python
# Create enhanced robot model
robot = Robot(name="advanced_robot")

# Add link with rich geometry and materials
link = Link(
    name="base_link",
    visual=Visual(
        geometry=Geometry(
            type=GeometryType.MESH,
            mesh=MeshGeometry(
                filename="base.stl",
                scale=(1.0, 1.0, 1.0)
            )
        ),
        material=Material(
            name="aluminum",
            visual=VisualProperties(
                color=RGBA(0.7, 0.7, 0.8, 1.0),
                metallic=0.8,
                roughness=0.3
            ),
            physical=PhysicalProperties(
                friction=(1.2, 1.2, 0.01),
                density=2700.0
            )
        )
    ),
    inertial=InertialProperties(
        mass=5.0,
        center_of_mass=(0.0, 0.0, 0.1),
        inertia=InertiaMatrix(ixx=0.1, iyy=0.1, izz=0.05)
    )
)

robot.add_link(link)

# Convert to different formats with enhanced fidelity
mjcf_exporter = MJCFExporter()
mjcf_model = mjcf_exporter.export(robot)

urdf_exporter = URDFExporter() 
urdf_model = urdf_exporter.export(robot)
```

## Conclusion

The proposed unified schema improvements provide a robust foundation for high-fidelity robot format conversion while maintaining backward compatibility and enabling future extensibility. The enhanced type system, rich material properties, and flexible coordinate handling address the major limitations of the current implementation.
