#!/usr/bin/env python3
"""
XLerobot VR Control - Integrated VR Teleoperation System
Controls XLerobot dual-arm robot using MetaQuest VR headset

Features:
- Real-time VR controller tracking
- Dual-arm inverse kinematics control
- Head and base movement
- Gripper control via VR triggers
- Thread-safe operation

Usage:
    uv run python3 xlerobot_vr_control.py
"""

import asyncio
import logging
import math
import os
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# Third-party imports
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# XLeVR path configuration
XLEVR_PATH = "/home/choyunsang/XLeRobot/XLeVR"


def setup_xlevr_environment():
    """Setup XLeVR environment"""
    if XLEVR_PATH not in sys.path:
        sys.path.insert(0, XLEVR_PATH)
    os.chdir(XLEVR_PATH)
    os.environ['PYTHONPATH'] = f"{XLEVR_PATH}:{os.environ.get('PYTHONPATH', '')}"


def import_xlevr_modules():
    """Import XLeVR modules"""
    try:
        from xlevr.config import XLeVRConfig
        from xlevr.inputs.vr_ws_server import VRWebSocketServer
        from xlevr.inputs.base import ControlGoal, ControlMode
        return XLeVRConfig, VRWebSocketServer, ControlGoal, ControlMode
    except ImportError as e:
        logger.error(f"Failed to import XLeVR modules: {e}")
        logger.error(f"XLeVR path: {XLEVR_PATH}")
        return None, None, None, None


# Joint mapping configurations
LEFT_JOINT_MAP = {
    "shoulder_pan": "left_arm_shoulder_pan",
    "shoulder_lift": "left_arm_shoulder_lift",
    "elbow_flex": "left_arm_elbow_flex",
    "wrist_flex": "left_arm_wrist_flex",
    "wrist_roll": "left_arm_wrist_roll",
    "gripper": "left_arm_gripper",
}

RIGHT_JOINT_MAP = {
    "shoulder_pan": "right_arm_shoulder_pan",
    "shoulder_lift": "right_arm_shoulder_lift",
    "elbow_flex": "right_arm_elbow_flex",
    "wrist_flex": "right_arm_wrist_flex",
    "wrist_roll": "right_arm_wrist_roll",
    "gripper": "right_arm_gripper",
}

HEAD_MOTOR_MAP = {
    "head_motor_1": "head_motor_1",
    "head_motor_2": "head_motor_2",
}


class VRControlMonitor:
    """Integrated VR monitor and controller manager"""
    
    def __init__(self):
        self.config = None
        self.vr_server = None
        self.is_running = False
        self.left_goal = None
        self.right_goal = None
        self.headset_goal = None
        self._goal_lock = threading.Lock()
        self.command_queue = None
        
    def initialize(self):
        """Initialize VR monitor"""
        logger.info("🔧 Initializing VR Control Monitor...")
        
        setup_xlevr_environment()
        
        XLeVRConfig, VRWebSocketServer, ControlGoal, ControlMode = import_xlevr_modules()
        if XLeVRConfig is None:
            logger.error("❌ Failed to import XLeVR modules")
            return False
        
        self.config = XLeVRConfig()
        self.config.enable_vr = True
        self.config.enable_keyboard = False
        self.command_queue = asyncio.Queue()
        
        try:
            self.vr_server = VRWebSocketServer(
                command_queue=self.command_queue,
                config=self.config,
                print_only=False
            )
            logger.info("✅ VR Control Monitor initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create VR WebSocket server: {e}")
            return False
    
    async def start_monitoring(self):
        """Start VR monitoring"""
        try:
            await self.vr_server.start()
            self.is_running = True
            logger.info("✅ VR Monitor is running")
            
            await self.monitor_commands()
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping VR monitor...")
        except Exception as e:
            logger.error(f"❌ Error in VR monitor: {e}")
        finally:
            await self.stop_monitoring()
    
    async def monitor_commands(self):
        """Monitor commands from VR controllers"""
        while self.is_running:
            try:
                goal = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
                
                with self._goal_lock:
                    if goal.arm == "left":
                        self.left_goal = goal
                    elif goal.arm == "right":
                        self.right_goal = goal
                    elif goal.arm == "headset":
                        self.headset_goal = goal
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ Error processing command: {e}")
    
    def get_latest_goal_nowait(self, arm=None):
        """Get latest VR goal"""
        with self._goal_lock:
            if arm == "left":
                return self.left_goal
            elif arm == "right":
                return self.right_goal
            elif arm == "headset":
                return self.headset_goal
            else:
                return {
                    "left": self.left_goal,
                    "right": self.right_goal,
                    "headset": self.headset_goal,
                }
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        if self.vr_server:
            await self.vr_server.stop()
        logger.info("✅ VR Monitor stopped")


