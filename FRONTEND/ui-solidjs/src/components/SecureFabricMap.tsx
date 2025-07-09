import { onCleanup, onMount, createSignal, createEffect, batch } from 'solid-js';
import * as PIXI from 'pixi.js';
import * as d3 from 'd3';
import {
  selectedNode,
  setSelectedNode,
  setExplainableAI,
  nodes,
  agents,
  anomalies,
  flows,
} from '../store/appState';

// Security and performance configuration
const FABRIC_MAP_CONFIG = {
  MAX_NODES: 1000,
  MAX_EDGES: 2000,
  VIEWPORT_NODES: 200,
  LEVEL_OF_DETAIL_THRESHOLD: 0.5,
  FRAME_RATE_LIMIT: 60,
  MEMORY_WARNING_THRESHOLD: 100 * 1024 * 1024, // 100MB
  ZOOM_LIMITS: { min: 0.1, max: 10 },
  CULLING_ENABLED: true,
  VIRTUALIZATION_ENABLED: true,
  PERFORMANCE_MONITORING: true,
} as const;

interface NodeData {
  id: string;
  x: number;
  y: number;
  type: string;
  status: string;
  connections: string[];
  metadata: Record<string, any>;
}

interface EdgeData {
  id: string;
  source: string;
  target: string;
  weight: number;
  type: string;
}

interface ViewportBounds {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}

// Performance monitoring
class PerformanceMonitor {
  private frameCount = 0;
  private lastFrameTime = 0;
  private avgFrameTime = 0;
  private memoryUsage = 0;
  private renderTime = 0;
  
  private onPerformanceAlert?: (metric: string, value: number) => void;
  
  constructor(onAlert?: (metric: string, value: number) => void) {
    this.onPerformanceAlert = onAlert;
  }
  
  startFrame() {
    this.lastFrameTime = performance.now();
  }
  
  endFrame() {
    const currentTime = performance.now();
    this.renderTime = currentTime - this.lastFrameTime;
    this.frameCount++;
    
    // Calculate average frame time
    this.avgFrameTime = (this.avgFrameTime * (this.frameCount - 1) + this.renderTime) / this.frameCount;
    
    // Check for performance issues
    if (this.renderTime > 16.67) { // 60 FPS threshold
      this.onPerformanceAlert?.('frame_time', this.renderTime);
    }
    
    // Monitor memory usage
    if ((performance as any).memory) {
      this.memoryUsage = (performance as any).memory.usedJSHeapSize;
      if (this.memoryUsage > FABRIC_MAP_CONFIG.MEMORY_WARNING_THRESHOLD) {
        this.onPerformanceAlert?.('memory_usage', this.memoryUsage);
      }
    }
  }
  
  getMetrics() {
    return {
      frameCount: this.frameCount,
      avgFrameTime: this.avgFrameTime,
      memoryUsage: this.memoryUsage,
      fps: this.avgFrameTime > 0 ? 1000 / this.avgFrameTime : 0,
    };
  }
}

// Virtualization manager for handling large datasets
class VirtualizationManager {
  private visibleNodes: Set<string> = new Set();
  private visibleEdges: Set<string> = new Set();
  private nodeQuadTree: d3.Quadtree<NodeData> | null = null;
  
  constructor(private viewport: ViewportBounds) {}
  
  updateViewport(bounds: ViewportBounds) {
    this.viewport = bounds;
    this.updateVisibleItems();
  }
  
  setNodes(nodes: NodeData[]) {
    // Limit total nodes for performance
    const limitedNodes = nodes.slice(0, FABRIC_MAP_CONFIG.MAX_NODES);
    
    // Build quad tree for efficient spatial queries
    this.nodeQuadTree = d3.quadtree<NodeData>()
      .x(d => d.x)
      .y(d => d.y)
      .addAll(limitedNodes);
      
    this.updateVisibleItems();
  }
  
  private updateVisibleItems() {
    if (!this.nodeQuadTree) return;
    
    this.visibleNodes.clear();
    this.visibleEdges.clear();
    
    // Find nodes in viewport using quad tree
    const padding = 100; // Add padding for smooth scrolling
    this.nodeQuadTree.visit((node, x1, y1, x2, y2) => {
      if (!node.length) {
        const nodeData = node.data as NodeData;
        if (nodeData &&
            nodeData.x >= this.viewport.minX - padding &&
            nodeData.x <= this.viewport.maxX + padding &&
            nodeData.y >= this.viewport.minY - padding &&
            nodeData.y <= this.viewport.maxY + padding) {
          this.visibleNodes.add(nodeData.id);
        }
      }
      
      // Continue visiting if quad intersects viewport
      return x1 >= this.viewport.maxX + padding || 
             y1 >= this.viewport.maxY + padding || 
             x2 < this.viewport.minX - padding || 
             y2 < this.viewport.minY - padding;
    });
    
    // Limit visible nodes for performance
    if (this.visibleNodes.size > FABRIC_MAP_CONFIG.VIEWPORT_NODES) {
      const nodeArray = Array.from(this.visibleNodes);
      this.visibleNodes = new Set(nodeArray.slice(0, FABRIC_MAP_CONFIG.VIEWPORT_NODES));
    }
  }
  
