#!/usr/bin/env python3
"""
MetaQuest VR Configuration and Utilities
Optimized settings for MetaQuest 3/Pro VR headsets
"""

import logging

logger = logging.getLogger(__name__)


class MetaQuestConfig:
    """MetaQuest VR configuration"""
    
    # Network settings
    HOST_IP = "0.0.0.0"  # Listen on all interfaces
    HTTPS_PORT = 8443    # HTTPS port for web interface
    
    # VR sensitivity
    POSITION_SCALE = 0.01  # How much controller movement affects arm position
    ANGLE_SCALE = 4.0      # How much controller rotation affects joint angles
    
    # Control limits
    DELTA_LIMIT = 0.01     # Max position change per frame (meters)
    ANGLE_LIMIT = 8.0      # Max angle change per frame (degrees)
    
    # Joystick settings
    THUMBSTICK_DEADZONE = 0.1  # Thumbstick deadzone
    TRIGGER_THRESHOLD = 0.5    # Trigger activation threshold
    
    # Update rates
    CONTROL_LOOP_RATE = 100    # Hz
    CONTROL_LOOP_DT = 1.0 / CONTROL_LOOP_RATE  # seconds
    
    # Safety limits
    MAX_ARM_SPEED = 1.0         # m/s
    MAX_JOINT_SPEED = 45.0      # degrees/s
    MAX_GRIPPER_FORCE = 100.0   # (unit-dependent)
    
    # Calibration
    VR_X_SCALE = 220.0   # Controller X to robot coordinate scaling
    VR_Y_SCALE = 70.0    # Controller Y to robot coordinate scaling
    VR_Z_SCALE = 70.0    # Controller Z to robot coordinate scaling
    
    # Default arm positions
    DEFAULT_ARM_X = 0.1629  # meters
    DEFAULT_ARM_Y = 0.1131  # meters
    DEFAULT_PITCH = 0.0     # degrees


class MetaQuestControlMode:
    """VR control modes for different scenarios"""
    
    # Control modes
    DELTA_CONTROL = "delta"        # Relative movement (default)
    ABSOLUTE_CONTROL = "absolute"  # Absolute positioning
    GUIDED_CONTROL = "guided"      # AI-assisted movement
    
    # Default mode
    DEFAULT_MODE = DELTA_CONTROL


class MetaQuestButtons:
    """MetaQuest controller button mapping"""
    
    # Right hand controller
    RIGHT_TRIGGER = "trigger"          # Gripper open/close
    RIGHT_GRIP = "grip"                # Alternate gripper
    RIGHT_A_BUTTON = "a"               # Function key 1
    RIGHT_B_BUTTON = "b"               # Function key 2
    RIGHT_THUMBSTICK = "thumbstick"    # Head control / movement
    
    # Left hand controller
    LEFT_TRIGGER = "trigger"           # Gripper open/close
    LEFT_GRIP = "grip"                 # Alternate gripper
    LEFT_X_BUTTON = "x"                # Function key 1
    LEFT_Y_BUTTON = "y"                # Function key 2
    LEFT_THUMBSTICK = "thumbstick"     # Head control / movement
    
    # Headset
    HEADSET_POSITION = "position"      # Headset position tracking
    HEADSET_ORIENTATION = "orientation"  # Headset orientation


class MetaQuestGestureRecognition:
    """Gesture recognition for MetaQuest controllers"""
    
    @staticmethod
    def detect_grip_gesture(controller_data) -> bool:
        """Detect grip gesture"""
        if not controller_data or not hasattr(controller_data, 'metadata'):
            return False
        return controller_data.metadata.get('grip', 0) > 0.5
    
    @staticmethod
    def detect_pinch_gesture(controller_data) -> bool:
        """Detect pinch gesture"""
        if not controller_data or not hasattr(controller_data, 'metadata'):
            return False
        return (controller_data.metadata.get('trigger', 0) > 0.8 and
                controller_data.metadata.get('grip', 0) > 0.5)
    
    @staticmethod
    def detect_point_gesture(controller_data) -> bool:
        """Detect pointing gesture"""
        if not controller_data or not hasattr(controller_data, 'metadata'):
            return False
        return (controller_data.metadata.get('trigger', 0) < 0.2 and
                controller_data.metadata.get('grip', 0) < 0.2)


