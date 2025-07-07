// Data Processing Worker
// Handles intensive data computations without blocking the main thread

// Worker message types
const MESSAGE_TYPES = {
  PROCESS_NETWORK_DATA: 'process-network-data',
  ANALYZE_ANOMALIES: 'analyze-anomalies',
  COMPUTE_METRICS: 'compute-metrics',
  OPTIMIZE_LAYOUT: 'optimize-layout',
  CLEANUP: 'cleanup'
};

// Performance monitoring
let processingStats = {
  tasksProcessed: 0,
  totalProcessingTime: 0,
  averageProcessingTime: 0,
  peakMemoryUsage: 0
};

// Network analysis algorithms
class NetworkAnalyzer {
  // Force-directed layout algorithm for network visualization
  static computeForceDirectedLayout(nodes, flows, options = {}) {
    const defaultOptions = {
      iterations: 100,
      springLength: 100,
      springStrength: 0.1,
      repulsionStrength: 1000,
      damping: 0.9,
      timeStep: 0.1
    };
    
    const config = { ...defaultOptions, ...options };
    const { iterations, springLength, springStrength, repulsionStrength, damping, timeStep } = config;
    
    // Initialize velocities
    const velocities = nodes.map(() => ({ vx: 0, vy: 0 }));
    const forces = nodes.map(() => ({ fx: 0, fy: 0 }));
    
    for (let iter = 0; iter < iterations; iter++) {
      // Reset forces
      forces.forEach(force => {
        force.fx = 0;
        force.fy = 0;
      });
      
      // Spring forces (edges)
      flows.forEach(flow => {
        const node1 = nodes[flow.from];
        const node2 = nodes[flow.to];
        if (!node1 || !node2) return;
        
        const dx = node2.x - node1.x;
        const dy = node2.y - node1.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 0.1;
        
        const springForce = springStrength * (distance - springLength);
        const fx = (dx / distance) * springForce;
        const fy = (dy / distance) * springForce;
        
        forces[flow.from].fx += fx;
        forces[flow.from].fy += fy;
        forces[flow.to].fx -= fx;
        forces[flow.to].fy -= fy;
      });
      
      // Repulsion forces (all node pairs)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const node1 = nodes[i];
          const node2 = nodes[j];
          
          const dx = node2.x - node1.x;
          const dy = node2.y - node1.y;
          const distanceSquared = dx * dx + dy * dy;
          const distance = Math.sqrt(distanceSquared) || 0.1;
          
          const repulsionForce = repulsionStrength / distanceSquared;
          const fx = (dx / distance) * repulsionForce;
          const fy = (dy / distance) * repulsionForce;
          
          forces[i].fx -= fx;
          forces[i].fy -= fy;
          forces[j].fx += fx;
          forces[j].fy += fy;
        }
      }
      
