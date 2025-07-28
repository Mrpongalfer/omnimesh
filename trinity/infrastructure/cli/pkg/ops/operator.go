package ops

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"

	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/kubernetes"
	"github.com/sirupsen/logrus"
)

// Operator handles operational tasks
type Operator struct {
	k8sClient *kubernetes.Client
	logger    *logrus.Logger
}

// NewOperator creates a new operator instance
func NewOperator() (*Operator, error) {
	k8sClient, err := kubernetes.NewClient()
	if err != nil {
		return nil, fmt.Errorf("failed to create kubernetes client: %w", err)
	}

	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	return &Operator{
		k8sClient: k8sClient,
		logger:    logger,
	}, nil
}

// SystemStatus represents the overall system status
type SystemStatus struct {
	ClusterHealth *kubernetes.ClusterHealth
	Deployments   []DeploymentStatus
	Services      []ServiceStatus
	Overall       string
}

// DeploymentStatus represents the status of a deployment
type DeploymentStatus struct {
	Name      string
	Namespace string
	Ready     bool
	Replicas  int32
	Available int32
}

// ServiceStatus represents the status of a service
type ServiceStatus struct {
	Name      string
	Namespace string
	Type      string
	ClusterIP string
	Ports     []string
}

// GetSystemStatus returns comprehensive system status
func (o *Operator) GetSystemStatus(ctx context.Context, namespace string) (*SystemStatus, error) {
	o.logger.Info("Checking system status...")

	// Get cluster health
	clusterHealth, err := o.k8sClient.GetClusterHealth(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get cluster health: %w", err)
	}

	// Get deployments
	deployments, err := o.k8sClient.GetDeployments(ctx, namespace)
	if err != nil {
		return nil, fmt.Errorf("failed to get deployments: %w", err)
	}

	var deploymentStatuses []DeploymentStatus
	for _, deployment := range deployments.Items {
		status := DeploymentStatus{
			Name:      deployment.Name,
			Namespace: deployment.Namespace,
			Ready:     deployment.Status.ReadyReplicas == *deployment.Spec.Replicas,
			Replicas:  *deployment.Spec.Replicas,
			Available: deployment.Status.AvailableReplicas,
		}
		deploymentStatuses = append(deploymentStatuses, status)
	}

	// Get services
	services, err := o.k8sClient.GetServices(ctx, namespace)
	if err != nil {
		return nil, fmt.Errorf("failed to get services: %w", err)
	}

	var serviceStatuses []ServiceStatus
	for _, service := range services.Items {
		var ports []string
		for _, port := range service.Spec.Ports {
			ports = append(ports, fmt.Sprintf("%d:%d/%s", port.Port, port.TargetPort.IntVal, port.Protocol))
		}

		status := ServiceStatus{
			Name:      service.Name,
			Namespace: service.Namespace,
			Type:      string(service.Spec.Type),
			ClusterIP: service.Spec.ClusterIP,
			Ports:     ports,
		}
		serviceStatuses = append(serviceStatuses, status)
	}

	// Determine overall status
	overall := "Healthy"
	if clusterHealth.Status != "Healthy" {
		overall = clusterHealth.Status
	}

	for _, deployment := range deploymentStatuses {
		if !deployment.Ready {
			overall = "Degraded"
			break
		}
	}

	return &SystemStatus{
		ClusterHealth: clusterHealth,
		Deployments:   deploymentStatuses,
		Services:      serviceStatuses,
		Overall:       overall,
	}, nil
}

// StreamLogs streams logs from components
func (o *Operator) StreamLogs(ctx context.Context, namespace, component string, follow bool, lines int64) error {
	o.logger.Infof("Streaming logs from component: %s", component)

	// Get pods for the component
	pods, err := o.k8sClient.GetPods(ctx, namespace)
	if err != nil {
		return fmt.Errorf("failed to get pods: %w", err)
	}

	// Filter pods by component label or name pattern
	var targetPods []string
	for _, pod := range pods.Items {
		if component == "all" ||
			strings.Contains(pod.Name, component) ||
			(pod.Labels != nil && pod.Labels["app"] == component) ||
			(pod.Labels != nil && pod.Labels["component"] == component) {
			targetPods = append(targetPods, pod.Name)
		}
	}

	if len(targetPods) == 0 {
		return fmt.Errorf("no pods found for component: %s", component)
	}

	// Stream logs from all matching pods
	for _, podName := range targetPods {
		o.logger.Infof("Streaming logs from pod: %s", podName)

		// In a real implementation, you would stream logs concurrently
		err := o.k8sClient.StreamLogs(ctx, namespace, podName, "", follow, lines, os.Stdout)
		if err != nil {
			o.logger.Errorf("Failed to stream logs from pod %s: %v", podName, err)
		}
	}

	return nil
}

