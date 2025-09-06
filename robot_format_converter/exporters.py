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
Format exporters for converting common schema to robot description formats.
"""

import json
import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Union, Optional, Dict, List
import logging

from .core import BaseExporter
from .schema import (
    CommonSchema, JointType, GeometryType, Link, Joint, Visual, Collision,
    Geometry, Material, Pose, Actuator
)

logger = logging.getLogger(__name__)


class URDFExporter(BaseExporter):
    """Exporter for URDF (Unified Robot Description Format) files."""
    
    def get_extension(self) -> str:
        """Return file extension for URDF format."""
        return 'urdf'
    
    def export(self, schema: CommonSchema, output_path: Union[str, Path]) -> None:
        """Export common schema to URDF format."""
        # Create root robot element
        robot = ET.Element('robot', name=schema.metadata.name)
        
        # Add links
        for link in schema.links:
            self._add_link(robot, link)
        
        # Add joints
        for joint in schema.joints:
            self._add_joint(robot, joint)
        
        # Write to file
        self._write_pretty_xml(robot, output_path)
        logger.info(f"Exported URDF to: {output_path}")
    
    def _add_link(self, robot: ET.Element, link: Link) -> None:
        """Add link element to URDF."""
        link_elem = ET.SubElement(robot, 'link', name=link.name)
        
        # Add inertial properties
        if link.mass > 0 or any([link.inertia.ixx, link.inertia.iyy, link.inertia.izz]):
            inertial = ET.SubElement(link_elem, 'inertial')
            
            # Mass
            ET.SubElement(inertial, 'mass', value=str(link.mass))
            
            # Center of mass
            com = link.center_of_mass
            ET.SubElement(inertial, 'origin', 
                         xyz=f"{com.x} {com.y} {com.z}",
                         rpy="0 0 0")
            
            # Inertia tensor
            I = link.inertia
            ET.SubElement(inertial, 'inertia',
                         ixx=str(I.ixx), iyy=str(I.iyy), izz=str(I.izz),
                         ixy=str(I.ixy), ixz=str(I.ixz), iyz=str(I.iyz))
        
        # Add visual elements
        for visual in link.visuals:
            self._add_visual(link_elem, visual)
        
        # Add collision elements
        for collision in link.collisions:
            self._add_collision(link_elem, collision)
    
    def _add_joint(self, robot: ET.Element, joint: Joint) -> None:
        """Add joint element to URDF."""
        # Map joint types to URDF
        type_mapping = {
            JointType.REVOLUTE: 'revolute',
            JointType.CONTINUOUS: 'continuous', 
            JointType.PRISMATIC: 'prismatic',
            JointType.FIXED: 'fixed',
            JointType.FLOATING: 'floating',
            JointType.PLANAR: 'planar'
        }
        
        urdf_type = type_mapping.get(joint.type, 'fixed')
        joint_elem = ET.SubElement(robot, 'joint', 
                                  name=joint.name, 
                                  type=urdf_type)
        
        # Parent and child links
        ET.SubElement(joint_elem, 'parent', link=joint.parent_link)
        ET.SubElement(joint_elem, 'child', link=joint.child_link)
        
        # Origin/pose
        pos = joint.pose.position
        ET.SubElement(joint_elem, 'origin',
                     xyz=f"{pos.x} {pos.y} {pos.z}",
                     rpy="0 0 0")  # Simplified - would need proper quaternion to RPY
        
        # Axis
        axis = joint.axis
        ET.SubElement(joint_elem, 'axis',
                     xyz=f"{axis.x} {axis.y} {axis.z}")
        
        # Limits
        if joint.limits:
            limits = joint.limits
            limit_elem = ET.SubElement(joint_elem, 'limit')
            if limits.lower is not None:
                limit_elem.set('lower', str(limits.lower))
            if limits.upper is not None:
                limit_elem.set('upper', str(limits.upper))
            if limits.effort is not None:
                limit_elem.set('effort', str(limits.effort))
            if limits.velocity is not None:
                limit_elem.set('velocity', str(limits.velocity))
        
        # Dynamics
        if joint.dynamics:
            dyn = joint.dynamics
            ET.SubElement(joint_elem, 'dynamics',
                         damping=str(dyn.damping),
                         friction=str(dyn.friction))
    
    def _add_visual(self, link_elem: ET.Element, visual: Visual) -> None:
        """Add visual element to link."""
        visual_elem = ET.SubElement(link_elem, 'visual')
        if visual.name:
            visual_elem.set('name', visual.name)
        
        # Origin
        pos = visual.pose.position
        ET.SubElement(visual_elem, 'origin',
                     xyz=f"{pos.x} {pos.y} {pos.z}",
                     rpy="0 0 0")
        
        # Geometry
        if visual.geometry:
            self._add_geometry(visual_elem, visual.geometry)
        
        # Material
        if visual.material:
            self._add_material(visual_elem, visual.material)
    
    def _add_collision(self, link_elem: ET.Element, collision: Collision) -> None:
        """Add collision element to link."""
        collision_elem = ET.SubElement(link_elem, 'collision')
        if collision.name:
            collision_elem.set('name', collision.name)
        
        # Origin
        pos = collision.pose.position
        ET.SubElement(collision_elem, 'origin',
                     xyz=f"{pos.x} {pos.y} {pos.z}",
                     rpy="0 0 0")
        
        # Geometry
        if collision.geometry:
            self._add_geometry(collision_elem, collision.geometry)
    
    def _add_geometry(self, parent: ET.Element, geometry) -> None:
        """Add geometry element."""
        geom_elem = ET.SubElement(parent, 'geometry')
        
        if geometry.type == GeometryType.BOX:
            if geometry.size:
                size = geometry.size
                ET.SubElement(geom_elem, 'box',
                             size=f"{size.x} {size.y} {size.z}")
        
        elif geometry.type == GeometryType.CYLINDER:
            ET.SubElement(geom_elem, 'cylinder',
                         radius=str(geometry.radius or 1.0),
                         length=str(geometry.length or 1.0))
        
        elif geometry.type == GeometryType.SPHERE:
            ET.SubElement(geom_elem, 'sphere',
                         radius=str(geometry.radius or 1.0))
        
        elif geometry.type == GeometryType.MESH:
            mesh_attrs = {}
            if geometry.filename:
                mesh_attrs['filename'] = geometry.filename
            if geometry.scale:
                scale = geometry.scale
                mesh_attrs['scale'] = f"{scale.x} {scale.y} {scale.z}"
            ET.SubElement(geom_elem, 'mesh', **mesh_attrs)
    
    def _add_material(self, parent: ET.Element, material) -> None:
        """Add material element."""
        mat_elem = ET.SubElement(parent, 'material')
        if material.name:
            mat_elem.set('name', material.name)
        
        if material.color:
            color = material.color
            rgba_str = ' '.join(str(c) for c in color)
            ET.SubElement(mat_elem, 'color', rgba=rgba_str)
        
        if material.texture:
            ET.SubElement(mat_elem, 'texture', filename=material.texture)
    
    def _write_pretty_xml(self, root: ET.Element, output_path: Union[str, Path]) -> None:
        """Write XML with pretty formatting."""
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)


class SDFExporter(BaseExporter):
    """Exporter for SDF (Simulation Description Format) files."""
    
    def get_extension(self) -> str:
        """Return file extension for SDF format."""
        return 'sdf'
    
    def export(self, schema: CommonSchema, output_path: Union[str, Path]) -> None:
        """Export common schema to SDF format."""
        # Create root SDF element
        sdf = ET.Element('sdf', version='1.10')
        world = ET.SubElement(sdf, 'world', name='default')
        
        # Create a single model containing all links/joints
        model = ET.SubElement(world, 'model', name=schema.metadata.name)
        
        # Add links
        for link in schema.links:
            self._add_link(model, link)
        
        # Add joints
        for joint in schema.joints:
            self._add_joint(model, joint)
        
        # Write to file
        self._write_pretty_xml(sdf, output_path)
        logger.info(f"Exported SDF to: {output_path}")
    
    def _add_link(self, model: ET.Element, link: Link) -> None:
        """Add link element to SDF model."""
        # SDF implementation would be similar to URDF but with SDF-specific elements
        # This is a simplified placeholder
        link_elem = ET.SubElement(model, 'link', name=link.name)
        
        # Inertial
        if link.mass > 0:
            inertial = ET.SubElement(link_elem, 'inertial')
            ET.SubElement(inertial, 'mass').text = str(link.mass)
            
            com = link.center_of_mass
            ET.SubElement(inertial, 'pose').text = f"{com.x} {com.y} {com.z} 0 0 0"
    
    def _add_joint(self, model: ET.Element, joint: Joint) -> None:
        """Add joint element to SDF model."""
        # SDF joint implementation placeholder
        joint_elem = ET.SubElement(model, 'joint', name=joint.name)
        ET.SubElement(joint_elem, 'parent').text = joint.parent_link
        ET.SubElement(joint_elem, 'child').text = joint.child_link
    
    def _write_pretty_xml(self, root: ET.Element, output_path: Union[str, Path]) -> None:
        """Write XML with pretty formatting."""
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)


class MJCFExporter(BaseExporter):
    """Exporter for MJCF (MuJoCo Model Format) files."""
    
    def get_extension(self) -> str:
        """Return file extension for MJCF format."""
        return 'xml'
    
    def export(self, schema: CommonSchema, output_path: Union[str, Path]) -> None:
        """Export common schema to MJCF format."""
        # Create root mujoco element
        mujoco = ET.Element('mujoco', model=schema.metadata.name)
        
        # Add compiler settings
        compiler = ET.SubElement(mujoco, 'compiler', 
                                angle='radian', autolimits='true')
        
        # Add option settings
        option = ET.SubElement(mujoco, 'option', integrator='implicitfast')
        
        # Add asset section for materials
        asset = ET.SubElement(mujoco, 'asset')
        materials_used = set()
        
        # Collect all materials used
        for link in schema.links:
            for visual in link.visuals:
                if visual.material and visual.material.name:
                    materials_used.add(visual.material.name)
        
        # Add materials to asset section
        for link in schema.links:
            for visual in link.visuals:
                if visual.material and visual.material.name in materials_used:
                    self._add_material(asset, visual.material)
                    materials_used.remove(visual.material.name)
        
        # Create worldbody
        worldbody = ET.SubElement(mujoco, 'worldbody')
        
        # Find root links (those not child of any joint)
        child_links = {joint.child_link for joint in schema.joints}
        root_links = [link for link in schema.links 
                     if link.name not in child_links and link.name != 'world']
        
        # If no root links found, use first link
        if not root_links and schema.links:
            root_links = [schema.links[0]]
        
        # Build body hierarchy
        link_to_children = {}
        for joint in schema.joints:
            parent = joint.parent_link
            child = joint.child_link
            if parent not in link_to_children:
                link_to_children[parent] = []
            link_to_children[parent].append((joint, child))
        
        # Add root bodies to worldbody
        for root_link in root_links:
            if root_link.name != 'world':
                self._add_body_hierarchy(
                    worldbody, root_link, schema, link_to_children
                )
        
        # Add actuators
        if schema.actuators:
            actuator_elem = ET.SubElement(mujoco, 'actuator')
            for actuator in schema.actuators:
                self._add_actuator(actuator_elem, actuator)
        
        self._write_pretty_xml(mujoco, output_path)
        logger.info(f"Exported MJCF to: {output_path}")
    
    def _add_material(self, asset: ET.Element, material: Material) -> None:
        """Add material to asset section."""
        mat_elem = ET.SubElement(asset, 'material', name=material.name)
        
        if material.color:
            # Convert RGBA to string
            rgba_str = ' '.join(str(c) for c in material.color[:4])
            mat_elem.set('rgba', rgba_str)
        
        if hasattr(material, 'specular') and material.specular:
            mat_elem.set('specular', str(material.specular))
        
        if hasattr(material, 'shininess') and material.shininess:
            mat_elem.set('shininess', str(material.shininess))
    
    def _add_body_hierarchy(
        self, 
        parent_elem: ET.Element,
        link: Link,
        schema: CommonSchema,
        link_to_children: Dict[str, List[tuple]]
    ) -> None:
        """Add body and its children recursively."""
        
        # Create body element
        body = ET.SubElement(parent_elem, 'body', name=link.name)
        
        # Add inertial properties
        if link.mass > 0:
            inertial = ET.SubElement(body, 'inertial')
            inertial.set('mass', str(link.mass))
            
            if link.center_of_mass:
                pos = f"{link.center_of_mass.x} {link.center_of_mass.y} {link.center_of_mass.z}"
                inertial.set('pos', pos)
            
            if link.inertia:
                # Use diagonal inertia for simplicity
                diag = f"{link.inertia.ixx} {link.inertia.iyy} {link.inertia.izz}"
                inertial.set('diaginertia', diag)
        
        # Add visual geometries
        for i, visual in enumerate(link.visuals):
            self._add_geom(body, visual.geometry, visual.material, 
                          visual.pose, f"visual_{i}", group='2')
        
        # Add collision geometries  
        for i, collision in enumerate(link.collisions):
            self._add_geom(body, collision.geometry, None,
                          collision.pose, f"collision_{i}", group='3')
        
        # Add child bodies
        if link.name in link_to_children:
            for joint, child_link_name in link_to_children[link.name]:
                child_link = next(
                    (l for l in schema.links if l.name == child_link_name), None
                )
                if child_link:
                    # Set position and joint for child body
                    child_body = self._add_body_with_joint(
                        body, child_link, joint, schema, link_to_children
                    )
    
    def _add_body_with_joint(
        self,
        parent_elem: ET.Element,
        link: Link,
        joint: Joint,
        schema: CommonSchema,
        link_to_children: Dict[str, List[tuple]]
    ) -> ET.Element:
        """Add body with joint connection."""
        
        # Create body element
        body = ET.SubElement(parent_elem, 'body', name=link.name)
        
        # Set position from joint pose
        if joint.pose and joint.pose.position:
            pos = joint.pose.position
            pos_str = f"{pos.x} {pos.y} {pos.z}"
            body.set('pos', pos_str)
        
        # Set orientation from joint pose
        if joint.pose and joint.pose.orientation:
            quat = joint.pose.orientation
            # MuJoCo uses w x y z format
            quat_str = f"{quat.w} {quat.x} {quat.y} {quat.z}"
            body.set('quat', quat_str)
        
        # Add joint element
        if joint.type != JointType.FIXED:
            joint_elem = ET.SubElement(body, 'joint', name=joint.name)
            
            # Set joint axis
            if joint.axis:
                axis_str = f"{joint.axis.x} {joint.axis.y} {joint.axis.z}"
                joint_elem.set('axis', axis_str)
            
            # Set joint limits
            if joint.limits:
                if joint.limits.lower is not None and joint.limits.upper is not None:
                    range_str = f"{joint.limits.lower} {joint.limits.upper}"
                    joint_elem.set('range', range_str)
            
            # Set joint dynamics
            if joint.dynamics and joint.dynamics.damping:
                joint_elem.set('damping', str(joint.dynamics.damping))
        
        # Add inertial properties
        if link.mass > 0:
            inertial = ET.SubElement(body, 'inertial')
            inertial.set('mass', str(link.mass))
            
            if link.center_of_mass:
                pos = f"{link.center_of_mass.x} {link.center_of_mass.y} {link.center_of_mass.z}"
                inertial.set('pos', pos)
            
            if link.inertia:
                diag = f"{link.inertia.ixx} {link.inertia.iyy} {link.inertia.izz}"
                inertial.set('diaginertia', diag)
        
        # Add geometries
        for i, visual in enumerate(link.visuals):
            self._add_geom(body, visual.geometry, visual.material,
                          visual.pose, f"visual_{i}", group='2')
        
        for i, collision in enumerate(link.collisions):
            self._add_geom(body, collision.geometry, None,
                          collision.pose, f"collision_{i}", group='3')
        
        # Add child bodies recursively
        if link.name in link_to_children:
            for child_joint, child_link_name in link_to_children[link.name]:
                child_link = next(
                    (l for l in schema.links if l.name == child_link_name), None
                )
                if child_link:
                    self._add_body_with_joint(
                        body, child_link, child_joint, schema, link_to_children
                    )
        
        return body
    
    def _add_geom(
        self, 
        body: ET.Element,
        geometry: Geometry,
        material: Optional[Material],
        pose: Optional[Pose],
        name_suffix: str,
        group: str = '0'
    ) -> None:
        """Add geometry element to body."""
        
        geom = ET.SubElement(body, 'geom')
        geom.set('group', group)
        
        # Set position
        if pose and pose.position:
            pos = pose.position
            pos_str = f"{pos.x} {pos.y} {pos.z}"
            geom.set('pos', pos_str)
        
        # Set orientation  
        if pose and pose.orientation:
            quat = pose.orientation
            quat_str = f"{quat.w} {quat.x} {quat.y} {quat.z}"
            geom.set('quat', quat_str)
        
        # Set geometry type and parameters
        if geometry.type == GeometryType.BOX:
            geom.set('type', 'box')
            if geometry.size:
                # MJCF uses half-extents
                size_str = f"{geometry.size.x/2} {geometry.size.y/2} {geometry.size.z/2}"
                geom.set('size', size_str)
        
        elif geometry.type == GeometryType.SPHERE:
            geom.set('type', 'sphere')
            if geometry.radius:
                geom.set('size', str(geometry.radius))
        
        elif geometry.type == GeometryType.CYLINDER:
            geom.set('type', 'cylinder')
            if geometry.radius and geometry.length:
                # MJCF uses radius and half-height
                size_str = f"{geometry.radius} {geometry.length/2}"
                geom.set('size', size_str)
        
        elif geometry.type == GeometryType.MESH:
            geom.set('type', 'mesh')
            if geometry.filename:
                # Extract mesh name from filename
                mesh_name = Path(geometry.filename).stem
                geom.set('mesh', mesh_name)
        
        else:
            # Default to box
            geom.set('type', 'box')
            geom.set('size', '0.1 0.1 0.1')
        
        # Set material
        if material and material.name:
            geom.set('material', material.name)
    
    def _add_actuator(self, actuator_elem: ET.Element, actuator: Actuator) -> None:
        """Add actuator to actuator section."""
        
        act_type = actuator.type if hasattr(actuator, 'type') else 'general'
        act = ET.SubElement(actuator_elem, act_type, 
                           name=actuator.name, joint=actuator.joint)
        
        # Add control range
        if hasattr(actuator, 'control_range') and actuator.control_range:
            ctrl_min, ctrl_max = actuator.control_range
            ctrl_range = f"{ctrl_min} {ctrl_max}"
            act.set('ctrlrange', ctrl_range)
        
        # Add force range
        if hasattr(actuator, 'force_range') and actuator.force_range:
            force_min, force_max = actuator.force_range
            force_range = f"{force_min} {force_max}"
            act.set('forcerange', force_range)
    
    def _write_pretty_xml(self, root: ET.Element, output_path: Union[str, Path]) -> None:
        """Write XML with pretty formatting."""
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)


class SchemaExporter(BaseExporter):
    """Exporter for common schema YAML/JSON files."""
    
    def get_extension(self) -> str:
        """Return file extension for schema format.""" 
        return 'yaml'
    
    def export(self, schema: CommonSchema, output_path: Union[str, Path]) -> None:
        """Export common schema to YAML/JSON format."""
        # Convert schema to dictionary
        data = self._schema_to_dict(schema)
        
        # Determine format from extension
        path = Path(output_path)
        if path.suffix.lower() == '.json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        else:  # Default to YAML
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Exported schema to: {output_path}")
    
    def _schema_to_dict(self, schema: CommonSchema) -> dict:
        """Convert CommonSchema to dictionary representation."""
        # This would need comprehensive conversion logic
        # Simplified implementation for demonstration
        
        data = {
            'metadata': {
                'name': schema.metadata.name,
                'version': schema.metadata.version,
                'description': schema.metadata.description,
                'source_format': schema.metadata.source_format
            },
            'links': [],
            'joints': [],
            'actuators': [],
            'sensors': [],
            'contacts': []
        }
        
        # Convert links
        for link in schema.links:
            link_data = {
                'name': link.name,
                'mass': link.mass,
                'center_of_mass': link.center_of_mass.to_list(),
                'inertia': {
                    'ixx': link.inertia.ixx,
                    'iyy': link.inertia.iyy,
                    'izz': link.inertia.izz,
                    'ixy': link.inertia.ixy,
                    'ixz': link.inertia.ixz,
                    'iyz': link.inertia.iyz
                }
            }
            data['links'].append(link_data)
        
        # Convert joints
        for joint in schema.joints:
            joint_data = {
                'name': joint.name,
                'type': joint.type.value,
                'parent_link': joint.parent_link,
                'child_link': joint.child_link,
                'pose': {
                    'position': joint.pose.position.to_list(),
                    'orientation': joint.pose.orientation.to_list()
                },
                'axis': joint.axis.to_list()
            }
            
            if joint.limits:
                joint_data['limits'] = {
                    'lower': joint.limits.lower,
                    'upper': joint.limits.upper,
                    'effort': joint.limits.effort,
                    'velocity': joint.limits.velocity
                }
            
            data['joints'].append(joint_data)
        
        return data


class USDExporter(BaseExporter):
    """Exporter for USD (Universal Scene Description) files."""
    
    def get_extension(self) -> str:
        """Return file extension for USD format."""
        return 'usd'
    
    def export(self, schema: CommonSchema, output_path: Union[str, Path]) -> None:
        """Export common schema to USD format."""
        try:
            # This would require proper USD integration
            # import pxr
            # stage = pxr.Usd.Stage.CreateNew(str(output_path))
            
            # USD export implementation would go here
            logger.info(f"USD export to: {output_path} (placeholder)")
            
            # Create empty file for now
            with open(output_path, 'w') as f:
                f.write(f"# USD export placeholder for {schema.metadata.name}\n")
            
        except ImportError:
            raise RuntimeError("USD support requires pxr module: pip install usd-core")