      // Update positions
      nodes.forEach((node, i) => {
        velocities[i].vx = (velocities[i].vx + forces[i].fx * timeStep) * damping;
        velocities[i].vy = (velocities[i].vy + forces[i].fy * timeStep) * damping;
        
        node.x += velocities[i].vx * timeStep;
        node.y += velocities[i].vy * timeStep;
        
        // Boundary constraints (optional)
        node.x = Math.max(50, Math.min(1850, node.x));
        node.y = Math.max(50, Math.min(950, node.y));
      });
    }
    
    return nodes;
  }
  
  // Detect network anomalies using statistical analysis
  static detectAnomalies(nodes, historicalData = []) {
    const anomalies = [];
    const timestamp = new Date().toISOString();
    
    nodes.forEach((node, index) => {
      const { resources, health, activity } = node;
      
      // Health anomaly detection
      if (health < 0.3) {
        anomalies.push({
          id: `health-${node.id}-${Date.now()}`,
          node: index,
          type: 'performance',
          severity: health < 0.1 ? 'critical' : 'high',
          description: `Node health critically low: ${(health * 100).toFixed(1)}%`,
          confidence: 1 - health,
          timestamp
        });
      }
      
      // Resource exhaustion detection
      const resourceMetrics = [
        { name: 'CPU', value: resources.cpu, threshold: 90 },
        { name: 'Memory', value: resources.memory, threshold: 85 },
        { name: 'Storage', value: resources.storage, threshold: 95 },
        { name: 'Network', value: resources.network, threshold: 80 }
      ];
      
      resourceMetrics.forEach(metric => {
        if (metric.value > metric.threshold) {
          anomalies.push({
            id: `resource-${metric.name.toLowerCase()}-${node.id}-${Date.now()}`,
            node: index,
            type: 'resource',
            severity: metric.value > metric.threshold + 10 ? 'critical' : 'high',
            description: `${metric.name} usage critical: ${metric.value.toFixed(1)}%`,
            confidence: Math.min(1, (metric.value - metric.threshold) / 20),
            timestamp
          });
        }
      });
      
      // Activity pattern anomaly (too high or too low)
      if (activity > 0.95) {
        anomalies.push({
          id: `activity-high-${node.id}-${Date.now()}`,
          node: index,
          type: 'performance',
          severity: 'medium',
          description: `Unusually high activity detected: ${(activity * 100).toFixed(1)}%`,
          confidence: activity,
          timestamp
        });
      } else if (activity < 0.05 && node.status === 'online') {
        anomalies.push({
          id: `activity-low-${node.id}-${Date.now()}`,
          node: index,
          type: 'connectivity',
          severity: 'medium',
          description: `Node appears idle despite online status`,
          confidence: 1 - activity,
          timestamp
        });
      }
    });
    
    return anomalies;
  }
  
  // Compute network metrics and statistics
  static computeNetworkMetrics(nodes, flows) {
    const totalNodes = nodes.length;
    const onlineNodes = nodes.filter(n => n.status === 'online').length;
    const healthyNodes = nodes.filter(n => n.health > 0.7).length;
    
    // Resource utilization
    const avgCpu = nodes.reduce((sum, n) => sum + n.resources.cpu, 0) / totalNodes;
    const avgMemory = nodes.reduce((sum, n) => sum + n.resources.memory, 0) / totalNodes;
    const avgStorage = nodes.reduce((sum, n) => sum + n.resources.storage, 0) / totalNodes;
    const avgNetwork = nodes.reduce((sum, n) => sum + n.resources.network, 0) / totalNodes;
    
    // Network connectivity
    const activeFlows = flows.filter(f => f.status === 'active').length;
    const totalBandwidth = flows.reduce((sum, f) => sum + f.bandwidth, 0);
    const avgLatency = flows.length > 0 
      ? flows.reduce((sum, f) => sum + f.latency, 0) / flows.length 
      : 0;
    
    // Network topology metrics
    const connections = new Map();
    flows.forEach(flow => {
      connections.set(flow.from, (connections.get(flow.from) || 0) + 1);
      connections.set(flow.to, (connections.get(flow.to) || 0) + 1);
    });
    
    const avgConnectivity = connections.size > 0 
      ? Array.from(connections.values()).reduce((sum, count) => sum + count, 0) / connections.size
      : 0;
    
    const maxConnectivity = Math.max(...Array.from(connections.values()), 0);
    
    return {
      topology: {
        totalNodes,
        onlineNodes,
        healthyNodes,
        nodeHealthPercentage: (healthyNodes / totalNodes) * 100,
        networkUptime: (onlineNodes / totalNodes) * 100
      },
      resources: {
        cpu: { average: avgCpu, utilization: avgCpu / 100 },
        memory: { average: avgMemory, utilization: avgMemory / 100 },
        storage: { average: avgStorage, utilization: avgStorage / 100 },
        network: { average: avgNetwork, utilization: avgNetwork / 100 }
      },
      connectivity: {
        activeFlows,
        totalBandwidth,
        averageLatency: avgLatency,
        averageConnectivity: avgConnectivity,
        maxConnectivity,
        networkDensity: (flows.length / (totalNodes * (totalNodes - 1))) * 2 // For undirected graph
      },
      performance: {
        overallHealth: nodes.reduce((sum, n) => sum + n.health, 0) / totalNodes,
        overallActivity: nodes.reduce((sum, n) => sum + n.activity, 0) / totalNodes,
        criticalNodes: nodes.filter(n => n.health < 0.3).length,
        bottleneckFlows: flows.filter(f => f.latency > 100 || f.status === 'congested').length
      }
    };
  }
}