class SimpleTeleopArm:
    """Robot arm control with VR input"""
    
    def __init__(self, joint_map, initial_obs, kinematics, prefix="right", kp=1):
        self.joint_map = joint_map
        self.prefix = prefix
        self.kp = kp
        self.kinematics = kinematics
        
        # Initial joint positions
        self.joint_positions = {
            "shoulder_pan": initial_obs.get(f"{prefix}_arm_shoulder_pan.pos", 0.0),
            "shoulder_lift": initial_obs.get(f"{prefix}_arm_shoulder_lift.pos", 0.0),
            "elbow_flex": initial_obs.get(f"{prefix}_arm_elbow_flex.pos", 0.0),
            "wrist_flex": initial_obs.get(f"{prefix}_arm_wrist_flex.pos", 0.0),
            "wrist_roll": initial_obs.get(f"{prefix}_arm_wrist_roll.pos", 0.0),
            "gripper": initial_obs.get(f"{prefix}_arm_gripper.pos", 0.0),
        }
        
        # End-effector tracking
        self.current_x = 0.1629
        self.current_y = 0.1131
        self.pitch = 0.0
        
        # VR state tracking
        self.last_vr_time = 0.0
        self.prev_vr_pos = None
        self.prev_wrist_flex = None
        self.prev_wrist_roll = None
        
        # Control parameters
        self.vr_deadzone = 0.001
        self.max_delta_per_frame = 0.005
        self.degree_step = 2
        self.xy_step = 0.005
        
        # Target positions
        self.target_positions = {
            "shoulder_pan": 0.0,
            "shoulder_lift": 0.0,
            "elbow_flex": 0.0,
            "wrist_flex": 0.0,
            "wrist_roll": 0.0,
            "gripper": 0.0,
        }
        
        self.zero_pos = {
            'shoulder_pan': 0.0,
            'shoulder_lift': 0.0,
            'elbow_flex': 0.0,
            'wrist_flex': 0.0,
            'wrist_roll': 0.0,
            'gripper': 0.0
        }

    def move_to_zero_position(self, robot):
        """Move arm to zero position"""
        logger.info(f"[{self.prefix}] Moving to Zero Position...")
        self.target_positions = self.zero_pos.copy()
        self.current_x = 0.1629
        self.current_y = 0.1131
        self.pitch = 0.0
        self.last_vr_time = 0.0
        
        action = self.p_control_action(robot)
        robot.send_action(action)

    def handle_vr_input(self, vr_goal, gripper_state=None):
        """Handle VR input with delta action control"""
        if vr_goal is None:
            return
        
        if not hasattr(vr_goal, 'target_position') or vr_goal.target_position is None:
            return
        
        # Get current VR position
        current_vr_pos = vr_goal.target_position
        
        # Initialize previous VR position
        if self.prev_vr_pos is None:
            self.prev_vr_pos = current_vr_pos
            return
        
        # Calculate relative change (delta)
        vr_x = (current_vr_pos[0] - self.prev_vr_pos[0]) * 220
        vr_y = (current_vr_pos[1] - self.prev_vr_pos[1]) * 70
        vr_z = (current_vr_pos[2] - self.prev_vr_pos[2]) * 70
        
        # Update previous position
        self.prev_vr_pos = current_vr_pos
        
        # Delta control parameters
        pos_scale = 0.01
        angle_scale = 4.0
        delta_limit = 0.01
        angle_limit = 8.0
        
        delta_x = max(-delta_limit, min(delta_limit, vr_x * pos_scale))
        delta_y = max(-delta_limit, min(delta_limit, vr_y * pos_scale))
        delta_z = max(-delta_limit, min(delta_limit, vr_z * pos_scale))
        
        self.current_x += -delta_z
        self.current_y += delta_y
        
        # Handle wrist angles
        if hasattr(vr_goal, 'wrist_flex_deg') and vr_goal.wrist_flex_deg is not None:
            if self.prev_wrist_flex is None:
                self.prev_wrist_flex = vr_goal.wrist_flex_deg
                return
            
            delta_pitch = (vr_goal.wrist_flex_deg - self.prev_wrist_flex) * angle_scale
            delta_pitch = max(-angle_limit, min(angle_limit, delta_pitch))
            self.pitch += delta_pitch
            self.pitch = max(-90, min(90, self.pitch))
            self.prev_wrist_flex = vr_goal.wrist_flex_deg
        
        if hasattr(vr_goal, 'wrist_roll_deg') and vr_goal.wrist_roll_deg is not None:
            if self.prev_wrist_roll is None:
                self.prev_wrist_roll = vr_goal.wrist_roll_deg
                return
            
            delta_roll = (vr_goal.wrist_roll_deg - self.prev_wrist_roll) * angle_scale
            delta_roll = max(-angle_limit, min(angle_limit, delta_roll))
            
            current_roll = self.target_positions.get("wrist_roll", 0.0)
            new_roll = current_roll + delta_roll
            new_roll = max(-90, min(90, new_roll))
            self.target_positions["wrist_roll"] = new_roll
            
            self.prev_wrist_roll = vr_goal.wrist_roll_deg
        
        # Handle shoulder_pan with delta control
        if abs(delta_x) > 0.001:
            x_scale = 200.0
            delta_pan = delta_x * x_scale
            delta_pan = max(-angle_limit, min(angle_limit, delta_pan))
            current_pan = self.target_positions.get("shoulder_pan", 0.0)
            new_pan = current_pan + delta_pan
            new_pan = max(-180, min(180, new_pan))
            self.target_positions["shoulder_pan"] = new_pan
        
        # Inverse kinematics
        try:
            joint2_target, joint3_target = self.kinematics.inverse_kinematics(
                self.current_x, self.current_y
            )
            alpha = 0.1
            self.target_positions["shoulder_lift"] = (
                (1 - alpha) * self.target_positions.get("shoulder_lift", 0.0) + 
                alpha * joint2_target
            )
            self.target_positions["elbow_flex"] = (
                (1 - alpha) * self.target_positions.get("elbow_flex", 0.0) + 
                alpha * joint3_target
            )
        except Exception as e:
            logger.debug(f"[{self.prefix}] VR IK failed: {e}")
        
        # Calculate wrist_flex for end-effector orientation
        self.target_positions["wrist_flex"] = (
            -self.target_positions["shoulder_lift"] - 
            self.target_positions["elbow_flex"] + 
            self.pitch
        )
        
        # Handle gripper
        if hasattr(vr_goal, 'metadata') and vr_goal.metadata.get('trigger', 0) > 0.5:
            self.target_positions["gripper"] = 45
        else:
            self.target_positions["gripper"] = 0.0

    def p_control_action(self, robot):
        """Generate proportional control action"""
        obs = robot.get_observation()
        action = {}
        
        for j in self.target_positions:
            current_key = f"{self.prefix}_arm_{j}.pos"
            current = obs.get(current_key, 0.0)
            error = self.target_positions[j] - current
            control = self.kp * error
            action[f"{self.joint_map[j]}.pos"] = current + control
        
        return action


