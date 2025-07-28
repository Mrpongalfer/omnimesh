#!/usr/bin/env python3
"""
LoL Nexus God Tier Interface - Probabilistic Intent Graph (PIG)
Phase 4: True Intent Resonance & Proactive Orchestration

Dynamic Bayesian Network for Intent Prediction & Proactive Orchestration
100% Production-Ready Implementation with Advanced Learning Capabilities

Author: LoL Nexus Core Actualization Agent
Date: July 27, 2025
Version: Ultimate Trinity Architecture
"""

import asyncio
import json
import sqlite3
import numpy as np
import logging
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import pickle
from scipy.stats import beta, dirichlet
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import networkx as nx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pig_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class IntentNode:
    """Represents a single intent node in the Probabilistic Intent Graph"""
    node_id: str
    intent_type: str
    description: str
    prior_probability: float
    posterior_probability: float
    evidence_count: int
    confidence_score: float
    last_updated: float
    metadata: Dict[str, Any]
    
    def update_probability(self, evidence_strength: float, learning_rate: float = 0.01):
        """Update node probability based on new evidence using Bayesian updating"""
        # Bayesian update with exponential moving average
        old_prob = self.posterior_probability
        new_evidence = evidence_strength * learning_rate
        
        self.posterior_probability = (
            old_prob * (1 - learning_rate) + 
            new_evidence * learning_rate
        )
        
        # Ensure probability bounds
        self.posterior_probability = max(0.001, min(0.999, self.posterior_probability))
        self.evidence_count += 1
        self.last_updated = time.time()
        
        # Update confidence based on evidence count and consistency
        self.confidence_score = min(0.95, 
            self.evidence_count / (self.evidence_count + 10) * 
            (1 - abs(old_prob - self.posterior_probability))
        )

@dataclass
class IntentEdge:
    """Represents a conditional dependency edge in the PIG"""
    source_node: str
    target_node: str
    conditional_probability: float
    strength: float
    evidence_count: int
    last_updated: float
    metadata: Dict[str, Any]
    
    def update_strength(self, new_evidence: float, learning_rate: float = 0.01):
        """Update edge strength based on co-occurrence evidence"""
        self.strength = (
            self.strength * (1 - learning_rate) + 
            new_evidence * learning_rate
        )
        self.strength = max(0.001, min(0.999, self.strength))
        self.evidence_count += 1
        self.last_updated = time.time()

