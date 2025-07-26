// Package monitor provides comprehensive system resource monitoring capabilities
package monitor

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"time"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
	"github.com/shirou/gopsutil/v3/process"
)

// SystemMetrics contains comprehensive system resource information
type SystemMetrics struct {
	// CPU metrics
	CPUPercent float64 `json:"cpu_percent"`
	CPUCores   int     `json:"cpu_cores"`
	CPUFreq    float64 `json:"cpu_freq_mhz"`

	// Memory metrics
	MemoryTotal     uint64  `json:"memory_total_bytes"`
	MemoryUsed      uint64  `json:"memory_used_bytes"`
	MemoryPercent   float64 `json:"memory_percent"`
	MemoryAvailable uint64  `json:"memory_available_bytes"`

	// Disk metrics
	DiskTotal   uint64  `json:"disk_total_bytes"`
	DiskUsed    uint64  `json:"disk_used_bytes"`
	DiskPercent float64 `json:"disk_percent"`
	DiskFree    uint64  `json:"disk_free_bytes"`

	// Network metrics
	NetworkBytesRecv   uint64 `json:"network_bytes_recv"`
	NetworkBytesSent   uint64 `json:"network_bytes_sent"`
	NetworkPacketsRecv uint64 `json:"network_packets_recv"`
	NetworkPacketsSent uint64 `json:"network_packets_sent"`

	// System info
	Hostname     string    `json:"hostname"`
	Platform     string    `json:"platform"`
	Uptime       uint64    `json:"uptime_seconds"`
	ProcessCount int       `json:"process_count"`
	Timestamp    time.Time `json:"timestamp"`

	// Load averages (Linux/Unix)
	LoadAvg1  float64 `json:"load_avg_1min"`
	LoadAvg5  float64 `json:"load_avg_5min"`
	LoadAvg15 float64 `json:"load_avg_15min"`
}

// Monitor provides system monitoring capabilities
type Monitor struct {
	mu              sync.RWMutex
	lastMetrics     *SystemMetrics
	lastNetworkStat *net.IOCountersStat
	updateInterval  time.Duration
	stopCh          chan struct{}
}

// NewMonitor creates a new system monitor
func NewMonitor(updateInterval time.Duration) *Monitor {
	return &Monitor{
		updateInterval: updateInterval,
		stopCh:         make(chan struct{}),
	}
}

// Start begins continuous monitoring
func (m *Monitor) Start(ctx context.Context) error {
	ticker := time.NewTicker(m.updateInterval)
	defer ticker.Stop()

	// Initial collection
	if err := m.collectMetrics(); err != nil {
		return fmt.Errorf("initial metrics collection failed: %w", err)
	}

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-m.stopCh:
			return nil
		case <-ticker.C:
			if err := m.collectMetrics(); err != nil {
				// Log error but continue monitoring
				fmt.Printf("Error collecting metrics: %v\n", err)
			}
		}
	}
}

// Stop stops the monitoring
func (m *Monitor) Stop() {
	close(m.stopCh)
}

// GetLatestMetrics returns the most recent metrics
func (m *Monitor) GetLatestMetrics() *SystemMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if m.lastMetrics == nil {
		return nil
	}

	// Return a copy
	metrics := *m.lastMetrics
	return &metrics
}

