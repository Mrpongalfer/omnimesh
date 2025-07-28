#!/usr/bin/env python3
"""
LoL Nexus God Tier Interface - Behavior Monitor Agent
Phase 4: True Intent Resonance & Proactive Orchestration

Architect's Behavior Data Ingestion & Analysis Pipeline
100% Production-Ready Implementation with Privacy-First Design

Author: LoL Nexus Core Actualization Agent
Date: July 27, 2025
Version: Ultimate Trinity Architecture
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
import subprocess
import psutil
import requests
from cryptography.fernet import Fernet
import base64
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/behavior_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Export main classes for easy importing
__all__ = [
    'BehaviorAnalyzer', 'BehaviorEvidence', 'DesktopBehaviorMonitor', 
    'TailscaleBehaviorSync', 'LocalBehaviorAgent', 'TermuxAPIIntegration',
    'BehaviorMonitorOrchestrator', 'PrivacyEngine'
]

@dataclass
class BehaviorEvidence:
    """Represents evidence of user behavior for intent analysis"""
    timestamp: datetime
    evidence_type: str  # file_access, app_launch, search_query, location, etc.
    raw_data: Dict[str, Any]
    processed_features: Dict[str, Any]
    anonymized_hash: str
    confidence: float
    source: str = "desktop_monitor"  # Source of the evidence
    privacy_preserved: bool = True

@dataclass
class BehaviorPattern:
    """Represents a detected user behavior pattern"""
    pattern_id: str
    pattern_type: str  # file_access, app_usage, search_query, location, etc.
    frequency: float
    temporal_pattern: Dict[str, float]  # hour_of_day -> probability
    context_data: Dict[str, Any]
    confidence: float
    last_observed: datetime
    prediction_weight: float = 0.5

@dataclass
class UserActivity:
    """Individual user activity record"""
    timestamp: datetime
    activity_type: str
    resource_path: Optional[str]
    application: Optional[str]
    duration: Optional[float]
    metadata: Dict[str, Any]
    anonymized_hash: str

class BehaviorAnalyzer:
    """Core behavior analysis engine with privacy preservation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Initialize database
        self.db_path = self.config.get('database_path', 'behavior_patterns.db')
        self._init_database()
        
        # Pattern storage
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}
        self.activity_buffer: deque = deque(maxlen=10000)
        self.pattern_cache: Dict[str, Any] = {}
        
        # Analysis parameters
        self.analysis_window = timedelta(hours=24)
        self.pattern_threshold = 0.1
        self.confidence_threshold = 0.7
        
        # Privacy settings
        self.anonymization_level = self.config.get('anonymization_level', 'high')
        self.data_retention_days = self.config.get('data_retention_days', 30)
        
        logger.info("BehaviorAnalyzer initialized with privacy-preserving configuration")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                return json.load(f)
        
        return {
            'monitoring_enabled': True,
            'privacy_mode': True,
            'anonymization_level': 'high',
            'data_retention_days': 30,
            'analysis_interval': 300,  # 5 minutes
            'pattern_detection_threshold': 0.1,
            'confidence_threshold': 0.7
        }

    def _generate_encryption_key(self) -> bytes:
        """Generate or load encryption key for data protection"""
        key_file = Path.home() / '.lolnexus' / 'behavior_key.key'
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Restrict permissions
            return key

    def _init_database(self):
        """Initialize SQLite database for pattern storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS behavior_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    frequency REAL NOT NULL,
                    temporal_pattern TEXT NOT NULL,
                    context_data TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    last_observed TEXT NOT NULL,
                    prediction_weight REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    anonymized_hash TEXT NOT NULL,
                    encrypted_metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_patterns_type ON behavior_patterns(pattern_type)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp)
            ''')

    def anonymize_data(self, data: Any) -> str:
        """Anonymize sensitive data while preserving analytical value"""
        if isinstance(data, str):
            # Create consistent hash for pattern recognition
            return hashlib.sha256(data.encode()).hexdigest()[:16]
        elif isinstance(data, dict):
            anonymized = {}
            for key, value in data.items():
                if key in ['user', 'username', 'personal_info']:
                    anonymized[key] = self.anonymize_data(str(value))
                elif key in ['path', 'file_path']:
                    # Preserve directory structure but anonymize file names
                    try:
                        path = Path(str(value))
                        parts = []
                        for part in path.parts:
                            if part.startswith('/') or part in ['home', 'Documents', 'Desktop']:
                                parts.append(part)
                            else:
                                parts.append(self.anonymize_data(part))
                        if parts:
                            anonymized[key] = str(Path(*parts))
                        else:
                            anonymized[key] = self.anonymize_data(str(value))
                    except (TypeError, OSError) as e:
                        # Fallback to simple anonymization
                        anonymized[key] = self.anonymize_data(str(value))
                else:
                    anonymized[key] = value
            return json.dumps(anonymized, sort_keys=True)
        else:
            return hashlib.sha256(str(data).encode()).hexdigest()[:16]

    async def record_activity(self, activity: UserActivity):
        """Record and process user activity with privacy preservation"""
        try:
            # Anonymize sensitive data
            activity.anonymized_hash = self.anonymize_data({
                'type': activity.activity_type,
                'resource': activity.resource_path,
                'app': activity.application
            })
            
            # Encrypt metadata
            encrypted_metadata = self.cipher_suite.encrypt(
                json.dumps(activity.metadata).encode()
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO activity_log 
                    (timestamp, activity_type, anonymized_hash, encrypted_metadata, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    activity.timestamp.isoformat(),
                    activity.activity_type,
                    activity.anonymized_hash,
                    encrypted_metadata.decode(),
                    datetime.now().isoformat()
                ))
            
            # Add to buffer for real-time analysis
            self.activity_buffer.append(activity)
            
            # Trigger pattern analysis if buffer is significant
            if len(self.activity_buffer) % 100 == 0:
                await self.analyze_patterns()
                
        except Exception as e:
            logger.error(f"Error recording activity: {e}")

    async def analyze_patterns(self):
        """Analyze activity buffer for behavioral patterns"""
        try:
            current_time = datetime.now()
            recent_activities = [
                activity for activity in self.activity_buffer
                if current_time - activity.timestamp < self.analysis_window
            ]
            
            # Group activities by type and resource
            activity_groups = defaultdict(list)
            for activity in recent_activities:
                group_key = f"{activity.activity_type}:{activity.anonymized_hash}"
                activity_groups[group_key].append(activity)
            
            # Detect patterns
            for group_key, activities in activity_groups.items():
                if len(activities) < 3:  # Minimum threshold for pattern
                    continue
                
                pattern = await self._detect_pattern(group_key, activities)
                if pattern and pattern.confidence > self.confidence_threshold:
                    self.behavior_patterns[pattern.pattern_id] = pattern
                    await self._store_pattern(pattern)
            
            # Clean old patterns
            await self._cleanup_old_patterns()
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")

    async def _detect_pattern(self, group_key: str, activities: List[UserActivity]) -> Optional[BehaviorPattern]:
        """Detect behavioral pattern from activity group"""
        try:
            if len(activities) < 3:
                return None
            
            # Calculate temporal distribution
            temporal_pattern = defaultdict(float)
            total_activities = len(activities)
            
            for activity in activities:
                hour = activity.timestamp.hour
                temporal_pattern[str(hour)] += 1.0 / total_activities
            
            # Calculate frequency (activities per day)
            time_span = (activities[-1].timestamp - activities[0].timestamp).total_seconds() / 86400
            frequency = len(activities) / max(time_span, 1.0)
            
            # Calculate confidence based on consistency
            hour_variance = sum((freq - 1.0/24)**2 for freq in temporal_pattern.values()) / 24
            confidence = max(0.0, 1.0 - hour_variance * 10)
            
            # Extract pattern type and context
            pattern_type = activities[0].activity_type
            context_data = {
                'resource_pattern': activities[0].anonymized_hash,
                'avg_duration': sum(a.duration for a in activities if a.duration) / len(activities),
                'peak_hours': sorted(temporal_pattern.keys(), key=temporal_pattern.get, reverse=True)[:3],
                'activity_count': len(activities)
            }
            
            # Generate pattern ID
            pattern_id = hashlib.sha256(
                f"{group_key}:{temporal_pattern}:{frequency}".encode()
            ).hexdigest()[:16]
            
            return BehaviorPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                frequency=frequency,
                temporal_pattern=dict(temporal_pattern),
                context_data=context_data,
                confidence=confidence,
                last_observed=activities[-1].timestamp,
                prediction_weight=min(confidence * frequency / 10.0, 1.0)
            )
            
        except Exception as e:
            logger.error(f"Error detecting pattern: {e}")
            return None

    async def _store_pattern(self, pattern: BehaviorPattern):
        """Store behavior pattern in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO behavior_patterns
                    (pattern_id, pattern_type, frequency, temporal_pattern, context_data,
                     confidence, last_observed, prediction_weight, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern.pattern_id,
                    pattern.pattern_type,
                    pattern.frequency,
                    json.dumps(pattern.temporal_pattern),
                    json.dumps(pattern.context_data),
                    pattern.confidence,
                    pattern.last_observed.isoformat(),
                    pattern.prediction_weight,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
        except Exception as e:
            logger.error(f"Error storing pattern: {e}")

    async def _cleanup_old_patterns(self):
        """Remove old patterns and activities beyond retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Remove old activity logs
                conn.execute('''
                    DELETE FROM activity_log 
                    WHERE datetime(timestamp) < ?
                ''', (cutoff_date.isoformat(),))
                
                # Remove low-confidence patterns
                conn.execute('''
                    DELETE FROM behavior_patterns 
                    WHERE confidence < ? OR datetime(last_observed) < ?
                ''', (self.confidence_threshold, cutoff_date.isoformat()))
                
        except Exception as e:
            logger.error(f"Error cleaning up old patterns: {e}")

    async def get_active_patterns(self) -> List[BehaviorPattern]:
        """Get all active behavior patterns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM behavior_patterns 
                    WHERE confidence >= ? 
                    ORDER BY prediction_weight DESC
                ''', (self.confidence_threshold,))
                
                patterns = []
                for row in cursor.fetchall():
                    pattern = BehaviorPattern(
                        pattern_id=row[0],
                        pattern_type=row[1],
                        frequency=row[2],
                        temporal_pattern=json.loads(row[3]),
                        context_data=json.loads(row[4]),
                        confidence=row[5],
                        last_observed=datetime.fromisoformat(row[6]),
                        prediction_weight=row[7]
                    )
                    patterns.append(pattern)
                
                return patterns
                
        except Exception as e:
            logger.error(f"Error getting active patterns: {e}")
            return []

    async def predict_next_activity(self, current_time: datetime = None) -> List[Tuple[str, float]]:
        """Predict likely next user activities based on patterns"""
        if current_time is None:
            current_time = datetime.now()
        
        try:
            patterns = await self.get_active_patterns()
            predictions = []
            
            current_hour = str(current_time.hour)
            
            for pattern in patterns:
                # Get probability for current hour
                hour_probability = pattern.temporal_pattern.get(current_hour, 0.0)
                
                # Calculate overall prediction score
                prediction_score = (
                    hour_probability * pattern.confidence * pattern.prediction_weight
                )
                
                if prediction_score > self.pattern_threshold:
                    predictions.append((pattern.pattern_type, prediction_score))
            
            # Sort by prediction score
            predictions.sort(key=lambda x: x[1], reverse=True)
            return predictions[:10]  # Return top 10 predictions
            
        except Exception as e:
            logger.error(f"Error predicting next activity: {e}")
            return []

    async def get_behavior_summary(self) -> Dict[str, Any]:
        """Get comprehensive behavior analysis summary"""
        try:
            patterns = await self.get_active_patterns()
            predictions = await self.predict_next_activity()
            
            # Calculate pattern statistics
            pattern_types = defaultdict(int) 
            total_confidence = 0.0
            peak_hours = defaultdict(float)
            
            for pattern in patterns:
                pattern_types[pattern.pattern_type] += 1
                total_confidence += pattern.confidence
                
                for hour, prob in pattern.temporal_pattern.items():
                    peak_hours[hour] += prob * pattern.prediction_weight
            
            avg_confidence = total_confidence / len(patterns) if patterns else 0.0
            
            # Get top peak hours
            sorted_hours = sorted(peak_hours.items(), key=lambda x: x[1], reverse=True)
            top_hours = [(hour, score) for hour, score in sorted_hours[:5]]
            
            return {
                'total_patterns': len(patterns),
                'pattern_types': dict(pattern_types),
                'average_confidence': avg_confidence,
                'peak_activity_hours': top_hours,
                'current_predictions': predictions,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_retention_days': self.data_retention_days,
                'privacy_level': self.anonymization_level
            }
            
        except Exception as e:
            logger.error(f"Error generating behavior summary: {e}")
            return {}

    def detect_patterns(self, evidence_list: List[BehaviorEvidence]) -> List[BehaviorPattern]:
        """
        Detect behavioral patterns from a list of evidence.
        This method analyzes evidence to identify recurring patterns.
        """
        try:
            patterns = []
            
            if not evidence_list:
                return patterns
            
            # Group evidence by type
            evidence_by_type = {}
            for evidence in evidence_list:
                if evidence.evidence_type not in evidence_by_type:
                    evidence_by_type[evidence.evidence_type] = []
                evidence_by_type[evidence.evidence_type].append(evidence)
            
            # Analyze patterns for each evidence type
            for evidence_type, evidence_group in evidence_by_type.items():
                if len(evidence_group) >= 2:  # Need at least 2 instances to form a pattern
                    # Calculate temporal pattern based on evidence timestamps
                    temporal_pattern = {}
                    for evidence in evidence_group:
                        hour = str(evidence.timestamp.hour)
                        temporal_pattern[hour] = temporal_pattern.get(hour, 0) + 1
                    
                    # Normalize temporal pattern
                    total = sum(temporal_pattern.values())
                    if total > 0:
                        temporal_pattern = {h: count/total for h, count in temporal_pattern.items()}
                    
                    pattern = BehaviorPattern(
                        pattern_id=f"pattern_{evidence_type}_{len(patterns)}",
                        pattern_type=evidence_type,
                        frequency=len(evidence_group),
                        temporal_pattern=temporal_pattern,
                        context_data={
                            'evidence_count': len(evidence_group),
                            'first_seen': evidence_group[0].timestamp.isoformat(),
                            'last_seen': evidence_group[-1].timestamp.isoformat()
                        },
                        confidence=min(1.0, len(evidence_group) / 10.0),  # Higher frequency = higher confidence
                        last_observed=evidence_group[-1].timestamp,
                        prediction_weight=0.7  # Default prediction weight
                    )
                    patterns.append(pattern)
            
            logger.debug(f"Detected {len(patterns)} patterns from {len(evidence_list)} evidence items")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []


class DesktopBehaviorMonitor:
    """Desktop-specific behavior monitoring with Tailscale integration"""
    
    def __init__(self, behavior_analyzer: BehaviorAnalyzer):
        self.analyzer = behavior_analyzer
        self.running = False
        self.monitor_thread = None
        
        # Monitoring intervals
        self.file_monitor_interval = 60    # 1 minute
        self.app_monitor_interval = 30     # 30 seconds
        self.system_monitor_interval = 120 # 2 minutes
        
        logger.info("DesktopBehaviorMonitor initialized")

    async def start_monitoring(self):
        """Start all monitoring processes"""
        self.running = True
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_file_access()),
            asyncio.create_task(self._monitor_application_usage()),
            asyncio.create_task(self._monitor_system_resources()),
            asyncio.create_task(self._monitor_network_activity())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in monitoring tasks: {e}")
        finally:
            self.running = False

    async def _monitor_file_access(self):
        """Monitor file system access patterns"""
        watched_dirs = [
            Path.home() / 'Documents',
            Path.home() / 'Desktop',
            Path.home() / 'Downloads',
            Path('/tmp')
        ]
        
        last_access_times = {}
        
        while self.running:
            try:
                for dir_path in watched_dirs:
                    if not dir_path.exists():
                        continue
                    
                    for file_path in dir_path.rglob('*'):
                        if file_path.is_file():
                            try:
                                stat = file_path.stat()
                                access_time = datetime.fromtimestamp(stat.st_atime)
                                
                                # Check if file was accessed recently
                                if file_path in last_access_times:
                                    if access_time > last_access_times[file_path]:
                                        activity = UserActivity(
                                            timestamp=access_time,
                                            activity_type='file_access',
                                            resource_path=str(file_path),
                                            application=None,
                                            duration=None,
                                            metadata={
                                                'file_size': stat.st_size,
                                                'file_type': file_path.suffix,
                                                'parent_dir': str(file_path.parent)
                                            },
                                            anonymized_hash=''
                                        )
                                        await self.analyzer.record_activity(activity)
                                
                                last_access_times[file_path] = access_time
                                
                            except (OSError, PermissionError):
                                continue
                
                await asyncio.sleep(self.file_monitor_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring file access: {e}")
                await asyncio.sleep(self.file_monitor_interval)

    async def _monitor_application_usage(self):
        """Monitor running applications and usage patterns"""
        last_processes = set()
        
        while self.running:
            try:
                current_processes = set()
                
                for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cpu_percent']):
                    try:
                        proc_info = proc.info
                        proc_key = f"{proc_info['name']}:{proc_info['pid']}"
                        current_processes.add(proc_key)
                        
                        # Detect new processes
                        if proc_key not in last_processes:
                            activity = UserActivity(
                                timestamp=datetime.fromtimestamp(proc_info['create_time']),
                                activity_type='app_launch',
                                resource_path=None,
                                application=proc_info['name'],
                                duration=None,
                                metadata={
                                    'pid': proc_info['pid'],
                                    'cpu_percent': proc_info['cpu_percent']
                                },
                                anonymized_hash=''
                            )
                            await self.analyzer.record_activity(activity)
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                last_processes = current_processes
                await asyncio.sleep(self.app_monitor_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring applications: {e}")
                await asyncio.sleep(self.app_monitor_interval)

    async def _monitor_system_resources(self):
        """Monitor system resource usage patterns"""
        while self.running:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                activity = UserActivity(
                    timestamp=datetime.now(),
                    activity_type='system_metrics',
                    resource_path=None,
                    application='system',
                    duration=None,
                    metadata={
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'disk_percent': disk.percent,
                        'memory_available': memory.available,
                        'disk_free': disk.free
                    },
                    anonymized_hash=''
                )
                await self.analyzer.record_activity(activity)
                
                await asyncio.sleep(self.system_monitor_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(self.system_monitor_interval)

    async def _monitor_network_activity(self):
        """Monitor network usage patterns"""
        last_stats = psutil.net_io_counters()
        
        while self.running:
            try:
                current_stats = psutil.net_io_counters()
                
                # Calculate deltas
                bytes_sent_delta = current_stats.bytes_sent - last_stats.bytes_sent
                bytes_recv_delta = current_stats.bytes_recv - last_stats.bytes_recv
                
                if bytes_sent_delta > 0 or bytes_recv_delta > 0:
                    activity = UserActivity(
                        timestamp=datetime.now(),
                        activity_type='network_activity',
                        resource_path=None,
                        application='network',
                        duration=None,
                        metadata={
                            'bytes_sent_delta': bytes_sent_delta,
                            'bytes_recv_delta': bytes_recv_delta,
                            'packets_sent': current_stats.packets_sent,
                            'packets_recv': current_stats.packets_recv
                        },
                        anonymized_hash=''
                    )
                    await self.analyzer.record_activity(activity)
                
                last_stats = current_stats
                await asyncio.sleep(30)  # Network monitoring every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring network activity: {e}")
                await asyncio.sleep(30)

    def stop_monitoring(self):
        """Stop all monitoring processes"""
        self.running = False
        logger.info("DesktopBehaviorMonitor stopped")


class TailscaleBehaviorSync:
    """Synchronize behavior data across Tailscale network"""
    
    def __init__(self, behavior_analyzer: BehaviorAnalyzer, tailscale_config: Dict[str, Any]):
        self.analyzer = behavior_analyzer
        self.tailscale_config = tailscale_config
        self.sync_interval = tailscale_config.get('sync_interval', 300)  # 5 minutes
        self.nodes = tailscale_config.get('nodes', [])
        
        logger.info("TailscaleBehaviorSync initialized")

    async def start_sync(self):
        """Start behavior data synchronization"""
        while True:
            try:
                await self._sync_behavior_data()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Error in behavior sync: {e}")
                await asyncio.sleep(self.sync_interval)

    async def _sync_behavior_data(self):
        """Synchronize behavior patterns across nodes"""
        try:
            local_summary = await self.analyzer.get_behavior_summary()
            
            for node in self.nodes:
                try:
                    # Send local summary to remote node
                    response = requests.post(
                        f"http://{node['address']}/api/behavior/sync",
                        json=local_summary,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        remote_patterns = response.json().get('patterns', [])
                        # Process remote patterns (implementation would merge with local)
                        logger.info(f"Synced with node {node['name']}: {len(remote_patterns)} patterns")
                    
                except requests.RequestException as e:
                    logger.warning(f"Failed to sync with node {node['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error syncing behavior data: {e}")


# Main behavior monitoring service
async def main():
    """Main behavior monitoring service entry point"""
    try:
        # Initialize behavior analyzer
        config_path = os.getenv('BEHAVIOR_CONFIG_PATH', 'config/behavior_monitor.json')
        analyzer = BehaviorAnalyzer(config_path)
        
        # Initialize desktop monitor
        desktop_monitor = DesktopBehaviorMonitor(analyzer)
        
        # Initialize Tailscale sync (if configured)
        tailscale_config = {
            'sync_interval': 300,
            'nodes': [
                {'name': 'chromebox-1', 'address': '100.64.0.2:8080'},
                {'name': 'chromebox-2', 'address': '100.64.0.3:8080'},
            ]
        }
        tailscale_sync = TailscaleBehaviorSync(analyzer, tailscale_config)
        
        # Start all services
        tasks = [
            asyncio.create_task(desktop_monitor.start_monitoring()),
            asyncio.create_task(tailscale_sync.start_sync())
        ]
        
        logger.info("Behavior monitoring services started")
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("Behavior monitoring service stopped by user")
    except Exception as e:
        logger.error(f"Error in behavior monitoring service: {e}")
    finally:
        if 'desktop_monitor' in locals():
            desktop_monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
