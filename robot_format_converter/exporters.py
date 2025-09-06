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
from typing import Union, Optional
import logging

from .core import BaseExporter
from .schema import (
    CommonSchema, JointType, GeometryType, Link, Joint, Visual, Collision
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
        worldbody = ET.SubElement(mujoco, 'worldbody')
        
        # MJCF uses a different structure - this is simplified
        # Full implementation would handle MuJoCo-specific elements
        
        self._write_pretty_xml(mujoco, output_path)
        logger.info(f"Exported MJCF to: {output_path}")
    
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
