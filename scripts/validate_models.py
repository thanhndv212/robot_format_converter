#!/usr/bin/env python3
"""
Model Validation and Visualization Tool for FIGAROH

This script validates and visualizes robot models in different formats:
- URDF models using Pinocchio and PyBullet
- MJCF (.xml) models using MuJoCo

Author: Thanh D.V. Nguyen
Date: September 2025
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelValidator:
    """Base class for model validation and visualization."""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model_name = self.model_path.stem
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
    
    def validate(self) -> Dict[str, Any]:
        """Validate the model and return validation results."""
        raise NotImplementedError
    
    def visualize(self, duration: float = 10.0) -> None:
        """Visualize the model for specified duration."""
        raise NotImplementedError


class URDFValidator(ModelValidator):
    """URDF model validator using Pinocchio and PyBullet."""
    
    def __init__(self, model_path: str):
        super().__init__(model_path)
        self.robot_pinocchio = None
        self.robot_pybullet = None
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            import pinocchio as pin
            self.pin = pin
        except ImportError:
            raise ImportError(
                "Pinocchio is required for URDF validation. "
                "Install with: pip install pin"
            )
        
        try:
            import pybullet as p
            self.pybullet = p
        except ImportError:
            raise ImportError(
                "PyBullet is required for URDF visualization. "
                "Install with: pip install pybullet"
            )
    
    def validate(self) -> Dict[str, Any]:
        """Validate URDF model using Pinocchio."""
        logger.info(f"Validating URDF model: {self.model_path}")
        
        results = {
            'model_type': 'URDF',
            'model_path': str(self.model_path),
            'valid': False,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        try:
            # Load with Pinocchio
            self.robot_pinocchio = self.pin.RobotWrapper.BuildFromURDF(
                str(self.model_path)
            )
            
            # Basic validation checks
            model = self.robot_pinocchio.model
            
            results['info'].update({
                'joints': model.njoints,
                'dofs': model.nv,
                'frames': len(model.frames),
                'bodies': len(model.names),
                'joint_names': [
                    model.names[i] for i in range(1, model.njoints)
                ],
                'frame_names': [frame.name for frame in model.frames]
            })
            
            # Check for common issues
            if model.njoints == 1:  # Only universe joint
                results['warnings'].append("Model has no movable joints")
            
            if model.nv == 0:
                results['warnings'].append("Model has no degrees of freedom")
            
            # Check joint limits
            joint_limits_ok = True
            for i in range(1, model.njoints):
                upper_lim = model.upperPositionLimit[i - 1]
                lower_lim = model.lowerPositionLimit[i - 1]
                if upper_lim <= lower_lim:
                    results['warnings'].append(
                        f"Invalid joint limits for joint {model.names[i]}"
                    )
                    joint_limits_ok = False
            
            results['info']['joint_limits_valid'] = joint_limits_ok
            
            # Check inertial properties
            inertia_ok = True
            for i in range(1, model.njoints):
                inertia = model.inertias[i]
                if inertia.mass <= 0:
                    results['warnings'].append(
                        f"Non-positive mass for body {model.names[i]}: "
                        f"{inertia.mass}"
                    )
                    inertia_ok = False
            
            results['info']['inertia_valid'] = inertia_ok
            results['valid'] = True
            
            logger.info("✅ URDF validation successful")
            logger.info(f"   - Joints: {model.njoints - 1}")
            logger.info(f"   - DOFs: {model.nv}")
            logger.info(f"   - Bodies: {len(model.names) - 1}")
            
        except Exception as e:
            error_msg = f"Pinocchio validation failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return results
    
    def visualize(self, duration: float = 10.0) -> None:
        """Visualize URDF model using PyBullet."""
        logger.info(f"Visualizing URDF model with PyBullet for {duration}s")
        
        try:
            # Initialize PyBullet
            self.pybullet.connect(self.pybullet.GUI)
            self.pybullet.setGravity(0, 0, -9.81)
            
            # Load ground plane
            self.pybullet.loadURDF("plane.urdf")
            
            # Load robot model
            robot_id = self.pybullet.loadURDF(str(self.model_path))
            
            # Get joint information
            num_joints = self.pybullet.getNumJoints(robot_id)
            logger.info(f"Loaded robot with {num_joints} joints")
            
            # Print joint information
            joint_info = []
            for i in range(num_joints):
                info = self.pybullet.getJointInfo(robot_id, i)
                joint_info.append({
                    'index': i,
                    'name': info[1].decode('utf-8'),
                    'type': info[2],
                    'lower_limit': info[8],
                    'upper_limit': info[9]
                })
                joint_name = info[1].decode('utf-8')
                logger.info(f"   Joint {i}: {joint_name} (type: {info[2]})")
            
            # Animate joints if possible
            start_time = time.time()
            t = 0
            
            while time.time() - start_time < duration:
                # Simple sinusoidal joint motion
                for joint in joint_info:
                    if joint['type'] in [0, 1]:  # Revolute or prismatic
                        upper = joint['upper_limit']
                        lower = joint['lower_limit']
                        joint_range = upper - lower
                        if joint_range > 0:
                            motion_factor = 1 + 0.5 * (1 + t * 0.5)
                            target_pos = (
                                lower + 0.5 * joint_range * motion_factor
                            )
                            self.pybullet.setJointMotorControl2(
                                robot_id, joint['index'],
                                self.pybullet.POSITION_CONTROL,
                                target_pos
                            )
                
                self.pybullet.stepSimulation()
                time.sleep(1. / 240.)  # 240 Hz
                t += 1. / 240.
            
            logger.info("✅ PyBullet visualization completed")
            
        except Exception as e:
            logger.error(f"❌ PyBullet visualization failed: {str(e)}")
        finally:
            try:
                self.pybullet.disconnect()
            except Exception:
                pass


class MJCFValidator(ModelValidator):
    """MJCF model validator using MuJoCo."""
    
    def __init__(self, model_path: str):
        super().__init__(model_path)
        self.model = None
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if MuJoCo is available."""
        try:
            import mujoco
            self.mujoco = mujoco
        except ImportError:
            raise ImportError(
                "MuJoCo is required for MJCF validation. "
                "Install with: pip install mujoco"
            )
    
    def validate(self) -> Dict[str, Any]:
        """Validate MJCF model using MuJoCo."""
        logger.info(f"Validating MJCF model: {self.model_path}")
        
        results = {
            'model_type': 'MJCF',
            'model_path': str(self.model_path),
            'valid': False,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        try:
            # Load model
            self.model = self.mujoco.MjModel.from_xml_path(
                str(self.model_path)
            )
            
            # Extract model information
            results['info'].update({
                'bodies': self.model.nbody,
                'joints': self.model.njnt,
                'dofs': self.model.nv,
                'geoms': self.model.ngeom,
                'sites': self.model.nsite,
                'actuators': self.model.nu,
                'sensors': self.model.nsensor
            })
            
            # Get body names
            body_names = []
            for i in range(self.model.nbody):
                name_start = self.model.name_bodyadr[i]
                name_end = name_start
                while (name_end < len(self.model.names) and
                       self.model.names[name_end] != 0):
                    name_end += 1
                name_bytes = self.model.names[name_start:name_end].tobytes()
                body_name = name_bytes.decode('utf-8')
                body_names.append(body_name)
            
            results['info']['body_names'] = body_names
            
            # Basic validation checks
            if self.model.njnt == 0:
                results['warnings'].append("Model has no joints")
            
            if self.model.nv == 0:
                results['warnings'].append("Model has no degrees of freedom")
            
            if self.model.ngeom == 0:
                results['warnings'].append("Model has no geometries")
            
            # Check for simulation stability
            if self.model.opt.timestep <= 0:
                results['errors'].append("Invalid timestep")
            else:
                results['info']['timestep'] = self.model.opt.timestep
            
            results['valid'] = True
            
            logger.info("✅ MJCF validation successful")
            logger.info(f"   - Bodies: {self.model.nbody}")
            logger.info(f"   - Joints: {self.model.njnt}")
            logger.info(f"   - DOFs: {self.model.nv}")
            logger.info(f"   - Geoms: {self.model.ngeom}")
            
        except Exception as e:
            error_msg = f"MuJoCo validation failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        return results
    
    def visualize(self, duration: float = 10.0) -> None:
        """Visualize MJCF model using MuJoCo viewer."""
        logger.info(f"Visualizing MJCF model with MuJoCo for {duration}s")
        
        try:
            if self.model is None:
                self.model = self.mujoco.MjModel.from_xml_path(
                    str(self.model_path)
                )
            
            # Create data
            data = self.mujoco.MjData(self.model)
            
            # Try to use MuJoCo viewer
            try:
                import mujoco.viewer
                
                with mujoco.viewer.launch_passive(self.model, data) as viewer:
                    start_time = time.time()
                    
                    while time.time() - start_time < duration:
                        # Simple sinusoidal control
                        t = time.time() - start_time
                        
                        # Apply simple joint control if actuators exist
                        if self.model.nu > 0:
                            for i in range(self.model.nu):
                                # Slow motion
                                data.ctrl[i] = 0.5 * (1 + 0.5 * t)
                        
                        # Step simulation
                        self.mujoco.mj_step(self.model, data)
                        viewer.sync()
                        time.sleep(0.01)
                
            except ImportError:
                logger.warning(
                    "MuJoCo viewer not available, running headless simulation"
                )
                
                # Run headless simulation
                start_time = time.time()
                while time.time() - start_time < duration:
                    self.mujoco.mj_step(self.model, data)
                    time.sleep(0.01)
            
            logger.info("✅ MuJoCo visualization completed")
            
        except Exception as e:
            logger.error(f"❌ MuJoCo visualization failed: {str(e)}")


def create_validator(model_path: str) -> ModelValidator:
    """Create appropriate validator based on file extension."""
    path = Path(model_path)
    
    if path.suffix.lower() in ['.urdf']:
        return URDFValidator(model_path)
    elif path.suffix.lower() in ['.xml']:
        return MJCFValidator(model_path)
    else:
        raise ValueError(
            f"Unsupported model format: {path.suffix}. "
            "Supported formats: .urdf, .xml (MJCF)"
        )


def find_models(directory: str) -> List[str]:
    """Find all model files in a directory."""
    models = []
    path = Path(directory)
    
    if path.is_file():
        return [str(path)]
    
    for ext in ['*.urdf', '*.xml']:
        models.extend(path.rglob(ext))
    
    return [str(model) for model in models]


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate and visualize robot models (URDF/MJCF)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s model.urdf                    # Validate and visualize URDF
  %(prog)s model.xml                     # Validate and visualize MJCF
  %(prog)s models/ --validate-only       # Validate all models in directory
  %(prog)s model.urdf --duration 30      # Visualize for 30 seconds
        """
    )
    
    parser.add_argument(
        'path',
        help='Path to model file or directory containing models'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate models, skip visualization'
    )
    
    parser.add_argument(
        '--duration',
        type=float,
        default=10.0,
        help='Visualization duration in seconds (default: 10.0)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Find models
    model_paths = find_models(args.path)
    
    if not model_paths:
        logger.error(f"No model files found in: {args.path}")
        return 1
    
    logger.info(f"Found {len(model_paths)} model(s)")
    
    # Process each model
    results = []
    
    for model_path in model_paths:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing: {model_path}")
        logger.info(f"{'=' * 60}")
        
        try:
            # Create validator
            validator = create_validator(model_path)
            
            # Validate
            result = validator.validate()
            results.append(result)
            
            # Print validation results
            print(f"\n📋 Validation Results for {result['model_type']}:")
            print(f"   Model: {Path(result['model_path']).name}")
            print(f"   Valid: {'✅ Yes' if result['valid'] else '❌ No'}")
            
            if result['errors']:
                print(f"   Errors: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"     - {error}")
            
            if result['warnings']:
                print(f"   Warnings: {len(result['warnings'])}")
                for warning in result['warnings']:
                    print(f"     - {warning}")
            
            if result['info']:
                print(f"   Info:")
                for key, value in result['info'].items():
                    if isinstance(value, list) and len(value) > 5:
                        print(f"     - {key}: {len(value)} items")
                    else:
                        print(f"     - {key}: {value}")
            
            # Visualize if requested and validation successful
            if not args.validate_only and result['valid']:
                print(f"\n🎬 Starting visualization...")
                validator.visualize(args.duration)
            
        except Exception as e:
            logger.error(f"❌ Failed to process {model_path}: {str(e)}")
            results.append({
                'model_path': model_path,
                'valid': False,
                'errors': [str(e)]
            })
    
    # Summary
    valid_count = sum(1 for r in results if r['valid'])
    total_count = len(results)
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total models: {total_count}")
    print(f"Valid models: {valid_count}")
    print(f"Invalid models: {total_count - valid_count}")
    
    if valid_count == total_count:
        print("🎉 All models are valid!")
        return 0
    else:
        print("⚠️  Some models have issues.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
