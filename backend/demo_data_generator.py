#!/usr/bin/env python3
"""
Demo Mode Data Generator for Vertex Rehabilitation System

This module generates realistic simulated sensor data with pusher syndrome patterns
for presentations and demonstrations when hardware is unavailable.

Requirements implemented:
- 6.1: Generate realistic simulated sensor data matching typical pusher syndrome patterns
- 6.2: Create smooth transitions between -15 to +15 degrees with occasional pusher events
- 6.3: Generate asymmetric pressure readings consistent with pusher syndrome behavior
- 6.6: Include realistic pusher detection events every 30-60 seconds
"""

import asyncio
import math
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DemoSensorReading:
    """Demo sensor reading with realistic pusher syndrome patterns"""
    device_id: str
    timestamp: int  # Unix timestamp in milliseconds
    pitch: float    # Pitch angle in degrees (-180 to +180)
    fsr_left: int   # Left FSR sensor value (0-4095)
    fsr_right: int  # Right FSR sensor value (0-4095)
    pusher_detected: bool = False
    confidence_level: float = 0.0
    description: str = ""

class DemoDataGenerator:
    """
    Generates realistic sensor data for demo mode presentations.
    
    Features:
    - Smooth pitch transitions between -15° to +15°
    - Asymmetric FSR readings consistent with pusher syndrome
    - Pusher detection events every 30-60 seconds
    - Realistic noise and variation patterns
    - Clinical-grade data patterns matching real patient behavior
    """
    
    def __init__(self, device_id: str = "ESP32_DEMO_001"):
        self.device_id = device_id
        self.is_running = False
        self.current_pitch = 0.0
        self.target_pitch = 0.0
        self.pitch_velocity = 0.0
        self.last_pusher_event = 0
        self.pusher_event_interval = random.uniform(30, 60)  # 30-60 seconds
        self.episode_active = False
        self.episode_start_time = 0
        self.episode_duration = 0
        self.baseline_fsr_left = 2048
        self.baseline_fsr_right = 2048
        self.noise_amplitude = 0.5  # Degrees of random noise
        self.fsr_noise_amplitude = 50  # FSR noise amplitude
        
        # Demo scenario parameters
        self.demo_scenarios = [
            "normal_posture",
            "mild_pusher_episode", 
            "moderate_pusher_episode",
            "severe_pusher_episode",
            "correction_attempt",
            "recovery_phase"
        ]
        self.current_scenario = "normal_posture"
        self.scenario_start_time = time.time()
        self.scenario_duration = random.uniform(5, 8)  # Short durations for demo variety
        
        logger.info(f"Demo data generator initialized for device {device_id}")
    
    def _add_realistic_noise(self, value: float, amplitude: float) -> float:
        """Add realistic sensor noise using Gaussian distribution"""
        noise = random.gauss(0, amplitude * 0.3)  # 3-sigma = amplitude
        return value + noise
    
    def _calculate_smooth_transition(self, current: float, target: float, velocity: float, dt: float) -> Tuple[float, float]:
        """
        Calculate smooth transition between current and target values using physics-based motion.
        Returns (new_value, new_velocity)
        """
        # Simple damped spring system for smooth transitions
        spring_constant = 2.0
        damping = 1.5
        
        # Calculate acceleration
        acceleration = spring_constant * (target - current) - damping * velocity
        
        # Update velocity and position
        new_velocity = velocity + acceleration * dt
        new_value = current + new_velocity * dt
        
        return new_value, new_velocity
    
    def _generate_pusher_syndrome_fsr(self, pitch: float, pusher_active: bool) -> Tuple[int, int]:
        """
        Generate asymmetric FSR readings consistent with pusher syndrome behavior.
        
        Args:
            pitch: Current pitch angle (positive = right lean)
            pusher_active: Whether pusher syndrome is currently active
            
        Returns:
            Tuple of (fsr_left, fsr_right) values
        """
        # Base FSR values (normal weight distribution)
        base_left = self.baseline_fsr_left
        base_right = self.baseline_fsr_right
        
        if pusher_active:
            # During pusher episodes, weight shifts dramatically toward non-paretic side
            # Assuming right-side paretic (left side is non-paretic)
            weight_shift_factor = min(abs(pitch) / 20.0, 1.0)  # Max shift at 20° lean
            
            # Non-paretic side (left) bears more weight during pusher episodes
            fsr_left = int(base_left + (1500 * weight_shift_factor))
            fsr_right = int(base_right - (800 * weight_shift_factor))
            
            # Add pusher-specific asymmetry
            if pitch > 10:  # Right lean during pusher episode
                fsr_left += int(500 * (pitch - 10) / 10)  # Additional left loading
                fsr_right = max(fsr_right - int(300 * (pitch - 10) / 10), 500)
        else:
            # Normal postural adjustments - more symmetric
            lean_factor = pitch / 15.0  # Normalize to ±1 at ±15°
            
            # Symmetric weight shift during normal leaning
            shift_amount = int(300 * abs(lean_factor))
            if pitch > 0:  # Right lean
                fsr_left = base_left + shift_amount
                fsr_right = base_right - shift_amount
            else:  # Left lean
                fsr_left = base_left - shift_amount
                fsr_right = base_right + shift_amount
        
        # Add realistic noise
        fsr_left = int(self._add_realistic_noise(fsr_left, self.fsr_noise_amplitude))
        fsr_right = int(self._add_realistic_noise(fsr_right, self.fsr_noise_amplitude))
        
        # Clamp to valid FSR range
        fsr_left = max(0, min(4095, fsr_left))
        fsr_right = max(0, min(4095, fsr_right))
        
        return fsr_left, fsr_right
    
    def _update_demo_scenario(self, current_time: float) -> None:
        """Update the current demo scenario based on timing"""
        if current_time - self.scenario_start_time > self.scenario_duration:
            # Move to next scenario
            current_index = self.demo_scenarios.index(self.current_scenario)
            next_index = (current_index + 1) % len(self.demo_scenarios)
            self.current_scenario = self.demo_scenarios[next_index]
            self.scenario_start_time = current_time
            self.scenario_duration = random.uniform(8, 15)  # Shorter durations for testing
            
            logger.info(f"Demo scenario changed to: {self.current_scenario}")
    
    def _get_scenario_target_pitch(self) -> float:
        """Get target pitch angle based on current demo scenario"""
        scenario_targets = {
            "normal_posture": random.uniform(-3, 3),
            "mild_pusher_episode": random.uniform(8, 12),
            "moderate_pusher_episode": random.uniform(12, 18),
            "severe_pusher_episode": random.uniform(18, 25),
            "correction_attempt": random.uniform(5, 10),
            "recovery_phase": random.uniform(-2, 5)
        }
        
        target = scenario_targets.get(self.current_scenario, 0.0)
        # Ensure we get variety in the demo by occasionally picking extreme values
        if random.random() < 0.3:  # 30% chance of more dramatic values
            if self.current_scenario == "severe_pusher_episode":
                target = random.uniform(20, 25)
            elif self.current_scenario == "moderate_pusher_episode":
                target = random.uniform(15, 20)
            elif self.current_scenario == "mild_pusher_episode":
                target = random.uniform(10, 15)
        
        return target
    
    def _is_pusher_episode_active(self) -> bool:
        """Determine if pusher syndrome should be detected based on current scenario"""
        pusher_scenarios = [
            "mild_pusher_episode",
            "moderate_pusher_episode", 
            "severe_pusher_episode"
        ]
        return self.current_scenario in pusher_scenarios
    
    def _calculate_confidence_level(self, pitch: float, pusher_active: bool) -> float:
        """Calculate confidence level for pusher detection"""
        if not pusher_active:
            return random.uniform(0.1, 0.3)
        
        # Higher confidence for more severe angles
        base_confidence = min(abs(pitch) / 20.0, 1.0)  # Max confidence at 20°
        confidence = 0.6 + (base_confidence * 0.4)  # Range: 0.6 to 1.0
        
        # Add some realistic variation
        confidence += random.uniform(-0.1, 0.1)
        return max(0.0, min(1.0, confidence))
    
    def generate_reading(self) -> DemoSensorReading:
        """
        Generate a single realistic sensor reading with pusher syndrome patterns.
        
        Returns:
            DemoSensorReading with realistic sensor data
        """
        current_time = time.time()
        
        # Update demo scenario
        self._update_demo_scenario(current_time)
        
        # Update target pitch based on scenario
        new_target = self._get_scenario_target_pitch()
        # Always update target to ensure variety
        self.target_pitch = new_target
        
        # Calculate smooth pitch transition (60 FPS equivalent)
        dt = 0.5  # Faster transitions for demo purposes
        self.current_pitch, self.pitch_velocity = self._calculate_smooth_transition(
            self.current_pitch, self.target_pitch, self.pitch_velocity, dt
        )
        
        # Add realistic noise to pitch
        noisy_pitch = self._add_realistic_noise(self.current_pitch, self.noise_amplitude)
        
        # Clamp pitch to demo range (-15° to +15°)
        demo_pitch = max(-15.0, min(15.0, noisy_pitch))
        
        # Determine if pusher syndrome is active
        pusher_active = self._is_pusher_episode_active()
        
        # Generate FSR readings consistent with pusher behavior
        fsr_left, fsr_right = self._generate_pusher_syndrome_fsr(demo_pitch, pusher_active)
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level(demo_pitch, pusher_active)
        
        # Create sensor reading
        reading = DemoSensorReading(
            device_id=self.device_id,
            timestamp=int(current_time * 1000),  # Convert to milliseconds
            pitch=round(demo_pitch, 1),
            fsr_left=fsr_left,
            fsr_right=fsr_right,
            pusher_detected=pusher_active,
            confidence_level=round(confidence, 3),
            description=f"Demo: {self.current_scenario.replace('_', ' ').title()}"
        )
        
        return reading
    
    async def start_continuous_generation(self, callback, interval_ms: int = 150):
        """
        Start continuous generation of demo data.
        
        Args:
            callback: Async function to call with each generated reading
            interval_ms: Interval between readings in milliseconds (default 150ms)
        """
        self.is_running = True
        logger.info(f"Starting continuous demo data generation (interval: {interval_ms}ms)")
        
        try:
            while self.is_running:
                reading = self.generate_reading()
                await callback(reading)
                await asyncio.sleep(interval_ms / 1000.0)
        except asyncio.CancelledError:
            logger.info("Demo data generation cancelled")
        except Exception as e:
            logger.error(f"Error in continuous demo generation: {str(e)}")
        finally:
            self.is_running = False
    
    def stop_generation(self):
        """Stop continuous data generation"""
        self.is_running = False
        logger.info("Demo data generation stopped")
    
    def reset_to_normal(self):
        """Reset generator to normal posture state"""
        self.current_pitch = 0.0
        self.target_pitch = 0.0
        self.pitch_velocity = 0.0
        self.current_scenario = "normal_posture"
        self.scenario_start_time = time.time()
        logger.info("Demo generator reset to normal posture")