// Data clustering for visualization optimization
class DataClusterer {
  static kMeansCluster(points, k, maxIterations = 100) {
    if (points.length === 0 || k <= 0) return { clusters: [], centroids: [] };
    
    // Initialize centroids randomly
    const centroids = Array.from({ length: k }, () => ({
      x: Math.random() * 1000,
      y: Math.random() * 600
    }));
    
    let clusters = new Array(points.length).fill(0);
    
    for (let iter = 0; iter < maxIterations; iter++) {
      let changed = false;
      
      // Assign points to nearest centroid
      points.forEach((point, i) => {
        let minDistance = Infinity;
        let nearestCluster = 0;
        
        centroids.forEach((centroid, j) => {
          const distance = Math.sqrt(
            Math.pow(point.x - centroid.x, 2) + Math.pow(point.y - centroid.y, 2)
          );
          if (distance < minDistance) {
            minDistance = distance;
            nearestCluster = j;
          }
        });
        
        if (clusters[i] !== nearestCluster) {
          clusters[i] = nearestCluster;
          changed = true;
        }
      });
      
      // Update centroids
      centroids.forEach((centroid, j) => {
        const clusterPoints = points.filter((_, i) => clusters[i] === j);
        if (clusterPoints.length > 0) {
          centroid.x = clusterPoints.reduce((sum, p) => sum + p.x, 0) / clusterPoints.length;
          centroid.y = clusterPoints.reduce((sum, p) => sum + p.y, 0) / clusterPoints.length;
        }
      });
      
      if (!changed) break;
    }
    
    return { clusters, centroids };
  }
}

// Message processing
async function processMessage(message) {
  const startTime = performance.now();
  
  try {
    switch (message.type) {
      case MESSAGE_TYPES.PROCESS_NETWORK_DATA:
        const { nodes, flows } = message.data;
        const metrics = NetworkAnalyzer.computeNetworkMetrics(nodes, flows);
        const anomalies = NetworkAnalyzer.detectAnomalies(nodes);
        
        self.postMessage({
          type: 'network-analysis-complete',
          id: message.id,
          data: { metrics, anomalies },
          processingTime: performance.now() - startTime
        });
        break;
        
      case MESSAGE_TYPES.OPTIMIZE_LAYOUT:
        const optimizedNodes = NetworkAnalyzer.computeForceDirectedLayout(
          message.data.nodes,
          message.data.flows,
          message.options
        );
        
        self.postMessage({
          type: 'layout-optimization-complete',
          id: message.id,
          data: { nodes: optimizedNodes },
          processingTime: performance.now() - startTime
        });
        break;
        
      case MESSAGE_TYPES.ANALYZE_ANOMALIES:
        const detectedAnomalies = NetworkAnalyzer.detectAnomalies(
          message.data.nodes,
          message.data.historicalData
        );
        
        self.postMessage({
          type: 'anomaly-analysis-complete',
          id: message.id,
          data: { anomalies: detectedAnomalies },
          processingTime: performance.now() - startTime
        });
        break;
        
      case MESSAGE_TYPES.COMPUTE_METRICS:
        const computedMetrics = NetworkAnalyzer.computeNetworkMetrics(
          message.data.nodes,
          message.data.flows
        );
        
        // Additional clustering analysis
        const nodePositions = message.data.nodes.map(n => ({ x: n.x, y: n.y }));
        const clusterAnalysis = DataClusterer.kMeansCluster(nodePositions, 3);
        
        self.postMessage({
          type: 'metrics-computation-complete',
          id: message.id,
          data: { 
            metrics: computedMetrics,
            clustering: clusterAnalysis
          },
          processingTime: performance.now() - startTime
        });
        break;
        
      case MESSAGE_TYPES.CLEANUP:
        // Reset processing stats
        processingStats = {
          tasksProcessed: 0,
          totalProcessingTime: 0,
          averageProcessingTime: 0,
          peakMemoryUsage: 0
        };
        
        self.postMessage({
          type: 'cleanup-complete',
          id: message.id
        });
        break;
        
      default:
        throw new Error(`Unknown message type: ${message.type}`);
    }
    
    // Update processing stats
    const processingTime = performance.now() - startTime;
    processingStats.tasksProcessed++;
    processingStats.totalProcessingTime += processingTime;
    processingStats.averageProcessingTime = processingStats.totalProcessingTime / processingStats.tasksProcessed;
    
  } catch (error) {
    self.postMessage({
      type: 'error',
      id: message.id,
      message: error.message,
      processingTime: performance.now() - startTime
    });
  }
}

// Message handler
self.addEventListener('message', (event) => {
  if (event.data.type === 'get-stats') {
    self.postMessage({
      type: 'stats',
      data: processingStats
    });
    return;
  }
  
  processMessage(event.data);
});

// Global error handler
self.addEventListener('error', (event) => {
  self.postMessage({
    type: 'error',
    message: `Worker error: ${event.message}`,
    filename: event.filename,
    lineno: event.lineno
  });
});
