// Package container provides comprehensive Docker container management
package container

import (
	"context"
	"fmt"
	"io"
	"strings"
	"sync"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
)

// Manager handles Docker container lifecycle operations
type Manager struct {
	client     *client.Client
	mu         sync.RWMutex
	containers map[string]*ContainerInfo
}

// ContainerInfo tracks managed container state
type ContainerInfo struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Image       string            `json:"image"`
	Status      string            `json:"status"`
	Created     time.Time         `json:"created"`
	Ports       map[string]string `json:"ports"`
	Environment map[string]string `json:"environment"`
	Labels      map[string]string `json:"labels"`
	AgentID     string            `json:"agent_id,omitempty"`
	AgentType   string            `json:"agent_type,omitempty"`
}

// DeploymentConfig specifies container deployment parameters
type DeploymentConfig struct {
	AgentID       string            `json:"agent_id"`
	AgentType     string            `json:"agent_type"`
	Image         string            `json:"image"`
	Name          string            `json:"name"`
	Environment   map[string]string `json:"environment"`
	Ports         map[string]string `json:"ports"`
	Volumes       map[string]string `json:"volumes"`
	Memory        int64             `json:"memory_mb"`
	CPUShares     int64             `json:"cpu_shares"`
	RestartPolicy string            `json:"restart_policy"`
	NetworkMode   string            `json:"network_mode"`
	Labels        map[string]string `json:"labels"`
}

// NewManager creates a new container manager
func NewManager() (*Manager, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, fmt.Errorf("failed to create Docker client: %w", err)
	}

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if _, err := cli.Ping(ctx); err != nil {
		return nil, fmt.Errorf("failed to connect to Docker daemon: %w", err)
	}

	return &Manager{
		client:     cli,
		containers: make(map[string]*ContainerInfo),
	}, nil
}

// DeployAgent deploys a new AI agent container
func (m *Manager) DeployAgent(ctx context.Context, config *DeploymentConfig) (*ContainerInfo, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Check if agent already exists
	if existing, exists := m.findContainerByAgentID(config.AgentID); exists {
		if existing.Status == "running" {
			return existing, fmt.Errorf("agent %s already running in container %s", config.AgentID, existing.ID)
		}
		// Remove old container
		if err := m.removeContainer(ctx, existing.ID); err != nil {
			return nil, fmt.Errorf("failed to remove existing container: %w", err)
		}
	}

	// Pull image if needed
	if err := m.pullImage(ctx, config.Image); err != nil {
		return nil, fmt.Errorf("failed to pull image: %w", err)
	}

	// Create container
	containerID, err := m.createContainer(ctx, config)
	if err != nil {
		return nil, fmt.Errorf("failed to create container: %w", err)
	}

	// Start container
	if err := m.client.ContainerStart(ctx, containerID, types.ContainerStartOptions{}); err != nil {
		// Clean up on failure
		m.client.ContainerRemove(ctx, containerID, types.ContainerRemoveOptions{Force: true})
		return nil, fmt.Errorf("failed to start container: %w", err)
	}

	// Get container info
	containerInfo, err := m.getContainerInfo(ctx, containerID)
	if err != nil {
		return nil, fmt.Errorf("failed to get container info: %w", err)
	}

	// Add to tracking
	containerInfo.AgentID = config.AgentID
	containerInfo.AgentType = config.AgentType
	m.containers[containerID] = containerInfo

	return containerInfo, nil
}

// StopAgent stops an agent container
func (m *Manager) StopAgent(ctx context.Context, agentID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	containerInfo, exists := m.findContainerByAgentID(agentID)
	if !exists {
		return fmt.Errorf("agent %s not found", agentID)
	}

	// Stop container with graceful timeout
	timeout := 30
	if err := m.client.ContainerStop(ctx, containerInfo.ID, &timeout); err != nil {
		return fmt.Errorf("failed to stop container %s: %w", containerInfo.ID, err)
	}

	// Update status
	containerInfo.Status = "stopped"

	return nil
}

// RemoveAgent removes an agent container completely
func (m *Manager) RemoveAgent(ctx context.Context, agentID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	containerInfo, exists := m.findContainerByAgentID(agentID)
	if !exists {
		return fmt.Errorf("agent %s not found", agentID)
	}

	// Stop if running
	if containerInfo.Status == "running" {
		timeout := 10
		m.client.ContainerStop(ctx, containerInfo.ID, &timeout)
	}

	// Remove container
	if err := m.removeContainer(ctx, containerInfo.ID); err != nil {
		return fmt.Errorf("failed to remove container: %w", err)
	}

	// Remove from tracking
	delete(m.containers, containerInfo.ID)

	return nil
}

// GetAgentStatus returns the status of an agent
func (m *Manager) GetAgentStatus(agentID string) (*ContainerInfo, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	containerInfo, exists := m.findContainerByAgentID(agentID)
	if !exists {
		return nil, fmt.Errorf("agent %s not found", agentID)
	}

	return containerInfo, nil
}

// ListAgents returns all managed agent containers
func (m *Manager) ListAgents() map[string]*ContainerInfo {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make(map[string]*ContainerInfo)
	for _, info := range m.containers {
		if info.AgentID != "" {
			result[info.AgentID] = info
		}
	}
	return result
}

// RefreshContainerStates updates container status from Docker daemon
func (m *Manager) RefreshContainerStates(ctx context.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	for containerID, info := range m.containers {
		updatedInfo, err := m.getContainerInfo(ctx, containerID)
		if err != nil {
			// Container might have been removed externally
			delete(m.containers, containerID)
			continue
		}

		// Preserve agent info
		updatedInfo.AgentID = info.AgentID
		updatedInfo.AgentType = info.AgentType
		m.containers[containerID] = updatedInfo
	}

	return nil
}

