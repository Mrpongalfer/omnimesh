#!/usr/bin/env node

/**
 * Memory profiling script for Omnitide Control Panel
 * Monitors memory usage during development and identifies potential leaks
 */

import { performance, PerformanceObserver } from 'perf_hooks';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

class MemoryProfiler {
  constructor() {
    this.measurements = [];
    this.startTime = Date.now();
    this.isRunning = false;
    this.reportPath = path.join(process.cwd(), 'reports');
  }

  start() {
    console.log('🔍 Starting memory profiler...');
    this.isRunning = true;
    
    // Ensure reports directory exists
    if (!fs.existsSync(this.reportPath)) {
      fs.mkdirSync(this.reportPath, { recursive: true });
    }

    // Start memory monitoring
    this.monitorMemory();
    
    // Monitor garbage collection
    this.observeGC();
    
    // Start development server for profiling
    this.startDevServer();
    
    // Generate report every 30 seconds
    setInterval(() => {
      this.generateReport();
    }, 30000);

    // Handle cleanup
    process.on('SIGINT', () => {
      this.stop();
    });
  }

  monitorMemory() {
    const monitor = () => {
      if (!this.isRunning) return;

      const memUsage = process.memoryUsage();
      const timestamp = Date.now() - this.startTime;
      
      this.measurements.push({
        timestamp,
        ...memUsage,
        heapUsedMB: Math.round(memUsage.heapUsed / 1024 / 1024 * 100) / 100,
        heapTotalMB: Math.round(memUsage.heapTotal / 1024 / 1024 * 100) / 100,
        externalMB: Math.round(memUsage.external / 1024 / 1024 * 100) / 100,
        rss: Math.round(memUsage.rss / 1024 / 1024 * 100) / 100
      });

      // Log current memory usage
      console.log(`📊 Memory: ${memUsage.heapUsed / 1024 / 1024 | 0}MB heap, ${memUsage.rss / 1024 / 1024 | 0}MB RSS`);

      // Check for potential memory leaks
      if (this.measurements.length > 10) {
        this.checkForLeaks();
      }

      setTimeout(monitor, 5000); // Check every 5 seconds
    };

    monitor();
  }