  getVisibleNodes(): Set<string> {
    return this.visibleNodes;
  }
  
  getVisibleEdges(): Set<string> {
    return this.visibleEdges;
  }
  
  shouldRenderNode(nodeId: string): boolean {
    return this.visibleNodes.has(nodeId);
  }
}

// Level of detail manager
class LevelOfDetailManager {
  private detailLevel: 'high' | 'medium' | 'low' = 'high';
  
  updateDetailLevel(zoomLevel: number) {
    if (zoomLevel < 0.3) {
      this.detailLevel = 'low';
    } else if (zoomLevel < 0.7) {
      this.detailLevel = 'medium';
    } else {
      this.detailLevel = 'high';
    }
  }
  
  getDetailLevel(): 'high' | 'medium' | 'low' {
    return this.detailLevel;
  }
  
  shouldRenderLabels(): boolean {
    return this.detailLevel === 'high';
  }
  
  shouldRenderDetails(): boolean {
    return this.detailLevel !== 'low';
  }
  
  getNodeSize(baseSize: number): number {
    switch (this.detailLevel) {
      case 'low': return Math.max(2, baseSize * 0.5);
      case 'medium': return Math.max(4, baseSize * 0.8);
      case 'high': return baseSize;
    }
  }
}

// Secure FabricMap component with performance optimizations
export default function SecureFabricMap() {
  let container: HTMLDivElement | undefined;
  let app: PIXI.Application | undefined;
  let d3Container: HTMLDivElement | undefined;
  let camera = { x: 0, y: 0, zoom: 1 };
  let dragging = false;
  let lastPos = { x: 0, y: 0 };
  let animationFrameId: number | null = null;
  
  const [focusedNodeIndex, setFocusedNodeIndex] = createSignal(0);
  const [showExplainableOverlay, setShowExplainableOverlay] = createSignal(false);
  const [performanceWarning, setPerformanceWarning] = createSignal<string | null>(null);
  const [isPerformanceMode, setIsPerformanceMode] = createSignal(false);
  
  // Performance and virtualization managers
  const performanceMonitor = new PerformanceMonitor((metric, value) => {
    console.warn(`Performance warning: ${metric} = ${value}`);
    setPerformanceWarning(`Performance issue detected: ${metric}`);
    
    // Automatically enable performance mode if needed
    if (metric === 'frame_time' && value > 33.33) { // 30 FPS threshold
      setIsPerformanceMode(true);
    }
  });
  
  const virtualizationManager = new VirtualizationManager({
    minX: -1000, maxX: 1000, minY: -1000, maxY: 1000
  });
  
  const lodManager = new LevelOfDetailManager();
  
  // Throttled render function
  const throttledRender = (() => {
    let lastRender = 0;
    const minInterval = 1000 / FABRIC_MAP_CONFIG.FRAME_RATE_LIMIT;
    
    return (renderFn: () => void) => {
      const now = performance.now();
      if (now - lastRender >= minInterval) {
        lastRender = now;
        renderFn();
      }
    };
  })();
  
  // Initialize PIXI application with performance settings
  const initializePixiApp = () => {
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    
    try {
      app = new PIXI.Application({
        width: rect.width,
        height: rect.height,
        backgroundColor: 0x0a0a0a,
        antialias: !isPerformanceMode(),
        resolution: isPerformanceMode() ? 1 : window.devicePixelRatio,
        autoDensity: true,
        powerPreference: 'high-performance',
      });
      
      container.appendChild(app.view as HTMLCanvasElement);
      
      // Enable interactivity
      app.stage.interactive = true;
      app.stage.hitArea = new PIXI.Rectangle(0, 0, rect.width, rect.height);
      
      // Set up event listeners
      setupEventListeners();
      
      // Start render loop
      startRenderLoop();
      
    } catch (error) {
      console.error('Failed to initialize PIXI application:', error);
      setPerformanceWarning('Failed to initialize graphics renderer');
    }
  };
  
  const setupEventListeners = () => {
    if (!app) return;
    
    // Mouse events
    app.stage.on('pointerdown', onPointerDown);
    app.stage.on('pointermove', onPointerMove);
    app.stage.on('pointerup', onPointerUp);
    app.stage.on('wheel', onWheel);
    
    // Keyboard events
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
    
    // Window resize
    window.addEventListener('resize', onResize);
  };
  
  const startRenderLoop = () => {
    const renderLoop = () => {
      if (!app) return;
      
      performanceMonitor.startFrame();
      
      // Update camera
      updateCamera();
      
      // Update virtualization
      updateVirtualization();
      
      // Render nodes and edges
      renderScene();
      
      performanceMonitor.endFrame();
      
      animationFrameId = requestAnimationFrame(renderLoop);
    };
    
    renderLoop();
  };
  
  const updateCamera = () => {
    if (!app) return;
    
    // Clamp zoom
    camera.zoom = Math.max(FABRIC_MAP_CONFIG.ZOOM_LIMITS.min, 
                          Math.min(FABRIC_MAP_CONFIG.ZOOM_LIMITS.max, camera.zoom));
    
    // Update level of detail
    lodManager.updateDetailLevel(camera.zoom);
    
    // Apply camera transform
    app.stage.scale.set(camera.zoom);
    app.stage.position.set(camera.x, camera.y);
  };
  
  const updateVirtualization = () => {
    if (!app) return;
    
    const bounds = {
      minX: -camera.x / camera.zoom,
      maxX: (-camera.x + app.screen.width) / camera.zoom,
      minY: -camera.y / camera.zoom,
      maxY: (-camera.y + app.screen.height) / camera.zoom,
    };
    
    virtualizationManager.updateViewport(bounds);
  };
  
  const renderScene = () => {
    if (!app) return;
    
    throttledRender(() => {
      // Clear previous frame
      app.stage.removeChildren();
      
      // Render nodes
      renderNodes();
      
      // Render edges
      renderEdges();
      
      // Render UI overlays
      renderOverlays();
    });
  };
  
  const renderNodes = () => {
    if (!app) return;
    
    const currentNodes = nodes();
    const visibleNodes = virtualizationManager.getVisibleNodes();
    const detailLevel = lodManager.getDetailLevel();
    
    // Limit rendering to visible nodes
    const nodesToRender = currentNodes.filter(node => 
      visibleNodes.has(node.id) || visibleNodes.size === 0
    );
    
    nodesToRender.forEach(node => {
      const nodeGraphic = new PIXI.Graphics();
      
      // Determine node color based on status
      let color = 0x00ff00; // Green for healthy
      if (node.status === 'error') color = 0xff0000; // Red for error
      else if (node.status === 'warning') color = 0xffff00; // Yellow for warning
      
      // Calculate node size based on LOD
      const baseSize = 8;
      const nodeSize = lodManager.getNodeSize(baseSize);
      
      // Draw node
      nodeGraphic.beginFill(color, 0.8);
      nodeGraphic.drawCircle(node.x, node.y, nodeSize);
      nodeGraphic.endFill();
      
      // Add border for selected node
      if (selectedNode()?.id === node.id) {
        nodeGraphic.lineStyle(2, 0xffffff, 1);
        nodeGraphic.drawCircle(node.x, node.y, nodeSize + 2);
      }
      
      // Add label if detail level is high
      if (lodManager.shouldRenderLabels() && detailLevel === 'high') {
        const text = new PIXI.Text(node.name, {
          fontSize: 12,
          fill: 0xffffff,
          align: 'center',
        });
        text.x = node.x - text.width / 2;
        text.y = node.y + nodeSize + 5;
        app.stage.addChild(text);
      }
      
      // Make node interactive
      nodeGraphic.interactive = true;
      nodeGraphic.buttonMode = true;
      nodeGraphic.on('pointerdown', () => {
        setSelectedNode(node);
      });
      
      app.stage.addChild(nodeGraphic);
    });
  };
  
  const renderEdges = () => {
    if (!app) return;
    
    const currentFlows = flows();
    const visibleEdges = virtualizationManager.getVisibleEdges();
    
    // Limit edge rendering based on performance mode
    const maxEdges = isPerformanceMode() ? 100 : FABRIC_MAP_CONFIG.MAX_EDGES;
    const edgesToRender = currentFlows.slice(0, maxEdges);
    
    edgesToRender.forEach(flow => {
      const edgeGraphic = new PIXI.Graphics();
      
      // Draw edge
      edgeGraphic.lineStyle(1, 0x444444, 0.6);
      edgeGraphic.moveTo(flow.source.x, flow.source.y);
      edgeGraphic.lineTo(flow.target.x, flow.target.y);
      
      app.stage.addChild(edgeGraphic);
    });
  };
  
  const renderOverlays = () => {
    if (!app) return;
    
    // Performance overlay
    if (performanceWarning()) {
      const warningText = new PIXI.Text(performanceWarning() || '', {
        fontSize: 14,
        fill: 0xff0000,
        backgroundColor: 0x000000,
        padding: 10,
      });
      warningText.x = 10;
      warningText.y = 10;
      app.stage.addChild(warningText);
    }
    
    // Performance metrics overlay
    if (FABRIC_MAP_CONFIG.PERFORMANCE_MONITORING) {
      const metrics = performanceMonitor.getMetrics();
      const metricsText = new PIXI.Text(
        `FPS: ${Math.round(metrics.fps)} | Memory: ${Math.round(metrics.memoryUsage / 1024 / 1024)}MB`,
        {
          fontSize: 12,
          fill: 0x888888,
          backgroundColor: 0x000000,
          padding: 5,
        }
      );
      metricsText.x = 10;
      metricsText.y = app.screen.height - 30;
      app.stage.addChild(metricsText);
    }
  };
  
  // Event handlers
  const onPointerDown = (event: PIXI.InteractionEvent) => {
    dragging = true;
    lastPos = { x: event.data.global.x, y: event.data.global.y };
  };
  
  const onPointerMove = (event: PIXI.InteractionEvent) => {
    if (!dragging) return;
    
    const dx = event.data.global.x - lastPos.x;
    const dy = event.data.global.y - lastPos.y;
    
    camera.x += dx;
    camera.y += dy;
    
    lastPos = { x: event.data.global.x, y: event.data.global.y };
  };
  
  const onPointerUp = () => {
    dragging = false;
  };
  
  const onWheel = (event: WheelEvent) => {
    event.preventDefault();
    
    const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
    camera.zoom *= zoomFactor;
    
    // Zoom towards mouse position
    const mouseX = event.offsetX;
    const mouseY = event.offsetY;
    
    camera.x = mouseX - (mouseX - camera.x) * zoomFactor;
    camera.y = mouseY - (mouseY - camera.y) * zoomFactor;
  };
  
  const onKeyDown = (event: KeyboardEvent) => {
    // Performance mode toggle
    if (event.key === 'p' && event.ctrlKey) {
      setIsPerformanceMode(!isPerformanceMode());
      event.preventDefault();
    }
    
    // Reset camera
    if (event.key === 'r' && event.ctrlKey) {
      camera = { x: 0, y: 0, zoom: 1 };
      event.preventDefault();
    }
  };
  
  const onKeyUp = (event: KeyboardEvent) => {
    // Handle key up events
  };
  
  const onResize = () => {
    if (!app || !container) return;
    
    const rect = container.getBoundingClientRect();
    app.renderer.resize(rect.width, rect.height);
  };
  
  // Component lifecycle
  onMount(() => {
    initializePixiApp();
    
    // Update virtualization with initial node data
    createEffect(() => {
      const currentNodes = nodes();
      virtualizationManager.setNodes(currentNodes.map(node => ({
        id: node.id,
        x: node.x,
        y: node.y,
        type: node.type,
        status: node.status,
        connections: node.connections || [],
        metadata: node.metadata || {},
      })));
    });
  });
  
  onCleanup(() => {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
    
    if (app) {
      app.destroy(true);
    }
    
    document.removeEventListener('keydown', onKeyDown);
    document.removeEventListener('keyup', onKeyUp);
    window.removeEventListener('resize', onResize);
  });
  
  return (
    <div class="relative h-full w-full overflow-hidden">
      <div ref={container} class="absolute inset-0" />
      <div ref={d3Container} class="absolute inset-0 pointer-events-none" />
      
      {/* Performance controls */}
      <div class="absolute top-4 right-4 bg-black/50 rounded-lg p-2 text-white text-sm">
        <div class="flex items-center gap-2">
          <input
            type="checkbox"
            id="performance-mode"
            checked={isPerformanceMode()}
            onChange={(e) => setIsPerformanceMode(e.target.checked)}
          />
          <label for="performance-mode">Performance Mode</label>
        </div>
        <div class="mt-1 text-xs text-gray-300">
          Nodes: {nodes().length} | Visible: {virtualizationManager.getVisibleNodes().size}
        </div>
      </div>
      
      {/* Performance warning */}
      {performanceWarning() && (
        <div class="absolute top-4 left-4 bg-red-900/80 border border-red-500 rounded-lg p-3 text-white text-sm max-w-md">
          <div class="flex items-center gap-2">
            <span class="text-red-400">⚠️</span>
            <span>{performanceWarning()}</span>
          </div>
          <button
            onClick={() => setPerformanceWarning(null)}
            class="mt-2 px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