// GetContainerLogs retrieves logs from a container
func (m *Manager) GetContainerLogs(ctx context.Context, agentID string, tail int) (string, error) {
	m.mu.RLock()
	containerInfo, exists := m.findContainerByAgentID(agentID)
	m.mu.RUnlock()

	if !exists {
		return "", fmt.Errorf("agent %s not found", agentID)
	}

	options := types.ContainerLogsOptions{
		ShowStdout: true,
		ShowStderr: true,
		Tail:       fmt.Sprintf("%d", tail),
	}

	logs, err := m.client.ContainerLogs(ctx, containerInfo.ID, options)
	if err != nil {
		return "", fmt.Errorf("failed to get logs: %w", err)
	}
	defer logs.Close()

	logData, err := io.ReadAll(logs)
	if err != nil {
		return "", fmt.Errorf("failed to read logs: %w", err)
	}

	return string(logData), nil
}

// Helper methods

func (m *Manager) findContainerByAgentID(agentID string) (*ContainerInfo, bool) {
	for _, info := range m.containers {
		if info.AgentID == agentID {
			return info, true
		}
	}
	return nil, false
}

func (m *Manager) pullImage(ctx context.Context, image string) error {
	reader, err := m.client.ImagePull(ctx, image, types.ImagePullOptions{})
	if err != nil {
		return err
	}
	defer reader.Close()

	// Read the pull output (could be logged)
	io.Copy(io.Discard, reader)
	return nil
}

func (m *Manager) createContainer(ctx context.Context, config *DeploymentConfig) (string, error) {
	// Convert environment
	env := make([]string, 0, len(config.Environment))
	for key, value := range config.Environment {
		env = append(env, fmt.Sprintf("%s=%s", key, value))
	}

	// Convert ports
	exposedPorts := make(nat.PortSet)
	portBindings := make(nat.PortMap)

	for containerPort, hostPort := range config.Ports {
		port, err := nat.NewPort("tcp", containerPort)
		if err != nil {
			return "", fmt.Errorf("invalid port %s: %w", containerPort, err)
		}
		exposedPorts[port] = struct{}{}
		portBindings[port] = []nat.PortBinding{{HostIP: "0.0.0.0", HostPort: hostPort}}
	}

	// Convert volumes
	binds := make([]string, 0, len(config.Volumes))
	for hostPath, containerPath := range config.Volumes {
		binds = append(binds, fmt.Sprintf("%s:%s", hostPath, containerPath))
	}

	// Create labels
	labels := make(map[string]string)
	for key, value := range config.Labels {
		labels[key] = value
	}
	labels["omnitide.agent_id"] = config.AgentID
	labels["omnitide.agent_type"] = config.AgentType
	labels["omnitide.managed"] = "true"

	// Container configuration
	containerConfig := &container.Config{
		Image:        config.Image,
		Env:          env,
		ExposedPorts: exposedPorts,
		Labels:       labels,
	}

	// Host configuration
	hostConfig := &container.HostConfig{
		PortBindings: portBindings,
		Binds:        binds,
		Memory:       config.Memory * 1024 * 1024, // Convert MB to bytes
		CPUShares:    config.CPUShares,
		NetworkMode:  container.NetworkMode(config.NetworkMode),
		RestartPolicy: container.RestartPolicy{
			Name: config.RestartPolicy,
		},
	}

	// Network configuration
	networkConfig := &network.NetworkingConfig{}

	// Create container
	resp, err := m.client.ContainerCreate(ctx, containerConfig, hostConfig, networkConfig, nil, config.Name)
	if err != nil {
		return "", err
	}

	return resp.ID, nil
}

func (m *Manager) removeContainer(ctx context.Context, containerID string) error {
	return m.client.ContainerRemove(ctx, containerID, types.ContainerRemoveOptions{
		Force:         true,
		RemoveVolumes: true,
	})
}

func (m *Manager) getContainerInfo(ctx context.Context, containerID string) (*ContainerInfo, error) {
	containerJSON, err := m.client.ContainerInspect(ctx, containerID)
	if err != nil {
		return nil, err
	}

	info := &ContainerInfo{
		ID:      containerJSON.ID,
		Name:    strings.TrimPrefix(containerJSON.Name, "/"),
		Image:   containerJSON.Image,
		Status:  containerJSON.State.Status,
		Created: containerJSON.Created,
		Labels:  containerJSON.Config.Labels,
	}

	// Extract environment
	info.Environment = make(map[string]string)
	for _, envVar := range containerJSON.Config.Env {
		parts := strings.SplitN(envVar, "=", 2)
		if len(parts) == 2 {
			info.Environment[parts[0]] = parts[1]
		}
	}

	// Extract ports
	info.Ports = make(map[string]string)
	if containerJSON.NetworkSettings != nil {
		for containerPort, bindings := range containerJSON.NetworkSettings.Ports {
			if len(bindings) > 0 {
				info.Ports[string(containerPort)] = bindings[0].HostPort
			}
		}
	}

	return info, nil
}

// Close closes the Docker client connection
func (m *Manager) Close() error {
	if m.client != nil {
		return m.client.Close()
	}
	return nil
}

// GetDockerVersion returns Docker daemon version info
func (m *Manager) GetDockerVersion(ctx context.Context) (types.Version, error) {
	return m.client.ServerVersion(ctx)
}

// GetDockerInfo returns Docker daemon system info
func (m *Manager) GetDockerInfo(ctx context.Context) (types.Info, error) {
	return m.client.Info(ctx)
}