class SimpleHeadControl:
    """Robot head control with VR input"""
    
    def __init__(self, initial_obs, kp=1):
        self.kp = kp
        self.degree_step = 2
        
        self.target_positions = {
            "head_motor_1": initial_obs.get("head_motor_1.pos", 0.0),
            "head_motor_2": initial_obs.get("head_motor_2.pos", 0.0),
        }
        
        self.zero_pos = {"head_motor_1": 0.0, "head_motor_2": 0.0}

    def handle_vr_input(self, vr_goal):
        """Handle VR input for head control"""
        if vr_goal is None or not hasattr(vr_goal, 'metadata'):
            return
        
        thumb = vr_goal.metadata.get('thumbstick', {})
        if not thumb:
            return
        
        thumb_x = thumb.get('x', 0)
        thumb_y = thumb.get('y', 0)
        
        if abs(thumb_x) > 0.1:
            if thumb_x > 0:
                self.target_positions["head_motor_1"] += self.degree_step
            else:
                self.target_positions["head_motor_1"] -= self.degree_step
        
        if abs(thumb_y) > 0.1:
            if thumb_y > 0:
                self.target_positions["head_motor_2"] += self.degree_step
            else:
                self.target_positions["head_motor_2"] -= self.degree_step

    def move_to_zero_position(self, robot):
        """Move head to zero position"""
        logger.info("[HEAD] Moving to Zero Position...")
        self.target_positions = self.zero_pos.copy()
        action = self.p_control_action(robot)
        robot.send_action(action)

    def p_control_action(self, robot):
        """Generate proportional control action for head motors"""
        obs = robot.get_observation()
        action = {}
        
        for motor in self.target_positions:
            current_key = f"{HEAD_MOTOR_MAP[motor]}.pos"
            current = obs.get(current_key, 0.0)
            error = self.target_positions[motor] - current
            control = self.kp * error
            action[f"{HEAD_MOTOR_MAP[motor]}.pos"] = current + control
        
        return action