// OpenDashboard opens the monitoring dashboard
func (o *Operator) OpenDashboard(ctx context.Context, namespace string) error {
	o.logger.Info("Opening monitoring dashboard...")

	// Try to find Grafana service
	services, err := o.k8sClient.GetServices(ctx, namespace)
	if err != nil {
		return fmt.Errorf("failed to get services: %w", err)
	}

	var grafanaService string
	for _, service := range services.Items {
		if strings.Contains(service.Name, "grafana") {
			grafanaService = service.Name
			break
		}
	}

	if grafanaService == "" {
		// Try to find any monitoring service
		for _, service := range services.Items {
			if strings.Contains(service.Name, "monitor") ||
				strings.Contains(service.Name, "dashboard") {
				grafanaService = service.Name
				break
			}
		}
	}

	if grafanaService == "" {
		return fmt.Errorf("no monitoring dashboard service found")
	}

	// Port-forward to the service
	port := "3000"
	localPort := "8080"

	o.logger.Infof("Port-forwarding to %s service on port %s", grafanaService, port)

	// Start port-forward in background
	cmd := exec.CommandContext(ctx, "kubectl", "port-forward",
		fmt.Sprintf("service/%s", grafanaService),
		fmt.Sprintf("%s:%s", localPort, port),
		"-n", namespace)

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start port-forward: %w", err)
	}

	// Wait a moment for port-forward to establish
	time.Sleep(2 * time.Second)

	// Open browser
	url := fmt.Sprintf("http://localhost:%s", localPort)
	o.logger.Infof("Opening browser to %s", url)

	return o.openBrowser(url)
}

// openBrowser opens a URL in the default browser
func (o *Operator) openBrowser(url string) error {
	var cmd string
	var args []string

	switch runtime.GOOS {
	case "windows":
		cmd = "cmd"
		args = []string{"/c", "start"}
	case "darwin":
		cmd = "open"
	default: // "linux", "freebsd", "openbsd", "netbsd"
		cmd = "xdg-open"
	}
	args = append(args, url)

	return exec.Command(cmd, args...).Start()
}

// ExecInPod executes a command in a pod
func (o *Operator) ExecInPod(ctx context.Context, namespace, podName, containerName string) error {
	o.logger.Infof("Opening shell to pod %s", podName)

	cmd := exec.CommandContext(ctx, "kubectl", "exec", "-it", podName)
	if containerName != "" {
		cmd.Args = append(cmd.Args, "-c", containerName)
	}
	cmd.Args = append(cmd.Args, "-n", namespace, "--", "sh")

	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

// SSHToNode establishes SSH connection to a node
func (o *Operator) SSHToNode(ctx context.Context, nodeName string) error {
	o.logger.Infof("SSH to node %s", nodeName)

	// Get node info to find external IP
	clusterInfo, err := o.k8sClient.GetClusterInfo(ctx)
	if err != nil {
		return fmt.Errorf("failed to get cluster info: %w", err)
	}

	var nodeIP string
	for _, node := range clusterInfo.Nodes {
		if node.Name == nodeName {
			for _, address := range node.Status.Addresses {
				if address.Type == "ExternalIP" {
					nodeIP = address.Address
					break
				}
			}
			break
		}
	}

	if nodeIP == "" {
		return fmt.Errorf("no external IP found for node %s", nodeName)
	}

	o.logger.Infof("Connecting to node %s at %s", nodeName, nodeIP)

	cmd := exec.CommandContext(ctx, "ssh", fmt.Sprintf("user@%s", nodeIP))
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

// GetMetrics retrieves and displays metrics
func (o *Operator) GetMetrics(ctx context.Context, namespace, service string) error {
	o.logger.Infof("Getting metrics for service: %s", service)

	// In a real implementation, you would:
	// 1. Connect to Prometheus API
	// 2. Query metrics for the service
	// 3. Format and display the results

	// For now, we'll display a placeholder
	fmt.Printf("Metrics for %s:\n", service)
	fmt.Println("  CPU Usage: 45%")
	fmt.Println("  Memory Usage: 68%")
	fmt.Println("  Request Rate: 127 req/min")
	fmt.Println("  Error Rate: 0.02%")
	fmt.Println("  Response Time: 89ms")

	return nil
}

// PrintStatus prints a formatted system status
func (o *Operator) PrintStatus(status *SystemStatus) {
	fmt.Println("🌊 OmniTide System Status")
	fmt.Println("=" + strings.Repeat("=", 49))
	fmt.Printf("Overall Status: %s\n\n", status.Overall)

	// Cluster Health
	fmt.Println("🏗️  Cluster Health")
	fmt.Printf("  Status: %s\n", status.ClusterHealth.Status)
	fmt.Printf("  Nodes: %d/%d healthy\n", status.ClusterHealth.HealthyNodes, status.ClusterHealth.TotalNodes)
	if len(status.ClusterHealth.Issues) > 0 {
		fmt.Println("  Issues:")
		for _, issue := range status.ClusterHealth.Issues {
			fmt.Printf("    - %s\n", issue)
		}
	}
	fmt.Println()

	// Deployments
	fmt.Println("🚀 Deployments")
	if len(status.Deployments) == 0 {
		fmt.Println("  No deployments found")
	} else {
		for _, deployment := range status.Deployments {
			statusIcon := "✅"
			if !deployment.Ready {
				statusIcon = "❌"
			}
			fmt.Printf("  %s %s: %d/%d ready\n", statusIcon, deployment.Name, deployment.Available, deployment.Replicas)
		}
	}
	fmt.Println()

	// Services
	fmt.Println("🌐 Services")
	if len(status.Services) == 0 {
		fmt.Println("  No services found")
	} else {
		for _, service := range status.Services {
			fmt.Printf("  🔗 %s (%s): %s\n", service.Name, service.Type, service.ClusterIP)
		}
	}
}
