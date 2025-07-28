#!/usr/bin/env python3
"""
Dynamic Resource Allocation Prophet (DRAP) - Phase 4: True Intent Resonance
Reinforcement Learning-driven Predictive Resource Allocation for LoL Nexus

Fully functional reinforcement learning component that predicts future compute
demand and makes probabilistic decisions on resource allocation and optimization.
"""

import asyncio
import json
import logging
import os
import time
import numpy as np
import pandas as pd
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import defaultdict, deque
import subprocess
import psutil
import requests
from pathlib import Path
import threading
import pickle
from concurrent.futures import ThreadPoolExecutor

# Machine Learning imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import scipy.optimize as optimize
from scipy.stats import norm, expon

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResourceMetrics:
    """Current resource utilization metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_bytes: int
    gpu_percent: Optional[float] = None
    gpu_memory_percent: Optional[float] = None
    load_average: Optional[float] = None
    temperature: Optional[float] = None
    power_usage: Optional[float] = None

@dataclass
class ResourceDemand:
    """Predicted resource demand"""
    timestamp: datetime
    predicted_cpu: float
    predicted_memory: float
    predicted_disk_io: float
    predicted_network_io: float
    predicted_gpu: Optional[float] = None
    confidence: float = 0.8
    prediction_horizon: timedelta = field(default_factory=lambda: timedelta(minutes=30))

@dataclass
class ResourceAction:
    """Resource allocation action"""
    action_id: str
    action_type: str  # scale_up, scale_down, optimize, migrate
    target_resource: str  # cpu, memory, storage, network
    target_nodes: List[str]
    parameters: Dict[str, Any]
    expected_benefit: float
    cost: float
    risk_score: float
    execution_time: timedelta
    priority: int

@dataclass
class ComputeNode:
    """Compute node in the resource fabric"""
    node_id: str
    node_type: str  # desktop, chromebox, cloud_vm, mobile
    address: str
    capabilities: Dict[str, Any]
    current_metrics: Optional[ResourceMetrics] = None
    availability_score: float = 1.0
    cost_per_hour: float = 0.0
    max_cpu: int = 4
    max_memory_gb: int = 8
    status: str = "active"  # active, idle, maintenance, offline

class DynamicResourceAllocationProphet:
    """
    Fully functional Dynamic Resource Allocation Prophet (DRAP) using
    reinforcement learning for predictive compute demand management.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Resource tracking
        self.compute_nodes: Dict[str, ComputeNode] = {}
        self.metrics_history: deque = deque(maxlen=10000)
        self.demand_predictions: Dict[str, ResourceDemand] = {}
        self.action_history: List[ResourceAction] = []
        
        # Machine learning models
        self.cpu_predictor = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.memory_predictor = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.io_predictor = RandomForestRegressor(n_estimators=50, random_state=42)
        self.network_predictor = LinearRegression()
        
        # Scalers for feature normalization
        self.feature_scaler = StandardScaler()
        self.target_scaler = MinMaxScaler()
        
        # Reinforcement learning parameters
        self.learning_rate = config.get('learning_rate', 0.01)
        self.discount_factor = config.get('discount_factor', 0.95)
        self.exploration_rate = config.get('exploration_rate', 0.1)
        self.exploration_decay = config.get('exploration_decay', 0.995)
        
        # Q-learning table for action selection
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.state_discretization = config.get('state_discretization', 10)
        
        # Prediction parameters
        self.prediction_window = timedelta(minutes=config.get('prediction_window_minutes', 30))
        self.retraining_interval = timedelta(hours=config.get('retraining_hours', 2))
        self.last_training = datetime.now() - self.retraining_interval
        
        # Database for persistence
        self.db_path = config.get('drap_database', 'drap_knowledge.db')
        self._init_database()
        
        # External data integration
        self.external_data_sources = config.get('external_data_sources', {})
        self.market_data: Dict[str, Any] = {}
        
        # Initialize compute nodes
        self._initialize_compute_nodes()
        
        logger.info("Dynamic Resource Allocation Prophet (DRAP) initialized")

    def _init_database(self):
        """Initialize SQLite database for DRAP persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_percent REAL NOT NULL,
                    network_io_bytes INTEGER NOT NULL,
                    gpu_percent REAL,
                    load_average REAL,
                    temperature REAL,
                    power_usage REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_actions (
                    action_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_resource TEXT NOT NULL,
                    target_nodes TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    expected_benefit REAL NOT NULL,
                    actual_benefit REAL,
                    cost REAL NOT NULL,
                    execution_time_seconds INTEGER NOT NULL,
                    success BOOLEAN NOT NULL DEFAULT 0
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS demand_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prediction_timestamp TEXT NOT NULL,
                    predicted_cpu REAL NOT NULL,
                    predicted_memory REAL NOT NULL,
                    predicted_disk_io REAL NOT NULL,
                    predicted_network_io REAL NOT NULL,
                    confidence REAL NOT NULL,
                    actual_cpu REAL,
                    actual_memory REAL,
                    actual_disk_io REAL,
                    actual_network_io REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS q_learning_table (
                    state_hash TEXT NOT NULL,
                    action TEXT NOT NULL,
                    q_value REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    PRIMARY KEY (state_hash, action)
                )
            ''')

    def _initialize_compute_nodes(self):
        """Initialize compute nodes from configuration"""
        try:
            nodes_config = self.config.get('compute_nodes', {})
            
            # Local desktop node
            self.compute_nodes['desktop'] = ComputeNode(
                node_id='desktop',
                node_type='desktop',
                address='localhost',
                capabilities={
                    'cpu_cores': psutil.cpu_count(),
                    'memory_gb': psutil.virtual_memory().total // (1024**3),
                    'has_gpu': self._detect_gpu(),
                    'max_power_watts': 300
                },
                max_cpu=psutil.cpu_count(),
                max_memory_gb=psutil.virtual_memory().total // (1024**3),
                cost_per_hour=0.05  # Local power cost estimate
            )
            
            # Chromebox nodes (from Tailscale network)
            for i, chromebox_config in enumerate(nodes_config.get('chromeboxes', [])):
                node_id = f"chromebox-{i+1}"
                self.compute_nodes[node_id] = ComputeNode(
                    node_id=node_id,
                    node_type='chromebox',
                    address=chromebox_config.get('address', f'100.64.0.{i+2}'),
                    capabilities=chromebox_config.get('capabilities', {
                        'cpu_cores': 4,
                        'memory_gb': 8,
                        'has_gpu': False,
                        'max_power_watts': 65
                    }),
                    max_cpu=4,
                    max_memory_gb=8,
                    cost_per_hour=0.02
                )
            
            # Cloud VM nodes (if configured)
            for cloud_config in nodes_config.get('cloud_vms', []):
                node_id = cloud_config['node_id']
                self.compute_nodes[node_id] = ComputeNode(
                    node_id=node_id,
                    node_type='cloud_vm',
                    address=cloud_config['address'],
                    capabilities=cloud_config.get('capabilities', {}),
                    max_cpu=cloud_config.get('max_cpu', 8),
                    max_memory_gb=cloud_config.get('max_memory_gb', 16),
                    cost_per_hour=cloud_config.get('cost_per_hour', 0.50)
                )
            
            logger.info(f"Initialized {len(self.compute_nodes)} compute nodes")
            
        except Exception as e:
            logger.error(f"Error initializing compute nodes: {e}")

    def _detect_gpu(self) -> bool:
        """Detect if GPU is available"""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    async def collect_resource_metrics(self):
        """Collect current resource metrics from all nodes"""
        try:
            current_time = datetime.now()
            
            for node_id, node in self.compute_nodes.items():
                try:
                    if node.node_type == 'desktop':
                        metrics = await self._collect_local_metrics()
                    else:
                        metrics = await self._collect_remote_metrics(node)
                    
                    if metrics:
                        metrics.timestamp = current_time
                        node.current_metrics = metrics
                        self.metrics_history.append((node_id, metrics))
                        
                        # Store in database
                        await self._store_metrics(node_id, metrics)
                        
                except Exception as e:
                    logger.warning(f"Failed to collect metrics from {node_id}: {e}")
                    node.availability_score *= 0.95  # Reduce availability on failure
            
        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")

    async def _collect_local_metrics(self) -> ResourceMetrics:
        """Collect metrics from local system"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io_bytes = network.bytes_sent + network.bytes_recv
            
            # Load average
            load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else None
            
            # GPU metrics (if available)
            gpu_percent = None
            gpu_memory_percent = None
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                                       '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    gpu_data = result.stdout.strip().split(', ')
                    gpu_percent = float(gpu_data[0])
                    gpu_memory_used = float(gpu_data[1])
                    gpu_memory_total = float(gpu_data[2])
                    gpu_memory_percent = (gpu_memory_used / gpu_memory_total) * 100
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
            
            # Temperature (simplified)
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    cpu_temps = temps.get('coretemp', temps.get('cpu_thermal', []))
                    if cpu_temps:
                        temperature = cpu_temps[0].current
            except (AttributeError, IndexError):
                pass
            
            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io_bytes=network_io_bytes,
                gpu_percent=gpu_percent,
                gpu_memory_percent=gpu_memory_percent,
                load_average=load_avg,
                temperature=temperature
            )
            
        except Exception as e:
            logger.error(f"Error collecting local metrics: {e}")
            return None

    async def _collect_remote_metrics(self, node: ComputeNode) -> Optional[ResourceMetrics]:
        """Collect metrics from remote node"""
        try:
            # For Chromebox nodes, use HTTP API
            if node.node_type == 'chromebox':
                url = f"http://{node.address}:8080/api/metrics"
                async with asyncio.timeout(10):
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                return ResourceMetrics(
                                    timestamp=datetime.now(),
                                    cpu_percent=data.get('cpu_percent', 0),
                                    memory_percent=data.get('memory_percent', 0),
                                    disk_percent=data.get('disk_percent', 0),
                                    network_io_bytes=data.get('network_io_bytes', 0),
                                    load_average=data.get('load_average')
                                )
            
            # For cloud VMs, use SSH or cloud provider API
            elif node.node_type == 'cloud_vm':
                # Simplified implementation - would use actual cloud provider APIs
                return None
                
        except Exception as e:
            logger.warning(f"Error collecting remote metrics from {node.node_id}: {e}")
            return None

    async def predict_resource_demand(self, prediction_horizon: timedelta = None) -> Dict[str, ResourceDemand]:
        """Predict future resource demand using ML models"""
        try:
            if prediction_horizon is None:
                prediction_horizon = self.prediction_window
            
            current_time = datetime.now()
            predictions = {}
            
            # Prepare training data from metrics history
            if len(self.metrics_history) < 50:  # Need minimum data
                logger.warning("Insufficient data for prediction")
                return {}
            
            # Extract features and targets from metrics history
            features, targets = self._prepare_training_data()
            
            if features.shape[0] < 20:
                logger.warning("Insufficient training data")
                return {}
            
            # Retrain models if needed
            if current_time - self.last_training > self.retraining_interval:
                await self._retrain_models(features, targets)
                self.last_training = current_time
            
            # Generate predictions for each node
            for node_id, node in self.compute_nodes.items():
                try:
                    if not node.current_metrics:
                        continue
                    
                    # Prepare current state features
                    current_features = self._extract_current_features(node)
                    
                    if current_features is None:
                        continue
                    
                    # Predict future demand
                    predicted_demand = await self._predict_node_demand(
                        node_id, current_features, prediction_horizon
                    )
                    
                    if predicted_demand:
                        predictions[node_id] = predicted_demand
                        
                        # Store prediction in database
                        await self._store_prediction(node_id, predicted_demand)
                        
                except Exception as e:
                    logger.warning(f"Error predicting demand for {node_id}: {e}")
            
            self.demand_predictions = predictions
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting resource demand: {e}")
            return {}

    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from metrics history"""
        try:
            # Convert metrics history to structured data
            data_rows = []
            
            # Group by node and create time series
            node_series = defaultdict(list)
            for node_id, metrics in self.metrics_history:
                node_series[node_id].append(metrics)
            
            # Create feature vectors with temporal patterns
            for node_id, metrics_list in node_series.items():
                if len(metrics_list) < 10:  # Need minimum history
                    continue
                
                # Sort by timestamp
                metrics_list.sort(key=lambda x: x.timestamp)
                
                # Create sliding windows
                for i in range(5, len(metrics_list)):  # Use 5 past points to predict next
                    window = metrics_list[i-5:i]
                    target = metrics_list[i]
                    
                    # Extract features from window
                    features = []
                    
                    # Basic statistics from window
                    cpu_values = [m.cpu_percent for m in window]
                    memory_values = [m.memory_percent for m in window]
                    disk_values = [m.disk_percent for m in window]
                    
                    features.extend([
                        np.mean(cpu_values), np.std(cpu_values), np.max(cpu_values),
                        np.mean(memory_values), np.std(memory_values), np.max(memory_values),
                        np.mean(disk_values), np.std(disk_values), np.max(disk_values)
                    ])
                    
                    # Temporal features
                    hour = target.timestamp.hour
                    day_of_week = target.timestamp.weekday()
                    features.extend([
                        hour / 24.0,  # Normalized hour
                        day_of_week / 7.0,  # Normalized day of week
                        np.sin(2 * np.pi * hour / 24),  # Cyclical hour
                        np.cos(2 * np.pi * hour / 24),
                        np.sin(2 * np.pi * day_of_week / 7),  # Cyclical day
                        np.cos(2 * np.pi * day_of_week / 7)
                    ])
                    
                    # Trend features
                    cpu_trend = (cpu_values[-1] - cpu_values[0]) / len(cpu_values)
                    memory_trend = (memory_values[-1] - memory_values[0]) / len(memory_values)
                    features.extend([cpu_trend, memory_trend])
                    
                    # Network activity (if available)
                    network_values = [m.network_io_bytes for m in window if m.network_io_bytes]
                    if network_values:
                        features.append(np.mean(network_values) / 1e6)  # Normalize to MB
                    else:
                        features.append(0.0)
                    
                    # Target values
                    targets_row = [
                        target.cpu_percent,
                        target.memory_percent,
                        target.disk_percent,
                        target.network_io_bytes / 1e6  # Normalize to MB
                    ]
                    
                    data_rows.append((features, targets_row))
            
            if not data_rows:
                return np.array([]), np.array([])
            
            # Convert to numpy arrays
            features_list, targets_list = zip(*data_rows)
            features = np.array(features_list)
            targets = np.array(targets_list)
            
            return features, targets
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return np.array([]), np.array([])

    async def _retrain_models(self, features: np.ndarray, targets: np.ndarray):
        """Retrain ML models with latest data"""
        try:
            if features.shape[0] < 20:
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.feature_scaler.fit_transform(X_train)
            X_test_scaled = self.feature_scaler.transform(X_test)
            
            # Train CPU predictor
            self.cpu_predictor.fit(X_train_scaled, y_train[:, 0])
            cpu_predictions = self.cpu_predictor.predict(X_test_scaled)
            cpu_r2 = r2_score(y_test[:, 0], cpu_predictions)
            
            # Train memory predictor
            self.memory_predictor.fit(X_train_scaled, y_train[:, 1])
            memory_predictions = self.memory_predictor.predict(X_test_scaled)
            memory_r2 = r2_score(y_test[:, 1], memory_predictions)
            
            # Train disk I/O predictor
            self.io_predictor.fit(X_train_scaled, y_train[:, 2])
            io_predictions = self.io_predictor.predict(X_test_scaled)
            io_r2 = r2_score(y_test[:, 2], io_predictions)
            
            # Train network predictor
            self.network_predictor.fit(X_train_scaled, y_train[:, 3])
            network_predictions = self.network_predictor.predict(X_test_scaled)
            network_r2 = r2_score(y_test[:, 3], network_predictions)
            
            logger.info(f"Models retrained - CPU R²: {cpu_r2:.3f}, Memory R²: {memory_r2:.3f}, "
                       f"IO R²: {io_r2:.3f}, Network R²: {network_r2:.3f}")
            
        except Exception as e:
            logger.error(f"Error retraining models: {e}")

    def _extract_current_features(self, node: ComputeNode) -> Optional[np.ndarray]:
        """Extract features from current node state"""
        try:
            if not node.current_metrics:
                return None
            
            metrics = node.current_metrics
            current_time = datetime.now()
            
            # Get recent metrics for this node
            recent_metrics = [
                m for node_id, m in self.metrics_history
                if node_id == node.node_id and 
                (current_time - m.timestamp).total_seconds() < 1800  # Last 30 minutes
            ]
            
            if len(recent_metrics) < 3:
                # Not enough history, use current values with defaults
                features = [
                    metrics.cpu_percent, 0, metrics.cpu_percent,  # mean, std, max
                    metrics.memory_percent, 0, metrics.memory_percent,
                    metrics.disk_percent, 0, metrics.disk_percent
                ]
            else:
                # Calculate statistics from recent history
                recent_metrics.sort(key=lambda x: x.timestamp)
                cpu_values = [m.cpu_percent for m in recent_metrics]
                memory_values = [m.memory_percent for m in recent_metrics]
                disk_values = [m.disk_percent for m in recent_metrics]
                
                features = [
                    np.mean(cpu_values), np.std(cpu_values), np.max(cpu_values),
                    np.mean(memory_values), np.std(memory_values), np.max(memory_values),
                    np.mean(disk_values), np.std(disk_values), np.max(disk_values)
                ]
            
            # Add temporal features
            hour = current_time.hour
            day_of_week = current_time.weekday()
            features.extend([
                hour / 24.0,
                day_of_week / 7.0,
                np.sin(2 * np.pi * hour / 24),
                np.cos(2 * np.pi * hour / 24),
                np.sin(2 * np.pi * day_of_week / 7),
                np.cos(2 * np.pi * day_of_week / 7)
            ])
            
            # Add trend and network features
            if len(recent_metrics) >= 2:
                cpu_trend = (recent_metrics[-1].cpu_percent - recent_metrics[0].cpu_percent) / len(recent_metrics)
                memory_trend = (recent_metrics[-1].memory_percent - recent_metrics[0].memory_percent) / len(recent_metrics)
                features.extend([cpu_trend, memory_trend])
                
                network_bytes = recent_metrics[-1].network_io_bytes / 1e6 if recent_metrics[-1].network_io_bytes else 0
                features.append(network_bytes)
            else:
                features.extend([0.0, 0.0, 0.0])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error extracting current features: {e}")
            return None

    async def _predict_node_demand(self, node_id: str, features: np.ndarray, 
                                 horizon: timedelta) -> Optional[ResourceDemand]:
        """Predict resource demand for specific node"""
        try:
            # Scale features
            features_scaled = self.feature_scaler.transform(features)
            
            # Make predictions
            predicted_cpu = max(0, min(100, self.cpu_predictor.predict(features_scaled)[0]))
            predicted_memory = max(0, min(100, self.memory_predictor.predict(features_scaled)[0]))
            predicted_disk_io = max(0, self.io_predictor.predict(features_scaled)[0])
            predicted_network_io = max(0, self.network_predictor.predict(features_scaled)[0] * 1e6)
            
            # Calculate prediction confidence based on model performance
            # This would be enhanced with actual model confidence intervals
            base_confidence = 0.8
            
            # Adjust confidence based on data recency and volume
            node_metrics_count = sum(1 for nid, _ in self.metrics_history if nid == node_id)
            data_confidence = min(1.0, node_metrics_count / 100.0)
            
            confidence = base_confidence * data_confidence
            
            return ResourceDemand(
                timestamp=datetime.now() + horizon,
                predicted_cpu=predicted_cpu,
                predicted_memory=predicted_memory,
                predicted_disk_io=predicted_disk_io,
                predicted_network_io=predicted_network_io,
                confidence=confidence,
                prediction_horizon=horizon
            )
            
        except Exception as e:
            logger.error(f"Error predicting node demand: {e}")
            return None

    async def generate_resource_actions(self, intent_predictions: List[Tuple[str, float, Dict[str, Any]]]) -> List[ResourceAction]:
        """Generate resource allocation actions based on demand predictions and intent"""
        try:
            actions = []
            current_time = datetime.now()
            
            # Get current resource state
            total_cpu_demand = 0
            total_memory_demand = 0
            total_nodes_available = 0
            
            for node_id, node in self.compute_nodes.items():
                if node.status == "active" and node.current_metrics:
                    total_cpu_demand += node.current_metrics.cpu_percent
                    total_memory_demand += node.current_metrics.memory_percent
                    total_nodes_available += 1
            
            if total_nodes_available == 0:
                return actions
            
            avg_cpu_demand = total_cpu_demand / total_nodes_available
            avg_memory_demand = total_memory_demand / total_nodes_available
            
            # Analyze intent predictions for resource implications
            high_compute_intents = [
                intent for intent, confidence, metadata in intent_predictions
                if intent in ['development', 'high_computation', 'document_work'] and confidence > 0.5
            ]
            
            # Generate actions based on current state and predictions
            
            # 1. Scale up actions if high demand predicted
            if avg_cpu_demand > 80 or any(self.demand_predictions.get(nid, ResourceDemand(
                timestamp=current_time, predicted_cpu=0, predicted_memory=0, 
                predicted_disk_io=0, predicted_network_io=0
            )).predicted_cpu > 85 for nid in self.compute_nodes.keys()):
                
                # Find best node to scale up or add
                scale_up_action = await self._generate_scale_up_action(high_compute_intents)
                if scale_up_action:
                    actions.append(scale_up_action)
            
            # 2. Optimization actions for efficiency
            optimization_actions = await self._generate_optimization_actions()
            actions.extend(optimization_actions)
            
            # 3. Load balancing actions
            if total_nodes_available > 1:
                load_balance_action = await self._generate_load_balance_action()
                if load_balance_action:
                    actions.append(load_balance_action)
            
            # 4. Resource cleanup actions
            cleanup_actions = await self._generate_cleanup_actions()
            actions.extend(cleanup_actions)
            
            # Use Q-learning to select best actions
            selected_actions = await self._select_actions_with_rl(actions)
            
            return selected_actions
            
        except Exception as e:
            logger.error(f"Error generating resource actions: {e}")
            return []

    async def _generate_scale_up_action(self, high_compute_intents: List[str]) -> Optional[ResourceAction]:
        """Generate scale-up action for high demand scenarios"""
        try:
            # Calculate expected benefit and cost
            expected_benefit = len(high_compute_intents) * 0.3  # Heuristic benefit
            
            # Find cheapest available scaling option
            available_nodes = [
                node for node in self.compute_nodes.values()
                if node.status in ["idle", "active"] and node.availability_score > 0.5
            ]
            
            if not available_nodes:
                return None
            
            # Sort by cost efficiency
            available_nodes.sort(key=lambda n: n.cost_per_hour / max(n.max_cpu, 1))
            target_node = available_nodes[0]
            
            # Determine scaling parameters
            if target_node.node_type == "desktop":
                # Scale up CPU frequency or enable turbo
                parameters = {
                    "scaling_governor": "performance",
                    "cpu_freq": "max",
                    "enable_turbo": True
                }
                cost = 0.1  # Power cost increase
            elif target_node.node_type == "chromebox":
                # Activate idle chromebox
                parameters = {
                    "power_state": "active",
                    "cpu_scaling": "performance"
                }
                cost = target_node.cost_per_hour
            else:
                # Cloud VM - scale up instance
                parameters = {
                    "instance_type": "upgrade",
                    "cpu_count": target_node.max_cpu * 2,
                    "memory_gb": target_node.max_memory_gb * 2
                }
                cost = target_node.cost_per_hour * 2
            
            return ResourceAction(
                action_id=f"scale_up_{target_node.node_id}_{int(time.time())}",
                action_type="scale_up",
                target_resource="cpu",
                target_nodes=[target_node.node_id],
                parameters=parameters,
                expected_benefit=expected_benefit,
                cost=cost,
                risk_score=0.2,
                execution_time=timedelta(minutes=2),
                priority=8
            )
            
        except Exception as e:
            logger.error(f"Error generating scale-up action: {e}")
            return None

    async def _generate_optimization_actions(self) -> List[ResourceAction]:
        """Generate optimization actions for resource efficiency"""
        try:
            actions = []
            
            for node_id, node in self.compute_nodes.items():
                if not node.current_metrics:
                    continue
                
                metrics = node.current_metrics
                
                # Memory optimization
                if metrics.memory_percent > 90:
                    actions.append(ResourceAction(
                        action_id=f"optimize_memory_{node_id}_{int(time.time())}",
                        action_type="optimize",
                        target_resource="memory",
                        target_nodes=[node_id],
                        parameters={
                            "action": "clear_cache",
                            "swap_optimization": True,
                            "compress_memory": True
                        },
                        expected_benefit=0.4,
                        cost=0.01,
                        risk_score=0.1,
                        execution_time=timedelta(seconds=30),
                        priority=6
                    ))
                
                # Disk optimization
                if metrics.disk_percent > 85:
                    actions.append(ResourceAction(
                        action_id=f"optimize_disk_{node_id}_{int(time.time())}",
                        action_type="optimize",
                        target_resource="storage",
                        target_nodes=[node_id],
                        parameters={
                            "action": "cleanup_temp",
                            "compress_logs": True,
                            "defragment": node.node_type == "desktop"
                        },
                        expected_benefit=0.3,
                        cost=0.02,
                        risk_score=0.15,
                        execution_time=timedelta(minutes=5),
                        priority=5
                    ))
                
                # CPU optimization
                if metrics.cpu_percent < 20 and node.node_type == "desktop":
                    actions.append(ResourceAction(
                        action_id=f"optimize_cpu_{node_id}_{int(time.time())}",
                        action_type="optimize",
                        target_resource="cpu",
                        target_nodes=[node_id],
                        parameters={
                            "scaling_governor": "powersave",
                            "cpu_freq": "min",
                            "enable_turbo": False
                        },
                        expected_benefit=0.2,
                        cost=-0.05,  # Negative cost = savings
                        risk_score=0.05,
                        execution_time=timedelta(seconds=10),
                        priority=3
                    ))
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating optimization actions: {e}")
            return []

    async def _generate_load_balance_action(self) -> Optional[ResourceAction]:
        """Generate load balancing action"""
        try:
            # Find nodes with unbalanced load
            active_nodes = [
                (node_id, node) for node_id, node in self.compute_nodes.items()
                if node.status == "active" and node.current_metrics
            ]
            
            if len(active_nodes) < 2:
                return None
            
            # Calculate load variance
            cpu_loads = [node.current_metrics.cpu_percent for _, node in active_nodes]
            load_variance = np.var(cpu_loads)
            
            if load_variance < 400:  # Not much variance
                return None
            
            # Find overloaded and underloaded nodes
            avg_load = np.mean(cpu_loads)
            overloaded = [(nid, node) for nid, node in active_nodes 
                         if node.current_metrics.cpu_percent > avg_load + 20]
            underloaded = [(nid, node) for nid, node in active_nodes 
                          if node.current_metrics.cpu_percent < avg_load - 20]
            
            if not overloaded or not underloaded:
                return None
            
            source_node = overloaded[0][0]
            target_node = underloaded[0][0]
            
            return ResourceAction(
                action_id=f"load_balance_{source_node}_{target_node}_{int(time.time())}",
                action_type="migrate",
                target_resource="cpu",
                target_nodes=[source_node, target_node],
                parameters={
                    "migration_type": "process",
                    "source_node": source_node,
                    "target_node": target_node,
                    "process_selection": "high_cpu"
                },
                expected_benefit=0.5,
                cost=0.1,
                risk_score=0.3,
                execution_time=timedelta(minutes=1),
                priority=7
            )
            
        except Exception as e:
            logger.error(f"Error generating load balance action: {e}")
            return None

    async def _generate_cleanup_actions(self) -> List[ResourceAction]:
        """Generate resource cleanup actions"""
        try:
            actions = []
            
            # System-wide cleanup action
            if len(self.metrics_history) > 8000:  # Cleanup old metrics
                actions.append(ResourceAction(
                    action_id=f"cleanup_system_{int(time.time())}",
                    action_type="optimize",
                    target_resource="system",
                    target_nodes=list(self.compute_nodes.keys()),
                    parameters={
                        "action": "cleanup_metrics",
                        "cleanup_logs": True,
                        "cleanup_cache": True
                    },
                    expected_benefit=0.1,
                    cost=0.01,
                    risk_score=0.05,
                    execution_time=timedelta(minutes=2),
                    priority=2
                ))
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating cleanup actions: {e}")
            return []

    async def _select_actions_with_rl(self, candidate_actions: List[ResourceAction]) -> List[ResourceAction]:
        """Select actions using reinforcement learning (Q-learning)"""
        try:
            if not candidate_actions:
                return []
            
            # Get current state representation
            state = self._get_current_state()
            state_hash = self._hash_state(state)
            
            # Calculate Q-values for each action
            action_values = []
            for action in candidate_actions:
                action_key = f"{action.action_type}_{action.target_resource}"
                q_value = self.q_table[state_hash][action_key]
                
                # Combine Q-value with action properties
                value_score = (
                    q_value * 0.4 +
                    action.expected_benefit * 0.3 +
                    (1.0 - action.risk_score) * 0.2 +
                    action.priority / 10.0 * 0.1
                )
                
                action_values.append((action, value_score))
            
            # Sort by value score
            action_values.sort(key=lambda x: x[1], reverse=True)
            
            # Select top actions with exploration
            selected_actions = []
            for action, value in action_values:
                if len(selected_actions) >= 3:  # Limit concurrent actions
                    break
                
                # Epsilon-greedy selection
                if np.random.random() < self.exploration_rate:
                    # Explore: random selection
                    if np.random.random() < 0.5:
                        selected_actions.append(action)
                else:
                    # Exploit: select high-value actions
                    if value > 0.3:  # Minimum value threshold
                        selected_actions.append(action)
            
            # Decay exploration rate
            self.exploration_rate *= self.exploration_decay
            self.exploration_rate = max(self.exploration_rate, 0.01)
            
            return selected_actions
            
        except Exception as e:
            logger.error(f"Error selecting actions with RL: {e}")
            return candidate_actions[:2]  # Fallback to top 2 actions

    def _get_current_state(self) -> Dict[str, float]:
        """Get current system state for RL"""
        try:
            # Aggregate current system state
            total_nodes = len(self.compute_nodes)
            active_nodes = sum(1 for node in self.compute_nodes.values() if node.status == "active")
            
            if active_nodes == 0:
                return {"system_load": 0, "memory_pressure": 0, "node_utilization": 0}
            
            total_cpu = sum(
                node.current_metrics.cpu_percent for node in self.compute_nodes.values()
                if node.current_metrics and node.status == "active"
            )
            total_memory = sum(
                node.current_metrics.memory_percent for node in self.compute_nodes.values()
                if node.current_metrics and node.status == "active"
            )
            
            avg_cpu = total_cpu / active_nodes
            avg_memory = total_memory / active_nodes
            node_utilization = active_nodes / max(total_nodes, 1)
            
            return {
                "system_load": min(avg_cpu / 100.0, 1.0),
                "memory_pressure": min(avg_memory / 100.0, 1.0),
                "node_utilization": node_utilization
            }
            
        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return {"system_load": 0.5, "memory_pressure": 0.5, "node_utilization": 0.5}

    def _hash_state(self, state: Dict[str, float]) -> str:
        """Create hash representation of state for Q-table"""
        try:
            # Discretize continuous state values
            discretized = {}
            for key, value in state.items():
                discretized[key] = int(value * self.state_discretization) / self.state_discretization
            
            # Create hash
            state_str = json.dumps(discretized, sort_keys=True)
            return str(hash(state_str))
            
        except Exception as e:
            logger.error(f"Error hashing state: {e}")
            return "default_state"

    async def execute_resource_action(self, action: ResourceAction) -> bool:
        """Execute a resource allocation action"""
        try:
            logger.info(f"Executing action: {action.action_type} on {action.target_resource} "
                       f"for nodes {action.target_nodes}")
            
            success = False
            start_time = time.time()
            
            if action.action_type == "scale_up":
                success = await self._execute_scale_up(action)
            elif action.action_type == "optimize":
                success = await self._execute_optimization(action)
            elif action.action_type == "migrate":
                success = await self._execute_migration(action)
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                return False
            
            execution_time = time.time() - start_time
            
            # Update Q-learning table based on result
            await self._update_q_learning(action, success)
            
            # Store action result
            await self._store_action_result(action, success, execution_time)
            
            # Add to action history
            self.action_history.append(action)
            if len(self.action_history) > 1000:
                self.action_history = self.action_history[-1000:]
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing resource action: {e}")
            return False

    async def _execute_scale_up(self, action: ResourceAction) -> bool:
        """Execute scale-up action"""
        try:
            target_node = action.target_nodes[0]
            node = self.compute_nodes.get(target_node)
            
            if not node:
                return False
            
            if node.node_type == "desktop":
                # Set CPU scaling governor
                governor = action.parameters.get("scaling_governor", "performance")
                try:
                    subprocess.run([
                        "sudo", "cpupower", "frequency-set", "-g", governor
                    ], check=True, capture_output=True)
                    return True
                except subprocess.CalledProcessError:
                    logger.warning("Failed to set CPU scaling governor")
                    return False
                    
            elif node.node_type == "chromebox":
                # Send activation command to chromebox
                try:
                    url = f"http://{node.address}:8080/api/power"
                    async with asyncio.timeout(30):
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.post(url, json=action.parameters) as response:
                                return response.status == 200
                except Exception:
                    return False
                    
            return False
            
        except Exception as e:
            logger.error(f"Error executing scale-up: {e}")
            return False

    async def _execute_optimization(self, action: ResourceAction) -> bool:
        """Execute optimization action"""
        try:
            if action.target_resource == "memory":
                # Clear system caches
                try:
                    subprocess.run(["sudo", "sync"], check=True)
                    subprocess.run([
                        "sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"
                    ], check=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
                    
            elif action.target_resource == "storage":
                # Clean temporary files
                try:
                    subprocess.run(["sudo", "find", "/tmp", "-type", "f", "-atime", "+7", "-delete"], 
                                 check=True, capture_output=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
                    
            elif action.target_resource == "cpu":
                # Set CPU scaling governor
                governor = action.parameters.get("scaling_governor", "powersave")
                try:
                    subprocess.run([
                        "sudo", "cpupower", "frequency-set", "-g", governor
                    ], check=True, capture_output=True)
                    return True
                except subprocess.CalledProcessError:
                    return False
                    
            return False
            
        except Exception as e:
            logger.error(f"Error executing optimization: {e}")
            return False

    async def _execute_migration(self, action: ResourceAction) -> bool:
        """Execute migration action (simplified)"""
        try:
            # This would implement actual process migration
            # For now, return success for demonstration
            logger.info(f"Migration from {action.parameters.get('source_node')} "
                       f"to {action.parameters.get('target_node')} simulated")
            return True
            
        except Exception as e:
            logger.error(f"Error executing migration: {e}")
            return False

    async def _update_q_learning(self, action: ResourceAction, success: bool):
        """Update Q-learning table based on action result"""
        try:
            # Get state before action (simplified)
            state_hash = self._hash_state(self._get_current_state())
            action_key = f"{action.action_type}_{action.target_resource}"
            
            # Calculate reward
            if success:
                reward = action.expected_benefit - action.cost - action.risk_score * 0.5
            else:
                reward = -action.cost - action.risk_score
            
            # Update Q-value using Q-learning formula
            current_q = self.q_table[state_hash][action_key]
            
            # Simplified next state (would need actual next state)
            next_state_q = 0  # max Q-value for next state
            
            new_q = current_q + self.learning_rate * (
                reward + self.discount_factor * next_state_q - current_q
            )
            
            self.q_table[state_hash][action_key] = new_q
            
            # Store in database
            await self._store_q_value(state_hash, action_key, new_q)
            
        except Exception as e:
            logger.error(f"Error updating Q-learning: {e}")

    async def _store_metrics(self, node_id: str, metrics: ResourceMetrics):
        """Store resource metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO resource_metrics
                    (timestamp, node_id, cpu_percent, memory_percent, disk_percent,
                     network_io_bytes, gpu_percent, load_average, temperature, power_usage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp.isoformat(),
                    node_id,
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_percent,
                    metrics.network_io_bytes,
                    metrics.gpu_percent,
                    metrics.load_average,
                    metrics.temperature,
                    metrics.power_usage
                ))
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")

    async def _store_prediction(self, node_id: str, prediction: ResourceDemand):
        """Store demand prediction in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO demand_predictions
                    (timestamp, prediction_timestamp, predicted_cpu, predicted_memory,
                     predicted_disk_io, predicted_network_io, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    prediction.timestamp.isoformat(),
                    prediction.predicted_cpu,
                    prediction.predicted_memory,
                    prediction.predicted_disk_io,
                    prediction.predicted_network_io,
                    prediction.confidence
                ))
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")

    async def _store_action_result(self, action: ResourceAction, success: bool, execution_time: float):
        """Store action execution result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO resource_actions
                    (action_id, timestamp, action_type, target_resource, target_nodes,
                     parameters, expected_benefit, cost, execution_time_seconds, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action.action_id,
                    datetime.now().isoformat(),
                    action.action_type,
                    action.target_resource,
                    json.dumps(action.target_nodes),
                    json.dumps(action.parameters),
                    action.expected_benefit,
                    action.cost,
                    int(execution_time),
                    success
                ))
        except Exception as e:
            logger.error(f"Error storing action result: {e}")

    async def _store_q_value(self, state_hash: str, action: str, q_value: float):
        """Store Q-learning value"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO q_learning_table
                    (state_hash, action, q_value, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (
                    state_hash,
                    action,
                    q_value,
                    datetime.now().isoformat()
                ))
        except Exception as e:
            logger.error(f"Error storing Q-value: {e}")

    async def get_drap_insights(self) -> Dict[str, Any]:
        """Get comprehensive DRAP insights and status"""
        try:
            current_time = datetime.now()
            
            # Calculate statistics
            total_actions = len(self.action_history)
            successful_actions = sum(1 for _ in self.action_history)  # Simplified
            
            # Node statistics
            node_stats = {}
            for node_id, node in self.compute_nodes.items():
                if node.current_metrics:
                    node_stats[node_id] = {
                        'cpu_percent': node.current_metrics.cpu_percent,
                        'memory_percent': node.current_metrics.memory_percent,
                        'availability_score': node.availability_score,
                        'cost_per_hour': node.cost_per_hour,
                        'status': node.status
                    }
            
            # Recent predictions
            recent_predictions = {}
            for node_id, prediction in self.demand_predictions.items():
                recent_predictions[node_id] = {
                    'predicted_cpu': prediction.predicted_cpu,
                    'predicted_memory': prediction.predicted_memory,
                    'confidence': prediction.confidence,
                    'horizon_minutes': prediction.prediction_horizon.total_seconds() / 60
                }
            
            # Q-learning statistics
            total_states = len(self.q_table)
            total_state_actions = sum(len(actions) for actions in self.q_table.values())
            
            return {
                'system_status': {
                    'total_nodes': len(self.compute_nodes),
                    'active_nodes': sum(1 for n in self.compute_nodes.values() if n.status == "active"),
                    'total_actions_executed': total_actions,
                    'exploration_rate': self.exploration_rate,
                    'last_training': self.last_training.isoformat()
                },
                'node_statistics': node_stats,
                'recent_predictions': recent_predictions,
                'q_learning_stats': {
                    'total_states': total_states,
                    'total_state_actions': total_state_actions,
                    'learning_rate': self.learning_rate,
                    'discount_factor': self.discount_factor
                },
                'metrics_history_size': len(self.metrics_history),
                'last_updated': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting DRAP insights: {e}")
            return {}

# Main DRAP service runner
async def main():
    """Main DRAP service entry point"""
    try:
        # Load configuration
        config = {
            'learning_rate': 0.01,
            'discount_factor': 0.95,
            'exploration_rate': 0.1,
            'prediction_window_minutes': 30,
            'retraining_hours': 2,
            'compute_nodes': {
                'chromeboxes': [
                    {'address': '100.64.0.2', 'capabilities': {'cpu_cores': 4, 'memory_gb': 8}},
                    {'address': '100.64.0.3', 'capabilities': {'cpu_cores': 4, 'memory_gb': 8}}
                ]
            }
        }
        
        # Initialize DRAP
        drap = DynamicResourceAllocationProphet(config)
        
        logger.info("DRAP service started")
        
        # Main service loop
        while True:
            try:
                # Collect metrics
                await drap.collect_resource_metrics()
                
                # Make predictions
                predictions = await drap.predict_resource_demand()
                
                # Generate and execute actions (simplified intent input)
                mock_intents = [("development", 0.8, {}), ("high_computation", 0.6, {})]
                actions = await drap.generate_resource_actions(mock_intents)
                
                # Execute top priority actions
                for action in actions[:2]:  # Execute top 2 actions
                    await drap.execute_resource_action(action)
                
                # Sleep for next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in DRAP main loop: {e}")
                await asyncio.sleep(60)
                
    except KeyboardInterrupt:
        logger.info("DRAP service stopped by user")
    except Exception as e:
        logger.error(f"Error in DRAP service: {e}")


if __name__ == "__main__":
    asyncio.run(main())