async def main():
    """Main VR control loop - Right Arm Only"""
    logger.info("="*60)
    logger.info("🚀 XLerobot VR Control System")
    logger.info("MetaQuest VR Teleoperation")
    logger.info("="*60)
    
    # Import XLerobot modules
    try:
        from lerobot.robots.xlerobot import XLerobotConfig, XLerobot
        from lerobot.model.SO101Robot import SO101Kinematics
    except ImportError as e:
        logger.error(f"❌ Failed to import LeRobot modules: {e}")
        logger.error("Please ensure LeRobot is installed: uv sync --locked --extra all")
        return
    
    # Initialize VR monitor
    logger.info("🔧 Initializing VR Control Monitor...")
    vr_monitor = VRControlMonitor()
    if not vr_monitor.initialize():
        logger.error("❌ VR monitor initialization failed")
        return
    
    # Start VR monitoring in background thread
    vr_thread = threading.Thread(
        target=lambda: asyncio.run(vr_monitor.start_monitoring()),
        daemon=True
    )
    vr_thread.start()
    logger.info("✅ VR monitoring thread started")
    
    try:
        # Connect to robot
        logger.info("🤖 Connecting to XLerobot...")
        robot_config = XLerobotConfig()
        robot = XLerobot(robot_config)
        
        try:
            robot.connect()
            logger.info("✅ Successfully connected to robot")
            if robot.is_calibrated:
                logger.info("✅ Robot is calibrated and ready")
            else:
                logger.warning("⚠️  Robot requires calibration")
        except Exception as e:
            logger.error(f"❌ Failed to connect to robot: {e}")
            return
        
        # Initialize arm and head controllers
        logger.info("⚙️  Initializing controllers (Right Arm Only)...")
        obs = robot.get_observation()
        
        kin_right = SO101Kinematics()
        
        right_arm = SimpleTeleopArm(RIGHT_JOINT_MAP, obs, kin_right, prefix="right")
        head_control = SimpleHeadControl(obs)
        
        # Move to zero position
        logger.info("🎯 Moving to zero position...")
        right_arm.move_to_zero_position(robot)
        head_control.move_to_zero_position(robot)
        
        logger.info("="*60)
        logger.info("📱 Connect your MetaQuest VR headset")
        logger.info("Press ESC to exit")
        logger.info("="*60)
        
        # Main VR control loop
        try:
            while True:
                # Get VR data
                dual_goals = vr_monitor.get_latest_goal_nowait()
                
                if dual_goals is None or (
                    dual_goals.get("left") is None and 
                    dual_goals.get("right") is None
                ):
                    await asyncio.sleep(0.01)
                    continue
                
                right_goal = dual_goals.get("right")
                headset_goal = dual_goals.get("headset")
                
                # Handle VR input (Right Arm Only)
                right_arm.handle_vr_input(right_goal)
                
                if headset_goal:
                    head_control.handle_vr_input(headset_goal)
                
                # Generate actions
                right_action = right_arm.p_control_action(robot)
                head_action = head_control.p_control_action(robot)
                
                # Merge and send actions
                action = {**right_action, **head_action}
                robot.send_action(action)
                
                await asyncio.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("🛑 Exit signal received")
        
        finally:
            robot.disconnect()
            logger.info("✅ Robot disconnected")
        
    except Exception as e:
        logger.error(f"❌ Program execution failed: {e}")
        traceback.print_exc()
    
    finally:
        vr_monitor.is_running = False
        logger.info("👋 XLerobot VR Control System stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 System stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        traceback.print_exc()