class MetaQuestCalibration:
    """Calibration utilities for MetaQuest VR"""
    
    @staticmethod
    def calibrate_controller_offset(controller_pos_start, controller_pos_end, 
                                   robot_pos_start, robot_pos_end):
        """
        Calibrate controller to robot position mapping
        
        Args:
            controller_pos_start: Starting VR controller position [x, y, z]
            controller_pos_end: Ending VR controller position [x, y, z]
            robot_pos_start: Starting robot position [x, y, z]
            robot_pos_end: Ending robot position [x, y, z]
            
        Returns:
            tuple: (offset, scale) for position mapping
        """
        controller_delta = [
            controller_pos_end[i] - controller_pos_start[i]
            for i in range(3)
        ]
        robot_delta = [
            robot_pos_end[i] - robot_pos_start[i]
            for i in range(3)
        ]
        
        scale = [
            robot_delta[i] / controller_delta[i] if controller_delta[i] != 0 else 1.0
            for i in range(3)
        ]
        
        return None, scale
    
    @staticmethod
    def calibrate_gripper_range(min_trigger_open, max_trigger_close):
        """
        Calibrate gripper trigger mapping
        
        Args:
            min_trigger_open: Trigger value for fully open gripper
            max_trigger_close: Trigger value for fully closed gripper
            
        Returns:
            tuple: (min_val, max_val) for gripper calibration
        """
        return (min_trigger_open, max_trigger_close)


class MetaQuestSafety:
    """Safety features for MetaQuest VR operation"""
    
    # Safety checks
    ENABLE_COLLISION_DETECTION = True
    ENABLE_JOINT_LIMITS = True
    ENABLE_SPEED_LIMITS = True
    ENABLE_EMERGENCY_STOP = True
    
    # Emergency stop triggers
    EMERGENCY_STOP_BUTTON = "y"  # Y button on left controller
    EMERGENCY_STOP_GESTURE = "pinch"  # Pinch gesture
    
    @staticmethod
    def check_joint_limits(joint_name: str, joint_value: float) -> bool:
        """
        Check if joint value is within safe limits
        
        Args:
            joint_name: Name of the joint
            joint_value: Current joint value (degrees or meters)
            
        Returns:
            bool: True if within limits, False otherwise
        """
        # Define safe limits for each joint
        limits = {
            "shoulder_pan": (-180, 180),
            "shoulder_lift": (-90, 90),
            "elbow_flex": (-180, 180),
            "wrist_flex": (-90, 90),
            "wrist_roll": (-180, 180),
            "gripper": (0, 45),
            "head_motor_1": (-180, 180),
            "head_motor_2": (-90, 90),
        }
        
        if joint_name in limits:
            min_val, max_val = limits[joint_name]
            return min_val <= joint_value <= max_val
        
        return True
    
    @staticmethod
    def clamp_joint_value(joint_name: str, joint_value: float) -> float:
        """
        Clamp joint value to safe limits
        
        Args:
            joint_name: Name of the joint
            joint_value: Desired joint value
            
        Returns:
            float: Clamped joint value
        """
        limits = {
            "shoulder_pan": (-180, 180),
            "shoulder_lift": (-90, 90),
            "elbow_flex": (-180, 180),
            "wrist_flex": (-90, 90),
            "wrist_roll": (-180, 180),
            "gripper": (0, 45),
            "head_motor_1": (-180, 180),
            "head_motor_2": (-90, 90),
        }
        
        if joint_name in limits:
            min_val, max_val = limits[joint_name]
            return max(min_val, min(max_val, joint_value))
        
        return joint_value


def print_metaquest_info():
    """Print MetaQuest VR system information"""
    print("="*60)
    print("🥽 MetaQuest VR Configuration")
    print("="*60)
    print(f"Host IP: {MetaQuestConfig.HOST_IP}")
    print(f"HTTPS Port: {MetaQuestConfig.HTTPS_PORT}")
    print(f"Control Loop Rate: {MetaQuestConfig.CONTROL_LOOP_RATE} Hz")
    print(f"Position Scale: {MetaQuestConfig.POSITION_SCALE}")
    print(f"Angle Scale: {MetaQuestConfig.ANGLE_SCALE}")
    print(f"Control Mode: {MetaQuestControlMode.DEFAULT_MODE}")
    print(f"Safety: {'ENABLED' if MetaQuestSafety.ENABLE_EMERGENCY_STOP else 'DISABLED'}")
    print("="*60)


if __name__ == "__main__":
    print_metaquest_info()
