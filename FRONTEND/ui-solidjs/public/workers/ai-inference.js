// AI Inference Worker for TensorFlow.js
// Provides background ML inference without blocking the main thread

import * as tf from '@tensorflow/tfjs';

// Worker message types
interface LoadModelMessage {
  type: 'load-model';
  name: string;
  url: string;
}

interface PredictMessage {
  type: 'predict';
  modelName: string;
  input: number[] | number[][];
  options?: {
    batchSize?: number;
    verbose?: boolean;
  };
}

interface InitializeMessage {
  type: 'initialize';
  config: {
    backend: 'webgl' | 'cpu';
    debug: boolean;
  };
}

type WorkerMessage = LoadModelMessage | PredictMessage | InitializeMessage;

// Model registry
const models = new Map<string, tf.LayersModel>();
const modelMetadata = new Map<string, { 
  inputShape: number[], 
  outputShape: number[],
  version: string 
}>();

// Performance metrics
let inferenceCount = 0;
let totalInferenceTime = 0;

// Initialize TensorFlow.js
async function initializeTensorFlow(backend: 'webgl' | 'cpu' = 'webgl', debug = false): Promise<void> {
  try {
    // Set backend
    await tf.setBackend(backend);
    
    if (debug) {
      tf.enableProdMode = false;
      console.log('TensorFlow.js initialized in debug mode');
      console.log('Backend:', tf.getBackend());
      console.log('Memory info:', tf.memory());
    }
    
    // Warm up with a simple operation
    const warmupTensor = tf.zeros([1, 1]);
    const result = tf.add(warmupTensor, warmupTensor);
    result.dispose();
    warmupTensor.dispose();
    
    self.postMessage({
      type: 'initialized',
      backend: tf.getBackend(),
      version: tf.version.tfjs
    });
  } catch (error) {
    self.postMessage({
      type: 'error',
      message: `Failed to initialize TensorFlow.js: ${error.message}`
    });
  }
}

// Load and cache ML model
async function loadModel(name: string, url: string): Promise<void> {
  try {
    console.log(`Loading model ${name} from ${url}`);
    
    const model = await tf.loadLayersModel(url);
    models.set(name, model);
    
    // Extract model metadata
    const inputShape = model.inputs[0].shape.slice(1); // Remove batch dimension
    const outputShape = model.outputs[0].shape.slice(1);
    
    modelMetadata.set(name, {
      inputShape,
      outputShape,
      version: '1.0.0'
    });
    
    console.log(`Model ${name} loaded successfully`);
    console.log('Input shape:', inputShape);
    console.log('Output shape:', outputShape);
    console.log('Total parameters:', model.countParams());
    
    self.postMessage({
      type: 'model-loaded',
      name,
      metadata: {
        inputShape,
        outputShape,
        parameters: model.countParams(),
        memoryUsage: tf.memory().numBytes
      }
    });
  } catch (error) {
    self.postMessage({
      type: 'error',
      message: `Failed to load model ${name}: ${error.message}`
    });
  }
}

// Perform inference
async function predict(
  modelName: string, 
  input: number[] | number[][], 
  options: { batchSize?: number; verbose?: boolean } = {}
): Promise<void> {
  const startTime = performance.now();
  
  try {
    const model = models.get(modelName);
    if (!model) {
      throw new Error(`Model ${modelName} not loaded`);
    }
    
    const metadata = modelMetadata.get(modelName);
    if (!metadata) {
      throw new Error(`No metadata found for model ${modelName}`);
    }
    
    // Prepare input tensor
    let inputTensor: tf.Tensor;
    
    if (Array.isArray(input[0])) {
      // Batch input
      inputTensor = tf.tensor2d(input as number[][]);
    } else {
      // Single input - add batch dimension
      inputTensor = tf.tensor2d([input as number[]]);
    }
    
    // Validate input shape
    const expectedShape = [inputTensor.shape[0], ...metadata.inputShape];
    if (!inputTensor.shape.every((dim, i) => dim === expectedShape[i] || expectedShape[i] === -1)) {
      inputTensor.dispose();
      throw new Error(`Input shape ${inputTensor.shape} doesn't match expected ${expectedShape}`);
    }
    
    // Run inference
    const prediction = model.predict(inputTensor) as tf.Tensor;
    const output = await prediction.data();
    
    // Cleanup tensors
    inputTensor.dispose();
    prediction.dispose();
    
    const inferenceTime = performance.now() - startTime;
    inferenceCount++;
    totalInferenceTime += inferenceTime;
    
    if (options.verbose) {
      console.log(`Inference completed in ${inferenceTime.toFixed(2)}ms`);
      console.log('Average inference time:', (totalInferenceTime / inferenceCount).toFixed(2), 'ms');
      console.log('Memory usage:', tf.memory());
    }
    
    self.postMessage({
      type: 'prediction',
      modelName,
      output: Array.from(output),
      metadata: {
        inferenceTime,
        inputShape: inputTensor.shape,
        outputShape: prediction.shape,
        memoryUsage: tf.memory().numBytes
      }
    });
    
  } catch (error) {
    const inferenceTime = performance.now() - startTime;
    
    self.postMessage({
      type: 'error',
      message: `Prediction failed for model ${modelName}: ${error.message}`,
      metadata: {
        inferenceTime,
        memoryUsage: tf.memory().numBytes
      }
    });
  }
}

// Performance monitoring
function getPerformanceStats() {
  return {
    inferenceCount,
    totalInferenceTime,
    averageInferenceTime: inferenceCount > 0 ? totalInferenceTime / inferenceCount : 0,
    loadedModels: Array.from(models.keys()),
    memoryUsage: tf.memory(),
    backend: tf.getBackend()
  };
}

// Cleanup resources
function cleanup() {
  // Dispose all models
  for (const model of models.values()) {
    model.dispose();
  }
  models.clear();
  modelMetadata.clear();
  
  // Reset performance metrics
  inferenceCount = 0;
  totalInferenceTime = 0;
  
  self.postMessage({
    type: 'cleanup-complete',
    memoryUsage: tf.memory()
  });
}

// Message handler
self.addEventListener('message', async (event: MessageEvent<WorkerMessage>) => {
  const { data } = event;
  
  try {
    switch (data.type) {
      case 'initialize':
        await initializeTensorFlow(data.config.backend, data.config.debug);
        break;
        
      case 'load-model':
        await loadModel(data.name, data.url);
        break;
        
      case 'predict':
        await predict(data.modelName, data.input, data.options);
        break;
        
      case 'get-stats':
        self.postMessage({
          type: 'stats',
          data: getPerformanceStats()
        });
        break;
        
      case 'cleanup':
        cleanup();
        break;
        
      default:
        self.postMessage({
          type: 'error',
          message: `Unknown message type: ${(data as any).type}`
        });
    }
  } catch (error) {
    self.postMessage({
      type: 'error',
      message: `Worker error: ${error.message}`
    });
  }
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

// Initialize on startup
initializeTensorFlow('webgl', false);
