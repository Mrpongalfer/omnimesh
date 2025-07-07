# Performance Optimization Guide

## 🎯 Performance Targets

### Core Web Vitals

- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **First Input Delay (FID)**: < 100ms
- **Cumulative Layout Shift (CLS)**: < 0.1

### Bundle Targets

- **Initial Bundle**: < 200KB gzipped
- **Total JavaScript**: < 500KB gzipped
- **CSS**: < 50KB gzipped

## 🚀 Optimization Strategies

### 1. Bundle Optimization

#### Code Splitting

```javascript
// Route-based splitting
const LazyComponent = lazy(() => import('./LazyComponent'));

// Manual chunk splitting in vite.config.ts
manualChunks: {
  vendor: ['solid-js'],
  visualization: ['pixi.js', 'd3'],
  utils: ['protobufjs'],
}
```

#### Tree Shaking

```javascript
// Use ES6 imports for better tree shaking
import { specificFunction } from 'library';

// Avoid importing entire libraries
// ❌ Bad
import * as d3 from 'd3';

// ✅ Good
import { select, scaleLinear } from 'd3';
```

#### Dynamic Imports

```javascript
// Load modules on demand
const loadVisualization = async () => {
  const { createChart } = await import('./visualization');
  return createChart;
};
```

### 2. Asset Optimization

#### Image Optimization

```javascript
// Use modern image formats
<img
  src="image.webp"
  alt="Description"
  loading="lazy"
  decoding="async"
/>

// Responsive images
<img
  src="small.webp"
  srcSet="
    small.webp 480w,
    medium.webp 800w,
    large.webp 1200w
  "
  sizes="(max-width: 480px) 100vw, (max-width: 800px) 50vw, 25vw"
  alt="Description"
/>
```

#### Font Optimization

```css
/* Preload critical fonts */
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap;
}
```

### 3. JavaScript Optimization

#### Solid.js Optimizations

```javascript
// Use createMemo for expensive computations
const expensiveValue = createMemo(() => {
  return heavyComputation(data());
});

// Batch updates
batch(() => {
  setFirstSignal(newValue1);
  setSecondSignal(newValue2);
  setThirdSignal(newValue3);
});

// Use untrack for non-reactive reads
const value = untrack(() => someSignal());
```

#### Event Optimization

```javascript
// Use event delegation for better performance
<div
  onClick={(e) => {
    if (e.target.matches('.button')) {
      handleClick(e);
    }
  }}
>
  {/* Multiple buttons */}
</div>;

// Throttle expensive operations
const throttledResize = throttle(() => {
  handleResize();
}, 16); // 60fps
```

### 4. Rendering Optimization

#### Virtual Scrolling

```javascript
// For large lists, use virtual scrolling
import { VirtualList } from '@tanstack/solid-virtual';

<VirtualList
  items={largeDataSet}
  itemHeight={50}
  renderItem={({ item, index }) => <Item item={item} />}
/>;
```

#### Efficient Updates

```javascript
// Use keys for efficient list updates
<For each={items()}>{(item) => <Item key={item.id} item={item} />}</For>;

// Avoid unnecessary re-renders
const MemoizedComponent = memo((props) => {
  return <ExpensiveComponent {...props} />;
});
```

### 5. Network Optimization

#### Resource Hints

```html
<!-- Preload critical resources -->
<link
  rel="preload"
  href="/fonts/critical.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>
<link rel="preload" href="/api/critical-data" as="fetch" crossorigin />

<!-- Prefetch next page resources -->
<link rel="prefetch" href="/next-page.js" />

<!-- Preconnect to external domains -->
<link rel="preconnect" href="https://api.example.com" />
```

#### Caching Strategy

```javascript
// Service Worker caching
const CACHE_NAME = 'omnitide-v1';
const urlsToCache = ['/', '/static/css/main.css', '/static/js/main.js'];

// Cache-first strategy for assets
self.addEventListener('fetch', (event) => {
  if (
    event.request.destination === 'script' ||
    event.request.destination === 'style'
  ) {
    event.respondWith(
      caches
        .match(event.request)
        .then((response) => response || fetch(event.request)),
    );
  }
});
```