  observeGC() {
    const obs = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.name === 'gc') {
          console.log(`🗑️  GC: ${entry.duration.toFixed(2)}ms (${entry.detail?.kind || 'unknown'})`);
        }
      });
    });
    
    obs.observe({ entryTypes: ['gc'] });
  }

  checkForLeaks() {
    const recent = this.measurements.slice(-5);
    const avgGrowth = recent.reduce((sum, curr, idx) => {
      if (idx === 0) return 0;
      return sum + (curr.heapUsedMB - recent[idx - 1].heapUsedMB);
    }, 0) / (recent.length - 1);

    if (avgGrowth > 5) { // More than 5MB average growth
      console.warn(`⚠️  Potential memory leak detected: ${avgGrowth.toFixed(2)}MB average growth`);
    }
  }

  startDevServer() {
    console.log('🚀 Starting development server for profiling...');
    
    const devServer = spawn('npm', ['run', 'dev'], {
      stdio: 'pipe',
      env: {
        ...process.env,
        VITE_MEMORY_PROFILING: 'true'
      }
    });

    devServer.stdout.on('data', (data) => {
      const output = data.toString();
      if (output.includes('Local:')) {
        console.log('✅ Development server started');
        console.log('📝 Open Chrome DevTools > Memory tab for detailed profiling');
        console.log('🔗 Navigate to http://localhost:5173');
      }
    });

    devServer.stderr.on('data', (data) => {
      console.error(`Dev server error: ${data}`);
    });
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      duration: Date.now() - this.startTime,
      measurements: this.measurements,
      summary: this.generateSummary(),
      recommendations: this.generateRecommendations()
    };

    const reportFile = path.join(this.reportPath, `memory-profile-${Date.now()}.json`);
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    
    console.log(`📋 Memory report saved: ${reportFile}`);
    
    // Generate HTML visualization
    this.generateHTMLReport(report);
  }

  generateSummary() {
    if (this.measurements.length === 0) return null;

    const latest = this.measurements[this.measurements.length - 1];
    const first = this.measurements[0];
    
    return {
      currentHeapMB: latest.heapUsedMB,
      currentRSSMB: latest.rss,
      heapGrowthMB: latest.heapUsedMB - first.heapUsedMB,
      peakHeapMB: Math.max(...this.measurements.map(m => m.heapUsedMB)),
      averageHeapMB: this.measurements.reduce((sum, m) => sum + m.heapUsedMB, 0) / this.measurements.length,
      measurementCount: this.measurements.length
    };
  }

  generateRecommendations() {
    const recommendations = [];
    const summary = this.generateSummary();
    
    if (!summary) return recommendations;

    if (summary.heapGrowthMB > 50) {
      recommendations.push('High memory growth detected. Check for memory leaks in event listeners, timers, or large data structures.');
    }
    
    if (summary.peakHeapMB > 200) {
      recommendations.push('High peak memory usage. Consider implementing data virtualization or lazy loading.');
    }
    
    if (summary.currentHeapMB > 100) {
      recommendations.push('Current memory usage is high. Review component lifecycle and state management.');
    }

    return recommendations;
  }

  generateHTMLReport(report) {
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Memory Profile Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .metric { background: #333; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .chart-container { width: 100%; height: 400px; margin: 20px 0; }
        .recommendations { background: #444; padding: 15px; border-left: 4px solid #ff6b6b; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Memory Profile Report</h1>
        <p>Generated: ${report.timestamp}</p>
        
        <div class="summary">
            <div class="metric">
                <h3>Current Heap</h3>
                <p>${report.summary?.currentHeapMB?.toFixed(2) || 0} MB</p>
            </div>
            <div class="metric">
                <h3>Peak Heap</h3>
                <p>${report.summary?.peakHeapMB?.toFixed(2) || 0} MB</p>
            </div>
            <div class="metric">
                <h3>Heap Growth</h3>
                <p>${report.summary?.heapGrowthMB?.toFixed(2) || 0} MB</p>
            </div>
            <div class="metric">
                <h3>Current RSS</h3>
                <p>${report.summary?.currentRSSMB?.toFixed(2) || 0} MB</p>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="memoryChart"></canvas>
        </div>

        ${report.recommendations.length > 0 ? `
        <div class="recommendations">
            <h3>📝 Recommendations</h3>
            <ul>
                ${report.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
        ` : ''}
    </div>

    <script>
        const ctx = document.getElementById('memoryChart').getContext('2d');
        const data = ${JSON.stringify(report.measurements)};
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => new Date(d.timestamp).toLocaleTimeString()),
                datasets: [{
                    label: 'Heap Used (MB)',
                    data: data.map(d => d.heapUsedMB),
                    borderColor: '#4bc0c0',
                    tension: 0.1
                }, {
                    label: 'RSS (MB)',
                    data: data.map(d => d.rss),
                    borderColor: '#ff6b6b',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Memory Usage Over Time',
                        color: '#fff'
                    },
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#fff' },
                        grid: { color: '#555' }
                    },
                    y: {
                        ticks: { color: '#fff' },
                        grid: { color: '#555' }
                    }
                }
            }
        });
    </script>
</body>
</html>`;

    const htmlFile = path.join(this.reportPath, `memory-profile-${Date.now()}.html`);
    fs.writeFileSync(htmlFile, html);
    console.log(`📊 HTML report saved: ${htmlFile}`);
  }

  stop() {
    console.log('\n🔴 Stopping memory profiler...');
    this.isRunning = false;
    this.generateReport();
    console.log('✅ Final report generated');
    process.exit(0);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const profiler = new MemoryProfiler();
  profiler.start();
}

export default MemoryProfiler;
