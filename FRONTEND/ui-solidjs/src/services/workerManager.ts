// Worker Manager Service
// Manages Web Workers for background processing tasks

export interface WorkerTask {
  id: string;
  type: string;
  data?: any;
  options?: any;
  priority?: number;
  timeout?: number;
}

export interface WorkerResponse {
  type: string;
  id: string;
  data?: any;
  error?: string;
  processingTime?: number;
}

export interface WorkerStats {
  tasksProcessed: number;
  totalProcessingTime: number;
  averageProcessingTime: number;
  queueLength: number;
  workerStatus: 'idle' | 'busy' | 'error';
}

// Task priority levels
export enum TaskPriority {
  LOW = 1,
  NORMAL = 2,
  HIGH = 3,
  CRITICAL = 4
}

// Base Worker Manager class
abstract class BaseWorkerManager {
  protected worker: Worker | null = null;
  protected taskQueue: Map<string, WorkerTask> = new Map();
  protected pendingTasks: Map<string, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
    timeout?: NodeJS.Timeout;
  }> = new Map();
  protected workerStats: WorkerStats = {
    tasksProcessed: 0,
    totalProcessingTime: 0,
    averageProcessingTime: 0,
    queueLength: 0,
    workerStatus: 'idle'
  };

  constructor(protected workerPath: string, protected maxQueueSize = 100) {}

  // Initialize worker
  async initialize(): Promise<void> {
    if (this.worker) {
      this.terminate();
    }

    try {
      this.worker = new Worker(this.workerPath);
      this.setupWorkerHandlers();
      this.workerStats.workerStatus = 'idle';
    } catch (error) {
      this.workerStats.workerStatus = 'error';
      throw new Error(`Failed to initialize worker: ${error.message}`);
    }
  }

  // Setup message handlers
  private setupWorkerHandlers(): void {
    if (!this.worker) return;

    this.worker.addEventListener('message', (event: MessageEvent<WorkerResponse>) => {
      this.handleWorkerMessage(event.data);
    });

    this.worker.addEventListener('error', (event: ErrorEvent) => {
      this.handleWorkerError(event);
    });

    this.worker.addEventListener('messageerror', (event: MessageEvent) => {
      console.error('Worker message error:', event);
      this.workerStats.workerStatus = 'error';
    });
  }

  // Handle worker messages
  private handleWorkerMessage(response: WorkerResponse): void {
    const { id, type, data, error, processingTime } = response;

    if (type === 'error') {
      this.handleTaskError(id, error || 'Unknown worker error');
      return;
    }

    if (type === 'stats') {
      // Update worker stats without affecting task processing
      return;
    }

    const pendingTask = this.pendingTasks.get(id);
    if (!pendingTask) {
      console.warn(`Received response for unknown task: ${id}`);
      return;
    }

    // Update statistics
    if (processingTime) {
      this.workerStats.tasksProcessed++;
      this.workerStats.totalProcessingTime += processingTime;
      this.workerStats.averageProcessingTime = 
        this.workerStats.totalProcessingTime / this.workerStats.tasksProcessed;
    }

    // Clear timeout
    if (pendingTask.timeout) {
      clearTimeout(pendingTask.timeout);
    }

    // Resolve task
    this.pendingTasks.delete(id);
    this.taskQueue.delete(id);
    this.workerStats.queueLength = this.taskQueue.size;
    
    if (this.pendingTasks.size === 0) {
      this.workerStats.workerStatus = 'idle';
    }

    pendingTask.resolve(data);
  }

  // Handle worker errors
  private handleWorkerError(event: ErrorEvent): void {
    console.error('Worker error:', event);
    this.workerStats.workerStatus = 'error';
    
    // Reject all pending tasks
    this.pendingTasks.forEach(({ reject, timeout }, taskId) => {
      if (timeout) clearTimeout(timeout);
      reject(new Error(`Worker error: ${event.message}`));
    });
    
    this.pendingTasks.clear();
    this.taskQueue.clear();
    this.workerStats.queueLength = 0;
  }

  // Handle task timeout or error
  private handleTaskError(taskId: string, error: string): void {
    const pendingTask = this.pendingTasks.get(taskId);
    if (pendingTask) {
      if (pendingTask.timeout) {
        clearTimeout(pendingTask.timeout);
      }
      this.pendingTasks.delete(taskId);
      this.taskQueue.delete(taskId);
      this.workerStats.queueLength = this.taskQueue.size;
      pendingTask.reject(new Error(error));
    }
  }

  // Execute task
  async executeTask(task: WorkerTask): Promise<any> {
    if (!this.worker) {
      throw new Error('Worker not initialized');
    }

    if (this.taskQueue.size >= this.maxQueueSize) {
      throw new Error('Task queue is full');
    }

    // Generate task ID if not provided
    if (!task.id) {
      task.id = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // Add to queue
    this.taskQueue.set(task.id, task);
    this.workerStats.queueLength = this.taskQueue.size;
    this.workerStats.workerStatus = 'busy';

    return new Promise((resolve, reject) => {
      // Setup timeout
      let timeoutId: NodeJS.Timeout | undefined;
      if (task.timeout && task.timeout > 0) {
        timeoutId = setTimeout(() => {
          this.handleTaskError(task.id, `Task timeout: ${task.timeout}ms`);
        }, task.timeout);
      }

      // Store promise handlers
      this.pendingTasks.set(task.id, { resolve, reject, timeout: timeoutId });

      // Send task to worker
      this.worker!.postMessage(task);
    });
  }

  // Get current statistics
  getStats(): WorkerStats {
    return { ...this.workerStats };
  }

  // Terminate worker
  terminate(): void {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }

    // Reject all pending tasks
    this.pendingTasks.forEach(({ reject, timeout }) => {
      if (timeout) clearTimeout(timeout);
      reject(new Error('Worker terminated'));
    });

    this.pendingTasks.clear();
    this.taskQueue.clear();
    this.workerStats = {
      tasksProcessed: 0,
      totalProcessingTime: 0,
      averageProcessingTime: 0,
      queueLength: 0,
      workerStatus: 'idle'
    };
  }
}