## 📊 Performance Monitoring

### Real User Monitoring

```javascript
// Core Web Vitals tracking
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

const sendToAnalytics = (metric) => {
  // Send to your analytics service
  console.log(metric);
};

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

### Performance API

```javascript
// Measure custom metrics
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(`${entry.name}: ${entry.duration}ms`);
  }
});

observer.observe({ entryTypes: ['measure', 'navigation'] });

// Custom timing
performance.mark('component-start');
// ... component rendering
performance.mark('component-end');
performance.measure('component-render', 'component-start', 'component-end');
```

### Bundle Analysis

```bash
# Analyze bundle size
npm run analyze

# Generate detailed report
npx webpack-bundle-analyzer dist/static/js/*.js
```

## 🛠️ Development Tools

### Performance Budget

```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Warn if chunks are too large
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
  },
});
```

### Lighthouse CI

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [push, pull_request]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun
```

### Performance Testing

```javascript
// performance.test.js
import { test, expect } from '@playwright/test';

test('page loads within performance budget', async ({ page }) => {
  const start = Date.now();
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - start;

  expect(loadTime).toBeLessThan(3000); // 3 second budget
});
```

## 🎨 Visual Performance

### Layout Optimization

```css
/* Use transform for animations (GPU accelerated) */
.animated-element {
  transform: translateX(0);
  transition: transform 0.3s ease;
}

.animated-element.moved {
  transform: translateX(100px);
}

/* Avoid layout thrashing */
.avoid-layout-shift {
  width: 200px; /* Fixed dimensions */
  height: 100px;
  aspect-ratio: 2/1; /* Modern approach */
}
```

### Rendering Optimization

```javascript
// Use will-change sparingly
const OptimizedComponent = () => {
  const [isAnimating, setIsAnimating] = createSignal(false);

  return (
    <div
      style={{
        'will-change': isAnimating() ? 'transform' : 'auto',
      }}
      onAnimationStart={() => setIsAnimating(true)}
      onAnimationEnd={() => setIsAnimating(false)}
    >
      Content
    </div>
  );
};
```

## 📱 Mobile Performance

### Touch Optimization

```css
/* Improve touch responsiveness */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  touch-action: manipulation;
}

/* Reduce input delay */
.input-element {
  touch-action: manipulation;
}
```

### Viewport Optimization

```html
<!-- Optimize viewport for mobile -->
<meta
  name="viewport"
  content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes"
/>
```

## 🔧 Advanced Techniques

### Web Workers

```javascript
// Offload heavy computations
const worker = new Worker('/workers/data-processor.js');

worker.postMessage({ data: heavyDataSet });
worker.onmessage = (e) => {
  setProcessedData(e.data);
};
```

### WebAssembly

```javascript
// Use WASM for performance-critical calculations
const wasmModule = await WebAssembly.instantiateStreaming(
  fetch('/wasm/calculations.wasm'),
);

const result = wasmModule.instance.exports.heavyCalculation(data);
```

### Streaming

```javascript
// Stream data for better perceived performance
const stream = new ReadableStream({
  start(controller) {
    fetchDataInChunks().then((chunks) => {
      chunks.forEach((chunk) => controller.enqueue(chunk));
      controller.close();
    });
  },
});
```

## 📈 Continuous Optimization

### Monitoring Setup

1. **Real User Monitoring**: Track actual user performance
2. **Synthetic Testing**: Regular automated performance tests
3. **Performance Budgets**: Automated alerts for regressions
4. **Regular Audits**: Monthly performance reviews

### Optimization Workflow

1. **Measure**: Establish baseline metrics
2. **Analyze**: Identify bottlenecks
3. **Optimize**: Apply targeted improvements
4. **Validate**: Confirm improvements
5. **Monitor**: Track ongoing performance