// collectMetrics gathers all system metrics
func (m *Monitor) collectMetrics() error {
	metrics := &SystemMetrics{
		Timestamp: time.Now(),
		CPUCores:  runtime.NumCPU(),
	}

	// CPU metrics
	cpuPercents, err := cpu.Percent(time.Second, false)
	if err == nil && len(cpuPercents) > 0 {
		metrics.CPUPercent = cpuPercents[0]
	}

	// CPU frequency
	cpuInfo, err := cpu.Info()
	if err == nil && len(cpuInfo) > 0 {
		metrics.CPUFreq = cpuInfo[0].Mhz
	}

	// Memory metrics
	memInfo, err := mem.VirtualMemory()
	if err == nil {
		metrics.MemoryTotal = memInfo.Total
		metrics.MemoryUsed = memInfo.Used
		metrics.MemoryPercent = memInfo.UsedPercent
		metrics.MemoryAvailable = memInfo.Available
	}

	// Disk metrics (root partition)
	diskInfo, err := disk.Usage("/")
	if err == nil {
		metrics.DiskTotal = diskInfo.Total
		metrics.DiskUsed = diskInfo.Used
		metrics.DiskPercent = diskInfo.UsedPercent
		metrics.DiskFree = diskInfo.Free
	}

	// Network metrics
	netInfo, err := net.IOCounters(false)
	if err == nil && len(netInfo) > 0 {
		currentNet := &netInfo[0]
		metrics.NetworkBytesRecv = currentNet.BytesRecv
		metrics.NetworkBytesSent = currentNet.BytesSent
		metrics.NetworkPacketsRecv = currentNet.PacketsRecv
		metrics.NetworkPacketsSent = currentNet.PacketsSent
	}

	// Host info
	hostInfo, err := host.Info()
	if err == nil {
		metrics.Hostname = hostInfo.Hostname
		metrics.Platform = hostInfo.Platform
		metrics.Uptime = hostInfo.Uptime
	}

	// Process count
	processes, err := process.Pids()
	if err == nil {
		metrics.ProcessCount = len(processes)
	}

	// Load averages (Linux/Unix only)
	loadInfo, err := host.LoadAvg()
	if err == nil {
		metrics.LoadAvg1 = loadInfo.Load1
		metrics.LoadAvg5 = loadInfo.Load5
		metrics.LoadAvg15 = loadInfo.Load15
	}

	// Store the metrics
	m.mu.Lock()
	m.lastMetrics = metrics
	m.mu.Unlock()

	return nil
}

// GetProcessMetrics returns metrics for specific processes
func (m *Monitor) GetProcessMetrics(pids []int32) (map[int32]*ProcessMetrics, error) {
	result := make(map[int32]*ProcessMetrics)

	for _, pid := range pids {
		proc, err := process.NewProcess(pid)
		if err != nil {
			continue
		}

		metrics := &ProcessMetrics{
			PID:       pid,
			Timestamp: time.Now(),
		}

		// Get process info
		if name, err := proc.Name(); err == nil {
			metrics.Name = name
		}

		if cpuPercent, err := proc.CPUPercent(); err == nil {
			metrics.CPUPercent = cpuPercent
		}

		if memInfo, err := proc.MemoryInfo(); err == nil {
			metrics.MemoryRSS = memInfo.RSS
			metrics.MemoryVMS = memInfo.VMS
		}

		if status, err := proc.Status(); err == nil {
			metrics.Status = status
		}

		if createTime, err := proc.CreateTime(); err == nil {
			metrics.CreateTime = time.Unix(createTime/1000, 0)
		}

		result[pid] = metrics
	}

	return result, nil
}

// ProcessMetrics contains process-specific metrics
type ProcessMetrics struct {
	PID        int32     `json:"pid"`
	Name       string    `json:"name"`
	CPUPercent float64   `json:"cpu_percent"`
	MemoryRSS  uint64    `json:"memory_rss"`
	MemoryVMS  uint64    `json:"memory_vms"`
	Status     string    `json:"status"`
	CreateTime time.Time `json:"create_time"`
	Timestamp  time.Time `json:"timestamp"`
}

// GetContainerMetrics returns metrics for Docker containers
func (m *Monitor) GetContainerMetrics() (map[string]*ContainerMetrics, error) {
	// This would integrate with Docker API
	// For now, return empty map
	return make(map[string]*ContainerMetrics), nil
}

// ContainerMetrics contains container-specific metrics
type ContainerMetrics struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Image       string    `json:"image"`
	Status      string    `json:"status"`
	CPUPercent  float64   `json:"cpu_percent"`
	MemoryUsage uint64    `json:"memory_usage"`
	MemoryLimit uint64    `json:"memory_limit"`
	NetworkRx   uint64    `json:"network_rx"`
	NetworkTx   uint64    `json:"network_tx"`
	BlockRead   uint64    `json:"block_read"`
	BlockWrite  uint64    `json:"block_write"`
	PIDs        int       `json:"pids"`
	Timestamp   time.Time `json:"timestamp"`
}