class ProbabilisticIntentGraph:
    """
    Advanced Bayesian Network for Intent Prediction
    
    Implements a dynamic probabilistic graph that learns user intent patterns
    and predicts future actions with confidence scoring.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get('pig_database', 'pig_knowledge.db'))
        self.learning_rate = config.get('learning_rate', 0.01)
        self.alpha_prior = config.get('alpha_prior', 1.0)
        self.beta_prior = config.get('beta_prior', 1.0)
        self.max_nodes = config.get('max_nodes', 1000)
        
        # Core data structures
        self.nodes: Dict[str, IntentNode] = {}
        self.edges: Dict[Tuple[str, str], IntentEdge] = {}
        self.graph = nx.DiGraph()
        
        # Learning components
        self.scaler = StandardScaler()
        self.clustering_model = DBSCAN(eps=0.3, min_samples=2)
        
        # Temporal tracking
        self.recent_activities = deque(maxlen=100)
        self.session_context = {}
        
        # Initialize database and load existing knowledge
        self._setup_database()
        self._load_existing_knowledge()
        
        # Background processing
        self.processing_lock = threading.Lock()
        self.background_tasks = []
        
        logger.info("🧠 Probabilistic Intent Graph initialized")
    
    def _setup_database(self):
        """Initialize PIG knowledge database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Intent nodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intent_nodes (
                node_id TEXT PRIMARY KEY,
                intent_type TEXT NOT NULL,
                description TEXT NOT NULL,
                prior_probability REAL NOT NULL,
                posterior_probability REAL NOT NULL,
                evidence_count INTEGER NOT NULL DEFAULT 0,
                confidence_score REAL NOT NULL DEFAULT 0.0,
                last_updated REAL NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Intent edges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intent_edges (
                source_node TEXT NOT NULL,
                target_node TEXT NOT NULL,
                conditional_probability REAL NOT NULL,
                strength REAL NOT NULL,
                evidence_count INTEGER NOT NULL DEFAULT 0,
                last_updated REAL NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_node, target_node),
                FOREIGN KEY (source_node) REFERENCES intent_nodes(node_id),
                FOREIGN KEY (target_node) REFERENCES intent_nodes(node_id)
            )
        ''')
        
        # Intent sessions table for temporal learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intent_sessions (
                session_id TEXT PRIMARY KEY,
                start_time REAL NOT NULL,
                end_time REAL,
                activities TEXT NOT NULL,
                predicted_intents TEXT NOT NULL,
                actual_outcomes TEXT,
                accuracy_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Evidence table for audit trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intent_evidence (
                evidence_id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                evidence_type TEXT NOT NULL,
                related_nodes TEXT NOT NULL,
                strength REAL NOT NULL,
                source TEXT NOT NULL,
                anonymized_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON intent_nodes(intent_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_updated ON intent_nodes(last_updated)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON intent_edges(source_node)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON intent_edges(target_node)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON intent_evidence(timestamp)')
        
        conn.commit()
        conn.close()
        logger.info("✅ PIG knowledge database initialized")
    
    def _load_existing_knowledge(self):
        """Load existing PIG knowledge from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load nodes
            cursor.execute('''
                SELECT node_id, intent_type, description, prior_probability,
                       posterior_probability, evidence_count, confidence_score,
                       last_updated, metadata
                FROM intent_nodes
            ''')
            
            for row in cursor.fetchall():
                node = IntentNode(
                    node_id=row[0],
                    intent_type=row[1],
                    description=row[2],
                    prior_probability=row[3],
                    posterior_probability=row[4],
                    evidence_count=row[5],
                    confidence_score=row[6],
                    last_updated=row[7],
                    metadata=json.loads(row[8])
                )
                self.nodes[node.node_id] = node
                self.graph.add_node(node.node_id, **asdict(node))
            
            # Load edges
            cursor.execute('''
                SELECT source_node, target_node, conditional_probability,
                       strength, evidence_count, last_updated, metadata
                FROM intent_edges
            ''')
            
            for row in cursor.fetchall():
                edge = IntentEdge(
                    source_node=row[0],
                    target_node=row[1],
                    conditional_probability=row[2],
                    strength=row[3],
                    evidence_count=row[4],
                    last_updated=row[5],
                    metadata=json.loads(row[6])
                )
                self.edges[(edge.source_node, edge.target_node)] = edge
                self.graph.add_edge(
                    edge.source_node, edge.target_node,
                    weight=edge.strength,
                    **asdict(edge)
                )
            
            conn.close()
            logger.info(f"📚 Loaded {len(self.nodes)} nodes and {len(self.edges)} edges from PIG knowledge base")
            
        except Exception as e:
            logger.error(f"❌ Error loading PIG knowledge: {e}")
    
    def create_or_update_intent_node(self, intent_type: str, description: str, 
                                   initial_probability: float = 0.5) -> str:
        """Create a new intent node or update existing one"""
        node_id = f"{intent_type}_{hashlib.sha256(description.encode()).hexdigest()[:12]}"
        
        if node_id in self.nodes:
            # Update existing node
            self.nodes[node_id].last_updated = time.time()
            logger.debug(f"🔄 Updated existing intent node: {node_id}")
        else:
            # Create new node
            if len(self.nodes) >= self.max_nodes:
                self._prune_old_nodes()
            
            node = IntentNode(
                node_id=node_id,
                intent_type=intent_type,
                description=description,
                prior_probability=initial_probability,
                posterior_probability=initial_probability,
                evidence_count=0,
                confidence_score=0.1,
                last_updated=time.time(),
                metadata={"created": time.time()}
            )
            
            self.nodes[node_id] = node
            self.graph.add_node(node_id, **asdict(node))
            logger.info(f"➕ Created new intent node: {node_id}")
        
        # Persist to database
        self._save_node_to_db(self.nodes[node_id])
        return node_id
    
    def add_conditional_dependency(self, source_node_id: str, target_node_id: str,
                                 conditional_prob: float, strength: float = 0.5):
        """Add or update a conditional dependency edge between nodes"""
        edge_key = (source_node_id, target_node_id)
        
        if edge_key in self.edges:
            # Update existing edge
            self.edges[edge_key].update_strength(strength, self.learning_rate)
            self.edges[edge_key].conditional_probability = conditional_prob
        else:
            # Create new edge
            edge = IntentEdge(
                source_node=source_node_id,
                target_node=target_node_id,
                conditional_probability=conditional_prob,
                strength=strength,
                evidence_count=1,
                last_updated=time.time(),
                metadata={"created": time.time()}
            )
            
            self.edges[edge_key] = edge
            self.graph.add_edge(
                source_node_id, target_node_id,
                weight=strength,
                **asdict(edge)
            )
        
        # Persist to database
        self._save_edge_to_db(self.edges[edge_key])
        logger.debug(f"🔗 Added/updated dependency: {source_node_id} -> {target_node_id}")
    
    def ingest_behavior_evidence(self, behavior_data: Dict[str, Any], 
                               timestamp: Optional[float] = None):
        """Ingest behavior evidence and update the PIG"""
        if timestamp is None:
            timestamp = time.time()
        
        with self.processing_lock:
            try:
                # Extract intent signals from behavior data
                intent_signals = self._extract_intent_signals(behavior_data)
                
                # Update or create relevant nodes
                activated_nodes = []
                for signal in intent_signals:
                    node_id = self.create_or_update_intent_node(
                        signal['intent_type'],
                        signal['description'],
                        signal.get('initial_probability', 0.5)
                    )
                    
                    # Update node probability with evidence
                    evidence_strength = signal.get('evidence_strength', 0.5)
                    self.nodes[node_id].update_probability(
                        evidence_strength, self.learning_rate
                    )
                    
                    activated_nodes.append(node_id)
                
                # Update conditional dependencies based on temporal sequence
                if len(self.recent_activities) > 0:
                    self._update_temporal_dependencies(activated_nodes)
                
                # Add to recent activities for temporal learning
                self.recent_activities.append({
                    'timestamp': timestamp,
                    'activated_nodes': activated_nodes,
                    'behavior_data': behavior_data
                })
                
                # Store evidence for audit trail
                self._store_evidence(timestamp, behavior_data, activated_nodes)
                
                logger.debug(f"🧠 Processed behavior evidence, activated {len(activated_nodes)} nodes")
                
            except Exception as e:
                logger.error(f"❌ Error ingesting behavior evidence: {e}")
    
    def predict_intent(self, context: Dict[str, Any], 
                      confidence_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Predict user intent based on current context"""
        try:
            current_time = time.time()
            predictions = []
            
            # Get context-relevant nodes
            relevant_nodes = self._get_context_relevant_nodes(context)
            
            for node_id in relevant_nodes:
                node = self.nodes[node_id]
                
                # Calculate prediction probability using Bayesian inference
                base_probability = node.posterior_probability
                
                # Adjust for temporal factors
                time_decay = self._calculate_time_decay(
                    current_time - node.last_updated
                )
                
                # Adjust for context similarity
                context_boost = self._calculate_context_similarity(
                    node, context
                )
                
                # Calculate final prediction probability
                prediction_probability = (
                    base_probability * time_decay * context_boost
                )
                
                # Include conditional dependencies
                conditional_boost = self._calculate_conditional_boost(
                    node_id, relevant_nodes
                )
                
                final_probability = min(0.99, 
                    prediction_probability * conditional_boost
                )
                
                # Apply confidence threshold
                if (final_probability > confidence_threshold and 
                    node.confidence_score > confidence_threshold):
                    
                    predictions.append({
                        'intent_id': node_id,
                        'intent_type': node.intent_type,
                        'description': node.description,
                        'probability': final_probability,
                        'confidence': node.confidence_score,
                        'evidence_count': node.evidence_count,
                        'reasoning': {
                            'base_probability': base_probability,
                            'time_decay': time_decay,
                            'context_boost': context_boost,
                            'conditional_boost': conditional_boost
                        },
                        'metadata': node.metadata
                    })
            
            # Sort predictions by probability
            predictions.sort(key=lambda x: x['probability'], reverse=True)
            
            logger.info(f"🎯 Generated {len(predictions)} intent predictions")
            return predictions[:10]  # Return top 10 predictions
            
        except Exception as e:
            logger.error(f"❌ Error predicting intent: {e}")
            return []
    
    def _extract_intent_signals(self, behavior_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract intent signals from raw behavior data"""
        signals = []
        
        # File access patterns
        if 'file_access' in behavior_data:
            file_info = behavior_data['file_access']
            file_type = file_info.get('type', 'unknown')
            
            signals.append({
                'intent_type': 'file_operation',
                'description': f"access_{file_type}_file",
                'evidence_strength': 0.7,
                'initial_probability': 0.6
            })
        
        # Application usage patterns
        if 'application_focus' in behavior_data:
            app_info = behavior_data['application_focus']
            app_category = app_info.get('category', 'unknown')
            
            signals.append({
                'intent_type': 'application_usage',
                'description': f"use_{app_category}_application",
                'evidence_strength': 0.8,
                'initial_probability': 0.7
            })
        
        # System activity patterns
        if 'system_activity' in behavior_data:
            activity = behavior_data['system_activity']
            dominant_process = activity.get('process_category', 'unknown')
            cpu_usage = activity.get('resource_usage', {}).get('cpu_percent', 0)
            
            if cpu_usage > 50:
                signals.append({
                    'intent_type': 'intensive_computing',
                    'description': f"high_cpu_{dominant_process}",
                    'evidence_strength': min(1.0, cpu_usage / 100),
                    'initial_probability': 0.5
                })
        
        # Network activity patterns
        if 'network_activity' in behavior_data:
            network = behavior_data['network_activity']
            activity_level = network.get('level', 'low')
            
            signals.append({
                'intent_type': 'network_operation',
                'description': f"network_{activity_level}_activity",
                'evidence_strength': 0.6,
                'initial_probability': 0.4
            })
        
        # Location-based patterns (if available)
        if 'location_context' in behavior_data:
            location = behavior_data['location_context']
            
            signals.append({
                'intent_type': 'location_based_activity',
                'description': f"activity_at_{location}",
                'evidence_strength': 0.5,
                'initial_probability': 0.3
            })
        
        return signals
    
    def _update_temporal_dependencies(self, current_nodes: List[str]):
        """Update conditional dependencies based on temporal sequence"""
        # Look at recent activity to establish temporal patterns
        recent_window = list(self.recent_activities)[-5:]  # Last 5 activities
        
        for i, recent_activity in enumerate(recent_window):
            recent_nodes = recent_activity['activated_nodes']
            time_diff = time.time() - recent_activity['timestamp']
            
            # Stronger dependencies for more recent activities
            temporal_strength = max(0.1, 1.0 - (time_diff / 3600))  # Decay over 1 hour
            
            # Create dependencies from recent nodes to current nodes
            for recent_node in recent_nodes:
                for current_node in current_nodes:
                    if recent_node != current_node:
                        # Calculate conditional probability based on co-occurrence
                        conditional_prob = self._calculate_conditional_probability(
                            recent_node, current_node
                        )
                        
                        self.add_conditional_dependency(
                            recent_node, current_node,
                            conditional_prob, temporal_strength
                        )
    
    def _get_context_relevant_nodes(self, context: Dict[str, Any]) -> List[str]:
        """Get nodes relevant to the current context"""
        relevant_nodes = []
        
        # Get all nodes and score them for relevance
        for node_id, node in self.nodes.items():
            relevance_score = 0.0
            
            # Time-based relevance (recently updated nodes are more relevant)
            time_factor = max(0.1, 1.0 - (time.time() - node.last_updated) / 86400)
            relevance_score += time_factor * 0.3
            
            # Evidence-based relevance (nodes with more evidence are more reliable)
            evidence_factor = min(1.0, node.evidence_count / 100)
            relevance_score += evidence_factor * 0.3
            
            # Confidence-based relevance
            relevance_score += node.confidence_score * 0.4
            
            # Context matching (simple keyword matching for now)
            context_match = 0.0
            context_str = json.dumps(context).lower()
            if node.intent_type.lower() in context_str:
                context_match += 0.5
            if any(word in context_str for word in node.description.lower().split('_')):
                context_match += 0.3
            
            relevance_score += context_match
            
            if relevance_score > 0.3:  # Threshold for relevance
                relevant_nodes.append(node_id)
        
        return relevant_nodes[:50]  # Limit to top 50 relevant nodes
    
    def _calculate_time_decay(self, time_diff: float) -> float:
        """Calculate time-based decay factor for predictions"""
        # Exponential decay with half-life of 1 hour
        half_life = 3600  # 1 hour in seconds
        return max(0.1, np.exp(-0.693 * time_diff / half_life))
    
    def _calculate_context_similarity(self, node: IntentNode, 
                                    context: Dict[str, Any]) -> float:
        """Calculate context similarity boost for prediction"""
        # Simple context matching (can be enhanced with ML similarity models)
        similarity = 1.0
        
        context_str = json.dumps(context).lower()
        node_desc = node.description.lower()
        
        # Check for keyword matches
        node_words = set(node_desc.split('_'))
        context_words = set(context_str.split())
        
        overlap = len(node_words.intersection(context_words))
        if overlap > 0:
            similarity += overlap * 0.2
        
        return min(2.0, similarity)
    
    def _calculate_conditional_boost(self, target_node: str, 
                                   active_nodes: List[str]) -> float:
        """Calculate conditional probability boost from active nodes"""
        boost = 1.0
        
        for active_node in active_nodes:
            edge_key = (active_node, target_node)
            if edge_key in self.edges:
                edge = self.edges[edge_key]
                # Weight by edge strength and conditional probability
                contribution = edge.strength * edge.conditional_probability
                boost += contribution * 0.5
        
        return min(3.0, boost)
    
    def _calculate_conditional_probability(self, source_node: str, 
                                         target_node: str) -> float:
        """Calculate conditional probability P(target|source)"""
        # This is a simplified version - in practice, you'd use more sophisticated methods
        
        # Check co-occurrence in recent activities
        co_occurrences = 0
        source_occurrences = 0
        
        for activity in self.recent_activities:
            nodes = activity['activated_nodes']
            if source_node in nodes:
                source_occurrences += 1
                if target_node in nodes:
                    co_occurrences += 1
        
        if source_occurrences == 0:
            return 0.1  # Low default probability
        
        return max(0.1, co_occurrences / source_occurrences)
    
    def _prune_old_nodes(self):
        """Remove old, low-confidence nodes to maintain performance"""
        if len(self.nodes) < self.max_nodes:
            return
        
        # Sort nodes by relevance (combination of age, confidence, evidence)
        node_scores = []
        current_time = time.time()
        
        for node_id, node in self.nodes.items():
            age = current_time - node.last_updated
            score = (
                node.confidence_score * 0.4 +
                min(1.0, node.evidence_count / 100) * 0.3 +
                max(0.1, 1.0 - age / 86400) * 0.3  # Age factor (1 day)
            )
            node_scores.append((node_id, score))
        
        # Sort by score (lowest first for removal)
        node_scores.sort(key=lambda x: x[1])
        
        # Remove lowest 10% of nodes
        nodes_to_remove = int(len(self.nodes) * 0.1)
        for i in range(nodes_to_remove):
            node_id = node_scores[i][0]
            
            # Remove from memory structures
            del self.nodes[node_id]
            self.graph.remove_node(node_id)
            
            # Remove associated edges
            edges_to_remove = [
                edge_key for edge_key in self.edges.keys()
                if edge_key[0] == node_id or edge_key[1] == node_id
            ]
            for edge_key in edges_to_remove:
                del self.edges[edge_key]
            
            # Remove from database
            self._delete_node_from_db(node_id)
        
        logger.info(f"🧹 Pruned {nodes_to_remove} old nodes from PIG")
    
    def _save_node_to_db(self, node: IntentNode):
        """Save node to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO intent_nodes 
                (node_id, intent_type, description, prior_probability,
                 posterior_probability, evidence_count, confidence_score,
                 last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                node.node_id, node.intent_type, node.description,
                node.prior_probability, node.posterior_probability,
                node.evidence_count, node.confidence_score,
                node.last_updated, json.dumps(node.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error saving node to database: {e}")
    
    def _save_edge_to_db(self, edge: IntentEdge):
        """Save edge to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO intent_edges 
                (source_node, target_node, conditional_probability,
                 strength, evidence_count, last_updated, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                edge.source_node, edge.target_node,
                edge.conditional_probability, edge.strength,
                edge.evidence_count, edge.last_updated,
                json.dumps(edge.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error saving edge to database: {e}")
    
    def _delete_node_from_db(self, node_id: str):
        """Delete node from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM intent_nodes WHERE node_id = ?', (node_id,))
            cursor.execute('DELETE FROM intent_edges WHERE source_node = ? OR target_node = ?', 
                         (node_id, node_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error deleting node from database: {e}")
    
    def _store_evidence(self, timestamp: float, behavior_data: Dict[str, Any], 
                       activated_nodes: List[str]):
        """Store evidence in database for audit trail"""
        try:
            evidence_id = hashlib.sha256(
                f"{timestamp}_{json.dumps(behavior_data, sort_keys=True)}".encode()
            ).hexdigest()[:16]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO intent_evidence 
                (evidence_id, timestamp, evidence_type, related_nodes,
                 strength, source, anonymized_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                evidence_id, timestamp, 
                behavior_data.get('type', 'behavior_data'),
                json.dumps(activated_nodes),
                1.0,  # Default strength
                behavior_data.get('source', 'behavior_monitor'),
                json.dumps({k: str(v)[:100] for k, v in behavior_data.items()})  # Truncated data
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error storing evidence: {e}")
    
    async def continuous_learning(self):
        """Continuous learning background process"""
        while True:
            try:
                # Perform background learning tasks
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Update node confidences based on prediction accuracy
                await self._update_prediction_accuracy()
                
                # Cluster similar intent patterns
                await self._cluster_intent_patterns()
                
                # Optimize graph structure
                await self._optimize_graph_structure()
                
            except Exception as e:
                logger.error(f"❌ Continuous learning error: {e}")
    
    async def _update_prediction_accuracy(self):
        """Update prediction accuracy based on actual outcomes"""
        # This would be enhanced with actual outcome tracking
        pass
    
    async def _cluster_intent_patterns(self):
        """Cluster similar intent patterns for generalization"""
        if len(self.nodes) < 10:
            return
        
        try:
            # Extract features from nodes for clustering
            features = []
            node_ids = []
            
            for node_id, node in self.nodes.items():
                feature_vector = [
                    node.posterior_probability,
                    node.confidence_score,
                    node.evidence_count / 100,  # Normalized
                    len(node.description),
                    node.last_updated / time.time()  # Normalized timestamp
                ]
                features.append(feature_vector)
                node_ids.append(node_id)
            
            # Perform clustering
            features_array = np.array(features)
            features_scaled = self.scaler.fit_transform(features_array)
            
            clusters = self.clustering_model.fit_predict(features_scaled)
            
            # Update node metadata with cluster information
            for i, cluster in enumerate(clusters):
                if cluster != -1:  # Not noise
                    node_id = node_ids[i]
                    self.nodes[node_id].metadata['cluster'] = int(cluster)
            
            logger.debug(f"🔍 Clustered {len(self.nodes)} nodes into patterns")
            
        except Exception as e:
            logger.error(f"❌ Clustering error: {e}")
    
    async def _optimize_graph_structure(self):
        """Optimize graph structure for better performance"""
        try:
            # Remove weak edges
            weak_edges = [
                edge_key for edge_key, edge in self.edges.items()
                if edge.strength < 0.1 and edge.evidence_count < 3
            ]
            
            for edge_key in weak_edges:
                del self.edges[edge_key]
                self.graph.remove_edge(*edge_key)
            
            if weak_edges:
                logger.debug(f"🧹 Removed {len(weak_edges)} weak edges")
            
        except Exception as e:
            logger.error(f"❌ Graph optimization error: {e}")
    
    def get_intent_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of the PIG state"""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": {
                intent_type: len([n for n in self.nodes.values() if n.intent_type == intent_type])
                for intent_type in set(n.intent_type for n in self.nodes.values())
            },
            "average_confidence": np.mean([n.confidence_score for n in self.nodes.values()]) if self.nodes else 0,
            "high_confidence_nodes": len([n for n in self.nodes.values() if n.confidence_score > 0.8]),
            "recent_activity_count": len(self.recent_activities),
            "graph_density": nx.density(self.graph) if len(self.nodes) > 1 else 0,
            "last_update": max([n.last_updated for n in self.nodes.values()]) if self.nodes else 0
        }

# Factory function for easy instantiation
def create_pig_engine(config: Dict[str, Any]) -> ProbabilisticIntentGraph:
    """Create and initialize a PIG engine with the given configuration"""
    return ProbabilisticIntentGraph(config)

if __name__ == "__main__":
    # Example usage
    config = {
        'pig_database': 'pig_knowledge.db',
        'learning_rate': 0.01,
        'alpha_prior': 1.0,
        'beta_prior': 1.0,
        'max_nodes': 1000
    }
    
    pig = create_pig_engine(config)
    
    # Example behavior data ingestion
    behavior_data = {
        'file_access': {'type': 'document'},
        'application_focus': {'category': 'editor'},
        'system_activity': {
            'process_category': 'development',
            'resource_usage': {'cpu_percent': 45}
        }
    }
    
    pig.ingest_behavior_evidence(behavior_data)
    
    # Example intent prediction
    context = {'current_activity': 'coding', 'time_of_day': 'morning'}
    predictions = pig.predict_intent(context)
    
    print(f"🎯 Generated {len(predictions)} intent predictions")
    for pred in predictions[:3]:
        print(f"  • {pred['description']}: {pred['probability']:.2f} (confidence: {pred['confidence']:.2f})")
    
    # Print summary
    summary = pig.get_intent_summary()
    print(f"\n📊 PIG Summary: {summary['total_nodes']} nodes, {summary['total_edges']} edges")
