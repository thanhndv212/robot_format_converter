# MuJoCo MJCF XML Schema Documentation

## Overview

MuJoCo uses the MJCF (MuJoCo Modeling Language) format for defining robot models and physical simulations. This document provides a comprehensive overview of the XML schema structure based on the official MuJoCo documentation.

## Table of Contents

- [Root Element](#root-element)
- [Main Sections](#main-sections)
- [Schema Features](#schema-features)
- [Conversion Considerations](#conversion-considerations)
- [Best Practices](#best-practices)

## Root Element

### `<mujoco>`
The unique top-level element that identifies the XML file as an MJCF model.

**Attributes:**
- `model` (string): Name of the model (default: "MuJoCo Model")

```xml
<mujoco model="Robot Model">
  <!-- All other elements go here -->
</mujoco>
```

## Main Sections

MJCF is organized into several main sections, all of which are optional and can be repeated:

### 1. Configuration Sections

#### `<option>` - Simulation Options
Controls simulation behavior and physics parameters.

**Key Attributes:**
- `timestep` (real): Simulation time step in seconds (default: 0.002)
- `gravity` (real(3)): Gravity vector (default: "0 0 -9.81")
- `integrator` ([RK4, Euler, implicit, implicitfast]): Integration method
- `iterations` (int): Solver iterations
- `tolerance` (real): Solver tolerance

#### `<compiler>` - Compilation Settings
Controls how the model is compiled and processed.

**Key Attributes:**
- `coordinate` ([local, global]): Coordinate system convention
- `angle` ([radian, degree]): Angular unit convention  
- `meshdir` (string): Directory for mesh files
- `texturedir` (string): Directory for texture files
- `autolimits` (bool): Automatic limit detection

#### `<size>` - Memory Allocation
Specifies memory allocation for various model components.

**Key Attributes:**
- `njmax` (int): Maximum number of joints
- `nconmax` (int): Maximum number of contacts
- `nstack` (int): Stack size for computations

### 2. Assets Section

#### `<asset>` - Resource Container
Contains reusable resources that can be referenced throughout the model.

##### `<mesh>` - 3D Geometry Meshes
**Supported Formats:** STL, OBJ, MSH (custom format)

**Key Attributes:**
- `name` (string, required): Unique identifier
- `file` (string): Path to mesh file
- `scale` (real(3)): Scaling factors for each axis
- `vertex` (real array): Explicit vertex data
- `face` (int array): Face indices

```xml
<asset>
  <mesh name="link_mesh" file="meshes/link.stl" scale="1 1 1"/>
</asset>
```

##### `<texture>` - Image and Procedural Textures
**Key Attributes:**
- `name` (string, required): Unique identifier
- `type` ([2d, cube, skybox]): Texture type
- `file` (string): Image file path
- `builtin` ([gradient, checker, flat]): Procedural texture type

##### `<material>` - Material Properties
**Key Attributes:**
- `name` (string, required): Unique identifier
- `texture` (string): Reference to texture
- `rgba` (real(4)): Color and transparency
- `shininess` (real): Surface shininess
- `reflectance` (real): Surface reflectance

### 3. Kinematic Tree

#### `<body>` / `<worldbody>` - Hierarchical Body Structure
The kinematic tree is built through nested body elements.

**Key Attributes:**
- `name` (string): Body identifier
- `pos` (real(3)): Position relative to parent
- `quat` (real(4)): Orientation quaternion
- `euler` (real(3)): Euler angles (alternative to quat)

##### `<inertial>` - Mass and Inertia Properties
**Key Attributes:**
- `mass` (real, required): Body mass
- `pos` (real(3), required): Center of mass position
- `diaginertia` (real(3)): Diagonal inertia matrix
- `fullinertia` (real(6)): Full symmetric inertia matrix

##### `<joint>` - Degrees of Freedom
**Joint Types:**
- `free`: 6-DOF floating body (3 translation + 3 rotation)
- `ball`: 3-DOF ball joint (3 rotation)
- `hinge`: 1-DOF revolute joint
- `slide`: 1-DOF prismatic joint

**Key Attributes:**
- `name` (string): Joint identifier
- `type` ([free, ball, slide, hinge]): Joint type
- `pos` (real(3)): Joint position in body frame
- `axis` (real(3)): Joint axis (for hinge/slide joints)
- `range` (real(2)): Joint limits
- `stiffness` (real): Joint stiffness
- `damping` (real): Joint damping

##### `<geom>` - Collision and Visual Geometry
**Geometry Types:**
- Primitives: `sphere`, `box`, `cylinder`, `capsule`, `ellipsoid`, `plane`
- Complex: `mesh`, `hfield`

**Key Attributes:**
- `name` (string): Geometry identifier
- `type` (string): Geometry type
- `size` (real array): Geometry dimensions
- `pos` (real(3)): Position in body frame
- `material` (string): Reference to material
- `rgba` (real(4)): Color override
- `mesh` (string): Reference to mesh asset

##### `<site>` - Reference Points
Used for sensors, cameras, and other attachments.

**Key Attributes:**
- `name` (string): Site identifier
- `pos` (real(3)): Position in body frame
- `size` (real(3)): Site dimensions (for visualization)

### 4. Mechanical Elements

#### `<actuator>` - Motors and Actuators
**Actuator Types:**
- `motor`: Direct force/torque application
- `position`: Position servo
- `velocity`: Velocity servo
- `general`: Configurable actuator

**Key Attributes:**
- `name` (string): Actuator identifier
- `joint` (string): Target joint reference
- `gear` (real(6)): Force/torque scaling
- `ctrlrange` (real(2)): Control input range

#### `<tendon>` - Cable Mechanisms
**Tendon Types:**
- `fixed`: Direct joint coupling
- `spatial`: 3D cable routing

### 5. Sensing

#### `<sensor>` - Various Sensor Types
**Sensor Types:**
- `accelerometer`: 3D acceleration
- `gyro`: 3D angular velocity
- `force`: 6D force/torque
- `torque`: Joint torque
- `position`: Joint position

## Schema Features

### Attribute Types
- **string**: Text values (names, file paths)
- **int(N)**: Integer arrays of length N
- **real(N)**: Real number arrays of length N
- **[keyword1, keyword2, ...]**: Enumerated values

### Element Multiplicity Notation
- **!**: Required, appears exactly once
- **?**: Optional, appears at most once  
- **\***: Optional, can appear multiple times
- **R**: Recursive, can appear multiple times with nesting

### Coordinate Systems
- Support for both local and global coordinate conventions
- Multiple orientation representations:
  - Quaternions (`quat`)
  - Euler angles (`euler`)
  - Axis-angle (`axisangle`)
  - Two axes (`xyaxes`)
  - Single axis (`zaxis`)

### Inheritance and Defaults
- Property inheritance through kinematic tree
- Default classes for common property sets
- Childclass attributes for scoped defaults

## Conversion Considerations

### MJCF to URDF Conversion
**Challenges:**
1. **Coordinate Systems**: MJCF uses flexible coordinate conventions, URDF is more rigid
2. **Joint Types**: MJCF ball joints need decomposition for URDF
3. **Geometry**: MJCF mesh handling is more sophisticated
4. **Materials**: MJCF material system is richer than URDF

**Solutions:**
1. Normalize coordinate systems during conversion
2. Decompose complex joints into equivalent joint chains
3. Extract mesh references and maintain asset paths
4. Map material properties to closest URDF equivalents

### URDF to MJCF Conversion
**Advantages:**
1. MJCF can represent all URDF constructs
2. Enhanced physics simulation capabilities
3. Better visual rendering support

### Unified Schema Benefits
A unified schema could provide:
1. **Consistent Representation**: Common data structures across formats
2. **Validation**: Schema-based validation for all formats
3. **Extensibility**: Plugin system for format-specific features
4. **Metadata**: Rich annotation and documentation support

## Best Practices

### Model Organization
1. **Use Assets**: Define reusable meshes, textures, and materials in assets
2. **Hierarchical Structure**: Organize bodies in logical kinematic tree
3. **Naming Convention**: Use consistent, descriptive names
4. **Default Classes**: Define common properties in default classes

### Performance Optimization
1. **Mesh Optimization**: Use appropriate mesh complexity
2. **Contact Parameters**: Tune contact parameters for stability
3. **Solver Settings**: Adjust iterations and tolerance for speed/accuracy trade-off

### Validation
1. **Schema Validation**: Validate against MJCF schema
2. **Physics Testing**: Verify model behavior in simulation
3. **Visualization**: Check visual appearance and scaling

### Example Structure
```xml
<mujoco model="Robot Model">
  <compiler coordinate="local" angle="radian"/>
  
  <option timestep="0.001" gravity="0 0 -9.81"/>
  
  <asset>
    <mesh name="base_link" file="meshes/base.stl"/>
    <material name="metal" rgba="0.7 0.7 0.8 1"/>
  </asset>
  
  <worldbody>
    <body name="base_link" pos="0 0 0">
      <geom type="mesh" mesh="base_link" material="metal"/>
      <inertial mass="10" pos="0 0 0" diaginertia="1 1 1"/>
      
      <body name="link1" pos="0 0 0.1">
        <joint name="joint1" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
        <geom type="cylinder" size="0.05 0.2" rgba="0.8 0.2 0.2 1"/>
        <inertial mass="2" pos="0 0 0.1" diaginertia="0.1 0.1 0.05"/>
      </body>
    </body>
  </worldbody>
  
  <actuator>
    <motor name="motor1" joint="joint1" gear="1"/>
  </actuator>
</mujoco>
```

## Conclusion

The MuJoCo MJCF format provides a comprehensive and flexible way to define robot models with rich physics simulation capabilities. Understanding its structure is crucial for effective robot format conversion and simulation setup.