// AI Inference Worker Manager
export class AIInferenceManager extends BaseWorkerManager {
  private loadedModels = new Set<string>();

  constructor() {
    super('/workers/ai-inference.js');
  }

  async initializeAI(config: { backend?: 'webgl' | 'cpu'; debug?: boolean } = {}): Promise<void> {
    await this.initialize();
    
    await this.executeTask({
      id: 'ai-init',
      type: 'initialize',
      data: { config: { backend: 'webgl', debug: false, ...config } },
      timeout: 10000
    });
  }

  async loadModel(name: string, url: string): Promise<void> {
    if (this.loadedModels.has(name)) {
      return; // Model already loaded
    }

    await this.executeTask({
      id: `load-model-${name}`,
      type: 'load-model',
      data: { name, url },
      timeout: 30000,
      priority: TaskPriority.HIGH
    });

    this.loadedModels.add(name);
  }

  async predict(
    modelName: string, 
    input: number[] | number[][], 
    options: { batchSize?: number; verbose?: boolean } = {}
  ): Promise<number[]> {
    if (!this.loadedModels.has(modelName)) {
      throw new Error(`Model ${modelName} not loaded`);
    }

    const result = await this.executeTask({
      id: `predict-${Date.now()}`,
      type: 'predict',
      data: { modelName, input, options },
      timeout: 5000,
      priority: TaskPriority.NORMAL
    });

    return result.output;
  }

  getLoadedModels(): string[] {
    return Array.from(this.loadedModels);
  }
}

// Data Processing Worker Manager
export class DataProcessingManager extends BaseWorkerManager {
  constructor() {
    super('/workers/data-processing.js');
  }

  async processNetworkData(nodes: any[], flows: any[]): Promise<{ metrics: any; anomalies: any[] }> {
    return await this.executeTask({
      id: `network-analysis-${Date.now()}`,
      type: 'process-network-data',
      data: { nodes, flows },
      timeout: 10000,
      priority: TaskPriority.NORMAL
    });
  }

  async optimizeLayout(nodes: any[], flows: any[], options: any = {}): Promise<{ nodes: any[] }> {
    return await this.executeTask({
      id: `layout-optimization-${Date.now()}`,
      type: 'optimize-layout',
      data: { nodes, flows },
      options,
      timeout: 15000,
      priority: TaskPriority.LOW
    });
  }

  async analyzeAnomalies(nodes: any[], historicalData: any[] = []): Promise<{ anomalies: any[] }> {
    return await this.executeTask({
      id: `anomaly-analysis-${Date.now()}`,
      type: 'analyze-anomalies',
      data: { nodes, historicalData },
      timeout: 8000,
      priority: TaskPriority.HIGH
    });
  }

  async computeMetrics(nodes: any[], flows: any[]): Promise<{ metrics: any; clustering: any }> {
    return await this.executeTask({
      id: `metrics-computation-${Date.now()}`,
      type: 'compute-metrics',
      data: { nodes, flows },
      timeout: 5000,
      priority: TaskPriority.NORMAL
    });
  }
}

// Global Worker Manager instance
export class WorkerManagerService {
  private static instance: WorkerManagerService;
  
  public readonly ai: AIInferenceManager;
  public readonly dataProcessing: DataProcessingManager;
  
  private initialized = false;

  private constructor() {
    this.ai = new AIInferenceManager();
    this.dataProcessing = new DataProcessingManager();
  }

  static getInstance(): WorkerManagerService {
    if (!WorkerManagerService.instance) {
      WorkerManagerService.instance = new WorkerManagerService();
    }
    return WorkerManagerService.instance;
  }

  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      await Promise.all([
        this.ai.initialize(),
        this.dataProcessing.initialize()
      ]);
      
      this.initialized = true;
      console.log('Worker Manager Service initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Worker Manager Service:', error);
      throw error;
    }
  }

  // Initialize AI with specific configuration
  async initializeAI(config?: { backend?: 'webgl' | 'cpu'; debug?: boolean }): Promise<void> {
    await this.ai.initializeAI(config);
  }

  // Get combined statistics from all workers
  getAllStats(): { ai: WorkerStats; dataProcessing: WorkerStats } {
    return {
      ai: this.ai.getStats(),
      dataProcessing: this.dataProcessing.getStats()
    };
  }

  // Cleanup all workers
  terminate(): void {
    this.ai.terminate();
    this.dataProcessing.terminate();
    this.initialized = false;
  }

  // Health check for all workers
  async healthCheck(): Promise<{ ai: boolean; dataProcessing: boolean; overall: boolean }> {
    const aiStats = this.ai.getStats();
    const dataStats = this.dataProcessing.getStats();
    
    const aiHealthy = aiStats.workerStatus !== 'error';
    const dataHealthy = dataStats.workerStatus !== 'error';
    
    return {
      ai: aiHealthy,
      dataProcessing: dataHealthy,
      overall: aiHealthy && dataHealthy
    };
  }
}

// Export singleton instance
export const workerManager = WorkerManagerService.getInstance();
