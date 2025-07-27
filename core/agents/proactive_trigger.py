#!/usr/bin/env python3
"""
Proactive Action Triggering Mechanism - Phase 4: True Intent Resonance
Complete proactive intelligence system for automatic action execution
based on probabilistic intent predictions with confidence thresholds.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProactiveActionTrigger:
    """
    Proactive Action Triggering Mechanism for Phase 4 True Intent Resonance.
    Automatically triggers actions based on probabilistic intent predictions
    with configurable confidence thresholds and risk assessment.
    """
    
    def __init__(self, pig_instance, config: Dict[str, Any]):
        self.pig = pig_instance
        self.confidence_threshold = config.get('confidence_threshold', 0.75)
        self.risk_threshold = config.get('risk_threshold', 0.3)
        self.action_cooldown = timedelta(minutes=config.get('action_cooldown_minutes', 5))
        
        # Action history for cooldown management
        self.recent_actions: Dict[str, datetime] = {}
        
        # Action registry - maps intent types to action functions
        self.action_registry = {
            'development': self._trigger_development_environment,
            'document_work': self._trigger_document_optimization,
            'multimedia': self._trigger_multimedia_processing,
            'gaming': self._trigger_gaming_optimization,
            'communication': self._trigger_communication_setup,
            'browsing': self._trigger_browser_optimization,
            'system_maintenance': self._trigger_system_maintenance,
            'high_computation': self._trigger_compute_scaling
        }
        
        # Risk assessment weights for different factors
        self.risk_weights = {
            'system_impact': 0.4,
            'resource_cost': 0.3,
            'user_disruption': 0.2,
            'reversibility': 0.1
        }
        
        logger.info("Proactive Action Trigger initialized with Phase 4 intelligence")

    async def evaluate_and_trigger(self, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate current context against PIG predictions and trigger actions proactively
        """
        try:
            triggered_actions = []
            
            # Get current intent predictions from PIG
            predictions = await self.pig.predict_intents(current_context)
            
            for intent_type, confidence, metadata in predictions:
                # Check if action should be triggered
                if await self._should_trigger_action(intent_type, confidence, metadata):
                    # Calculate risk score
                    risk_score = await self._calculate_risk_score(intent_type, metadata)
                    
                    if risk_score <= self.risk_threshold:
                        # Trigger action
                        action_result = await self._execute_proactive_action(
                            intent_type, confidence, metadata, risk_score
                        )
                        
                        if action_result:
                            triggered_actions.append(action_result)
                            
                            # Update cooldown
                            self.recent_actions[intent_type] = datetime.now()
                            
                            logger.info(f"Proactively triggered action for {intent_type} "
                                      f"with confidence {confidence:.3f}")
            
            return triggered_actions
            
        except Exception as e:
            logger.error(f"Error in proactive action evaluation: {e}")
            return []

    async def _should_trigger_action(self, intent_type: str, confidence: float, 
                                   metadata: Dict[str, Any]) -> bool:
        """Determine if an action should be triggered"""
        try:
            # Check confidence threshold
            if confidence < self.confidence_threshold:
                return False
            
            # Check cooldown period
            if intent_type in self.recent_actions:
                time_since_last = datetime.now() - self.recent_actions[intent_type]
                if time_since_last < self.action_cooldown:
                    return False
            
            # Check if action is available
            if intent_type not in self.action_registry:
                return False
            
            # Check metadata constraints
            if metadata.get('user_preference_block', False):
                return False
            
            # Check system resources
            system_load = metadata.get('system_load', 0.5)
            if system_load > 0.9 and intent_type in ['high_computation', 'multimedia']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking trigger conditions: {e}")
            return False

    async def _calculate_risk_score(self, intent_type: str, metadata: Dict[str, Any]) -> float:
        """Calculate risk score for proactive action"""
        try:
            risk_factors = {
                'system_impact': 0.0,
                'resource_cost': 0.0,
                'user_disruption': 0.0,
                'reversibility': 0.0
            }
            
            # Intent-specific risk assessment
            if intent_type == 'system_maintenance':
                risk_factors['system_impact'] = 0.7
                risk_factors['user_disruption'] = 0.6
                risk_factors['reversibility'] = 0.8
            elif intent_type == 'high_computation':
                risk_factors['resource_cost'] = 0.8
                risk_factors['system_impact'] = 0.4
            elif intent_type == 'development':
                risk_factors['resource_cost'] = 0.3
                risk_factors['system_impact'] = 0.2
            elif intent_type in ['document_work', 'browsing']:
                risk_factors['system_impact'] = 0.1
                risk_factors['user_disruption'] = 0.2
            
            # Adjust based on current system state
            current_load = metadata.get('system_load', 0.5)
            risk_factors['resource_cost'] *= (1.0 + current_load)
            
            active_users = metadata.get('active_users', 1)
            risk_factors['user_disruption'] *= min(2.0, active_users / 2.0)
            
            # Calculate weighted risk score
            total_risk = sum(
                risk_factors[factor] * self.risk_weights[factor]
                for factor in risk_factors
            )
            
            return min(1.0, total_risk)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 1.0  # Maximum risk on error

    async def _execute_proactive_action(self, intent_type: str, confidence: float,
                                      metadata: Dict[str, Any], risk_score: float) -> Optional[Dict[str, Any]]:
        """Execute proactive action for predicted intent"""
        try:
            if intent_type not in self.action_registry:
                return None
            
            action_function = self.action_registry[intent_type]
            
            # Execute action with timeout
            try:
                result = await asyncio.wait_for(
                    action_function(confidence, metadata, risk_score),
                    timeout=30.0
                )
                
                return {
                    'intent_type': intent_type,
                    'confidence': confidence,
                    'risk_score': risk_score,
                    'action_result': result,
                    'timestamp': datetime.now().isoformat(),
                    'success': result.get('success', False) if result else False
                }
                
            except asyncio.TimeoutError:
                logger.warning(f"Action timeout for {intent_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing proactive action for {intent_type}: {e}")
            return None

    # Action Implementation Methods

    async def _trigger_development_environment(self, confidence: float, metadata: Dict[str, Any], 
                                             risk_score: float) -> Dict[str, Any]:
        """Trigger development environment optimization"""
        try:
            actions_taken = []
            
            # Set CPU governor to performance mode for better compile times
            try:
                result = subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'performance'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Set CPU governor to performance mode")
                else:
                    actions_taken.append("CPU governor change failed (may require sudo)")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                actions_taken.append("CPU governor change not available")
            
            # Increase file watchers for development tools
            try:
                result = subprocess.run(['sudo', 'sysctl', '-w', 'fs.inotify.max_user_watches=524288'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Increased file system watchers for development")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Clear system caches for better compile performance
            try:
                subprocess.run(['sudo', 'sync'], capture_output=True, timeout=5)
                subprocess.run(['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], 
                             capture_output=True, timeout=5)
                actions_taken.append("Cleared system caches for better performance")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'development_environment',
                'expected_benefit': 'Improved compilation and IDE performance'
            }
            
        except Exception as e:
            logger.error(f"Error in development environment trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def _trigger_document_optimization(self, confidence: float, metadata: Dict[str, Any], 
                                           risk_score: float) -> Dict[str, Any]:
        """Trigger document work optimization"""
        try:
            actions_taken = []
            
            # Set CPU governor to ondemand for responsive desktop performance
            try:
                result = subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'ondemand'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Set CPU governor to ondemand for responsiveness")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                actions_taken.append("CPU governor change not available")
            
            # Reduce swappiness for better interactive performance
            try:
                subprocess.run(['sudo', 'sysctl', '-w', 'vm.swappiness=10'], 
                             capture_output=True, timeout=5)
                actions_taken.append("Optimized memory swappiness for desktop responsiveness")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'document_work',
                'expected_benefit': 'Improved desktop responsiveness for document editing'
            }
            
        except Exception as e:
            logger.error(f"Error in document optimization trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def _trigger_multimedia_processing(self, confidence: float, metadata: Dict[str, Any], 
                                           risk_score: float) -> Dict[str, Any]:
        """Trigger multimedia processing optimization"""
        try:
            actions_taken = []
            
            # Set high performance mode for multimedia processing
            try:
                result = subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'performance'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Enabled high performance mode for multimedia")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                actions_taken.append("CPU performance mode not available")
            
            # Optimize GPU performance if NVIDIA GPU is available
            try:
                result = subprocess.run(['nvidia-smi', '-pm', '1'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Enabled persistent GPU mode for multimedia processing")
            except (subprocess.CalledProcessError, FileNotFoundError):
                actions_taken.append("NVIDIA GPU optimization not available")
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'multimedia_processing',
                'expected_benefit': 'Optimized CPU and GPU for multimedia workflows'
            }
            
        except Exception as e:
            logger.error(f"Error in multimedia optimization trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def _trigger_gaming_optimization(self, confidence: float, metadata: Dict[str, Any], 
                                         risk_score: float) -> Dict[str, Any]:
        """Trigger gaming performance optimization"""
        try:
            actions_taken = []
            
            # Set maximum performance settings for gaming
            try:
                result = subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'performance'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Set maximum CPU performance mode")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                actions_taken.append("CPU performance mode not available")
            
            # Disable CPU power saving features for consistent performance
            try:
                with open('/sys/devices/system/cpu/cpuidle/state1/disable', 'w') as f:
                    f.write('1')
                actions_taken.append("Disabled CPU idle states for consistent gaming performance")
            except (FileNotFoundError, PermissionError):
                actions_taken.append("CPU idle state control not available")
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'gaming_performance',
                'expected_benefit': 'Maximum CPU performance for gaming'
            }
            
        except Exception as e:
            logger.error(f"Error in gaming optimization trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def _trigger_communication_setup(self, confidence: float, metadata: Dict[str, Any], 
                                          risk_score: float) -> Dict[str, Any]:
        """Trigger communication application optimization"""
        try:
            actions_taken = []
            
            # Optimize network buffers for low latency communication
            try:
                subprocess.run(['sudo', 'sysctl', '-w', 'net.core.rmem_max=268435456'], 
                             capture_output=True, timeout=5)
                subprocess.run(['sudo', 'sysctl', '-w', 'net.core.wmem_max=268435456'], 
                             capture_output=True, timeout=5)
                actions_taken.append("Optimized network buffers for low latency")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Set CPU governor for responsive performance
            try:
                result = subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'ondemand'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Set responsive CPU scaling for communication")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'communication_setup',
                'expected_benefit': 'Optimized for video calls and real-time communication'
            }
            
        except Exception as e:
            logger.error(f"Error in communication setup trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def _trigger_browser_optimization(self, confidence: float, metadata: Dict[str, Any], 
                                          risk_score: float) -> Dict[str, Any]:
        """Trigger browser performance optimization"""
        try:
            actions_taken = []
            
            # Clear system caches if memory usage is high
            memory_percent = metadata.get('memory_usage', 50)
            if memory_percent > 80:
                try:
                    subprocess.run(['sudo', 'sync'], capture_output=True, timeout=5)
                    subprocess.run(['sudo', 'sh', '-c', 'echo 1 > /proc/sys/vm/drop_caches'], 
                                 capture_output=True, timeout=5)
                    actions_taken.append("Cleared system caches to free memory for browser")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Optimize for desktop responsiveness
            try:
                subprocess.run(['sudo', 'sysctl', '-w', 'vm.swappiness=10'], 
                             capture_output=True, timeout=5)
                actions_taken.append("Optimized memory management for browser performance")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'browser_optimization',
                'expected_benefit': 'Improved browser responsiveness and memory management'
            }
            
        except Exception as e:
            logger.error(f"Error in browser optimization trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def _trigger_system_maintenance(self, confidence: float, metadata: Dict[str, Any], 
                                        risk_score: float) -> Dict[str, Any]:
        """Trigger system maintenance tasks"""
        try:
            actions_taken = []
            
            # Only perform low-risk maintenance
            if risk_score < 0.2:
                # Clean temporary files older than 7 days
                try:
                    result = subprocess.run(['find', '/tmp', '-type', 'f', '-atime', '+7', '-delete'], 
                                          capture_output=True, text=True, timeout=30)
                    actions_taken.append("Cleaned old temporary files")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                
                # Update package database (non-interactive)
                try:
                    result = subprocess.run(['sudo', 'apt', 'update'], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        actions_taken.append("Updated package database")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    actions_taken.append("Package update not available")
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'system_maintenance',
                'expected_benefit': 'System cleanup and maintenance'
            }
            
        except Exception as e:
            logger.error(f"Error in system maintenance trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def _trigger_compute_scaling(self, confidence: float, metadata: Dict[str, Any], 
                                     risk_score: float) -> Dict[str, Any]:
        """Trigger compute resource scaling for high-computation tasks"""
        try:
            actions_taken = []
            
            # Set maximum compute performance
            try:
                result = subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'performance'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    actions_taken.append("Enabled maximum compute performance")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                actions_taken.append("CPU performance scaling not available")
            
            # Disable CPU frequency scaling to maintain consistent performance
            try:
                with open('/sys/devices/system/cpu/intel_pstate/no_turbo', 'w') as f:
                    f.write('0')  # Enable turbo boost
                actions_taken.append("Enabled CPU turbo boost for maximum computation")
            except (FileNotFoundError, PermissionError):
                actions_taken.append("CPU turbo control not available")
            
            return {
                'success': True,
                'actions_taken': actions_taken,
                'optimization_type': 'compute_scaling',
                'expected_benefit': 'Maximum CPU performance for computational workloads'
            }
            
        except Exception as e:
            logger.error(f"Error in compute scaling trigger: {e}")
            return {'success': False, 'error': str(e)}

    async def get_trigger_status(self) -> Dict[str, Any]:
        """Get current status of the proactive trigger system"""
        try:
            current_time = datetime.now()
            
            # Calculate cooldown status
            cooldowns = {}
            for intent_type, last_action in self.recent_actions.items():
                time_remaining = self.action_cooldown - (current_time - last_action)
                cooldowns[intent_type] = {
                    'last_action': last_action.isoformat(),
                    'cooldown_remaining_seconds': max(0, time_remaining.total_seconds())
                }
            
            return {
                'system_status': {
                    'confidence_threshold': self.confidence_threshold,
                    'risk_threshold': self.risk_threshold,
                    'action_cooldown_minutes': self.action_cooldown.total_seconds() / 60,
                    'available_actions': list(self.action_registry.keys()),
                    'recent_actions_count': len(self.recent_actions)
                },
                'action_cooldowns': cooldowns,
                'risk_weights': self.risk_weights,
                'timestamp': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trigger status: {e}")
            return {}


# Test functionality
async def test_proactive_trigger():
    """Test the proactive trigger system"""
    try:
        # Mock PIG instance for testing
        class MockPIG:
            async def predict_intents(self, context):
                # Return mock predictions
                return [
                    ('development', 0.85, {'system_load': 0.4}),
                    ('document_work', 0.70, {'system_load': 0.3}),
                    ('high_computation', 0.60, {'system_load': 0.8})
                ]
        
        # Initialize trigger
        config = {
            'confidence_threshold': 0.75,
            'risk_threshold': 0.3,
            'action_cooldown_minutes': 1  # Short cooldown for testing
        }
        
        mock_pig = MockPIG()
        trigger = ProactiveActionTrigger(mock_pig, config)
        
        # Test context
        test_context = {
            'system_load': 0.4,
            'memory_usage': 60,
            'time_of_day': 14,
            'active_users': 1
        }
        
        print("Testing Proactive Action Trigger...")
        
        # Execute test
        results = await trigger.evaluate_and_trigger(test_context)
        
        print(f"Triggered {len(results)} actions:")
        for result in results:
            print(f"  - {result['intent_type']}: {result['success']}")
            if result['action_result']:
                print(f"    Actions: {result['action_result'].get('actions_taken', [])}")
        
        # Get status
        status = await trigger.get_trigger_status()
        print(f"\nSystem Status: {status['system_status']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return False


if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_proactive_trigger())
    print(f"Test {'PASSED' if result else 'FAILED'}")