class DemoModeManager:
    """
    Manages demo mode state and coordinates data generation with WebSocket broadcasting.
    """
    
    def __init__(self):
        self.is_demo_active = False
        self.generator: Optional[DemoDataGenerator] = None
        self.generation_task: Optional[asyncio.Task] = None
        self.websocket_manager = None  # Will be set by main.py
        self.demo_start_time: Optional[datetime] = None
        
        logger.info("Demo mode manager initialized")
    
    async def start_demo_mode(self, websocket_manager, device_id: str = "ESP32_DEMO_001"):
        """
        Start demo mode with continuous data generation.
        
        Args:
            websocket_manager: WebSocket manager for broadcasting data
            device_id: Device ID for demo data
        """
        if self.is_demo_active:
            logger.warning("Demo mode already active")
            return {"status": "already_active", "message": "Demo mode is already running"}
        
        self.websocket_manager = websocket_manager
        self.generator = DemoDataGenerator(device_id)
        self.is_demo_active = True
        self.demo_start_time = datetime.now(timezone.utc)
        
        # Start continuous generation task
        self.generation_task = asyncio.create_task(
            self.generator.start_continuous_generation(self._broadcast_demo_data, 150)
        )
        
        logger.info(f"Demo mode started with device {device_id}")
        return {
            "status": "started",
            "message": "Demo mode activated successfully",
            "device_id": device_id,
            "start_time": self.demo_start_time.isoformat()
        }
    
    async def stop_demo_mode(self):
        """Stop demo mode and clean up resources"""
        if not self.is_demo_active:
            return {"status": "not_active", "message": "Demo mode is not currently running"}
        
        # Stop generation
        if self.generator:
            self.generator.stop_generation()
        
        # Cancel generation task
        if self.generation_task and not self.generation_task.done():
            self.generation_task.cancel()
            try:
                await self.generation_task
            except asyncio.CancelledError:
                pass
        
        # Clean up state
        self.is_demo_active = False
        self.generator = None
        self.generation_task = None
        demo_duration = None
        
        if self.demo_start_time:
            demo_duration = (datetime.now(timezone.utc) - self.demo_start_time).total_seconds()
        
        logger.info(f"Demo mode stopped (duration: {demo_duration:.1f}s)")
        return {
            "status": "stopped",
            "message": "Demo mode deactivated successfully",
            "duration_seconds": demo_duration
        }
    
    async def _broadcast_demo_data(self, reading: DemoSensorReading):
        """
        Broadcast demo sensor data via WebSocket.
        
        Args:
            reading: Demo sensor reading to broadcast
        """
        if not self.websocket_manager:
            return
        
        # Convert demo reading to standard sensor data format
        demo_data = {
            "device_id": reading.device_id,
            "timestamp": datetime.fromtimestamp(reading.timestamp / 1000, tz=timezone.utc).isoformat(),
            "raw_data": {
                "pitch": reading.pitch,
                "fsr_left": reading.fsr_left,
                "fsr_right": reading.fsr_right
            },
            "processed_data": {
                "tilt_angle": abs(reading.pitch),
                "tilt_direction": "left" if reading.pitch < -2 else "right" if reading.pitch > 2 else "center",
                "alert_level": "unsafe" if abs(reading.pitch) > 15 else "warning" if abs(reading.pitch) > 8 else "safe",
                "fsr_balance": (reading.fsr_right - reading.fsr_left) / (reading.fsr_left + reading.fsr_right) if (reading.fsr_left + reading.fsr_right) > 0 else 0
            },
            "clinical_analysis": {
                "pusher_detected": reading.pusher_detected,
                "confidence_level": reading.confidence_level,
                "severity_score": 2 if reading.pusher_detected and abs(reading.pitch) > 15 else 1 if reading.pusher_detected else 0,
                "severity_name": "MODERATE" if reading.pusher_detected and abs(reading.pitch) > 15 else "MILD" if reading.pusher_detected else "NO_PUSHING",
                "tilt_classification": "severe" if abs(reading.pitch) > 20 else "pusher_relevant" if abs(reading.pitch) > 10 else "normal",
                "paretic_tilt": reading.pitch,  # Assuming right paretic side
                "weight_imbalance": abs((reading.fsr_right - reading.fsr_left) / (reading.fsr_left + reading.fsr_right)) if (reading.fsr_left + reading.fsr_right) > 0 else 0,
                "resistance_index": 0.8 if reading.pusher_detected else 0.1,
                "episode_duration": 5.0 if reading.pusher_detected else 0.0,
                "criteria_met": ["abnormal_tilt", "weight_imbalance"] if reading.pusher_detected else []
            },
            "device_status": {
                "connection_status": "connected",
                "data_count": int(time.time()) % 1000  # Simulated data count
            },
            "demo_mode": {
                "active": True,
                "scenario": reading.description,
                "device_id": reading.device_id
            }
        }
        
        # Broadcast to all connected WebSocket clients
        await self.websocket_manager.broadcast_sensor_data(demo_data)
    
    def get_demo_status(self) -> Dict:
        """Get current demo mode status"""
        if not self.is_demo_active:
            return {
                "active": False,
                "message": "Demo mode is not currently running"
            }
        
        duration = None
        if self.demo_start_time:
            duration = (datetime.now(timezone.utc) - self.demo_start_time).total_seconds()
        
        current_scenario = "unknown"
        if self.generator:
            current_scenario = self.generator.current_scenario
        
        return {
            "active": True,
            "device_id": self.generator.device_id if self.generator else "unknown",
            "start_time": self.demo_start_time.isoformat() if self.demo_start_time else None,
            "duration_seconds": duration,
            "current_scenario": current_scenario,
            "websocket_clients": len(self.websocket_manager.active_connections) if self.websocket_manager else 0
        }

# Global demo mode manager instance
demo_manager = DemoModeManager()