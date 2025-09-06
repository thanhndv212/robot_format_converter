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

"""Test configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path
from typing import Generator


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_urdf() -> str:
    """Sample URDF content for testing."""
    return '''<?xml version="1.0"?>
<robot name="test_robot">
  <link name="base_link">
    <inertial>
      <mass value="1.0"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.1" ixy="0" ixz="0" iyy="0.1" iyz="0" izz="0.1"/>
    </inertial>
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="0.1 0.1 0.1"/>
      </geometry>
      <material name="red">
        <color rgba="1 0 0 1"/>
      </material>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="0.1 0.1 0.1"/>
      </geometry>
    </collision>
  </link>
  
  <link name="link1">
    <inertial>
      <mass value="0.5"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.05" ixy="0" ixz="0" iyy="0.05" iyz="0" izz="0.05"/>
    </inertial>
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="0.05" length="0.2"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 1 1"/>
      </material>
    </visual>
  </link>
  
  <joint name="joint1" type="revolute">
    <parent link="base_link"/>
    <child link="link1"/>
    <origin xyz="0 0 0.1" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="10" velocity="1"/>
  </joint>
</robot>'''


@pytest.fixture
def sample_schema() -> dict:
    """Sample schema data for testing."""
    return {
        "metadata": {
            "name": "test_robot",
            "version": "1.0",
            "author": "Test Author",
            "description": "A test robot"
        },
        "links": [
            {
                "name": "base_link",
                "inertial": {
                    "mass": 1.0,
                    "center_of_mass": [0, 0, 0],
                    "inertia_matrix": [0.1, 0, 0, 0.1, 0, 0.1]
                },
                "visual": {
                    "geometry": {
                        "type": "box",
                        "size": [0.1, 0.1, 0.1]
                    },
                    "material": {
                        "color": [1, 0, 0, 1]
                    }
                },
                "collision": {
                    "geometry": {
                        "type": "box", 
                        "size": [0.1, 0.1, 0.1]
                    }
                }
            }
        ],
        "joints": [
            {
                "name": "joint1",
                "type": "revolute",
                "parent": "base_link",
                "child": "link1",
                "origin": {
                    "xyz": [0, 0, 0.1],
                    "rpy": [0, 0, 0]
                },
                "axis": [0, 0, 1],
                "limits": {
                    "lower": -3.14,
                    "upper": 3.14,
                    "effort": 10,
                    "velocity": 1
                }
            }
        ]
    }


@pytest.fixture
def sample_urdf_file(temp_dir: Path, sample_urdf: str) -> Path:
    """Create temporary URDF file."""
    urdf_file = temp_dir / "test_robot.urdf"
    urdf_file.write_text(sample_urdf)
    return urdf_file
