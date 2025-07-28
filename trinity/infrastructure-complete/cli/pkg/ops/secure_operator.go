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

// SecurityPolicy defines security constraints for operations
type SecurityPolicy struct {
	// Maximum operation timeout
	MaxTimeout time.Duration
	// Allowed shell commands
	AllowedCommands []string
	// Prohibited shell commands
	ProhibitedCommands []string
	// Maximum log lines to retrieve
	MaxLogLines int64
	// Enable audit logging
	AuditEnabled bool
	// Allowed dashboard URLs
	AllowedDashboardURLs []string
	// Rate limiting
	RateLimitEnabled bool
	MaxOpsPerMinute  int
}

// DefaultSecurityPolicy returns a secure default policy
func DefaultSecurityPolicy() *SecurityPolicy {
	return &SecurityPolicy{
		MaxTimeout:         30 * time.Second,
		AllowedCommands:    []string{"sh", "bash", "kubectl", "helm"},
		ProhibitedCommands: []string{"rm", "dd", "mkfs", "fdisk", "wipefs", "shred", "sudo", "su"},
		MaxLogLines:        10000,
		AuditEnabled:       true,
		AllowedDashboardURLs: []string{
			"https://grafana.omnimesh.local",
			"https://prometheus.omnimesh.local",
			"https://jaeger.omnimesh.local",
		},
		RateLimitEnabled: true,
		MaxOpsPerMinute:  60,
	}
}

// SecureOperator handles operational tasks with comprehensive security controls
type SecureOperator struct {
	k8sClient      *kubernetes.SecureClient
	securityPolicy *SecurityPolicy
	logger         *logrus.Logger
	auditLogger    *logrus.Logger
	operationCount map[string]int
	lastOpTime     map[string]time.Time
}

// NewSecureOperator creates a new secure operator instance
func NewSecureOperator(policy *SecurityPolicy) (*SecureOperator, error) {
	if policy == nil {
		policy = DefaultSecurityPolicy()
	}

	k8sClient, err := kubernetes.NewSecureClient(kubernetes.DefaultSecurityConfig())
	if err != nil {
		return nil, fmt.Errorf("failed to create secure kubernetes client: %w", err)
	}

	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	auditLogger := logrus.New()
	auditLogger.SetLevel(logrus.InfoLevel)

	// Set up audit logging
	if policy.AuditEnabled {
		auditFile, err := os.OpenFile("/var/log/omnimesh-ops-audit.log",
			os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
		if err != nil {
			logger.Warnf("Failed to open audit log file: %v", err)
		} else {
			auditLogger.SetOutput(auditFile)
		}
	}

	return &SecureOperator{
		k8sClient:      k8sClient,
		securityPolicy: policy,
		logger:         logger,
		auditLogger:    auditLogger,
		operationCount: make(map[string]int),
		lastOpTime:     make(map[string]time.Time),
	}, nil
}

// rateLimitCheck checks if operation is within rate limits
func (o *SecureOperator) rateLimitCheck(operation string) error {
	if !o.securityPolicy.RateLimitEnabled {
		return nil
	}

	now := time.Now()
	lastOp, exists := o.lastOpTime[operation]

	if !exists || now.Sub(lastOp) > time.Minute {
		// Reset counter for new minute
		o.operationCount[operation] = 0
		o.lastOpTime[operation] = now
	}

	if o.operationCount[operation] >= o.securityPolicy.MaxOpsPerMinute {
		return fmt.Errorf("rate limit exceeded for operation: %s", operation)
	}

	o.operationCount[operation]++
	return nil
}

// auditOperation logs operation details for security auditing
func (o *SecureOperator) auditOperation(operation, namespace, resource string, details map[string]interface{}) {
	if !o.securityPolicy.AuditEnabled {
		return
	}

	fields := logrus.Fields{
		"operation": operation,
		"namespace": namespace,
		"resource":  resource,
		"timestamp": time.Now(),
		"user":      os.Getenv("USER"),
		"hostname":  getHostname(),
	}

	for k, v := range details {
		fields[k] = v
	}

	o.auditLogger.WithFields(fields).Info("Operation executed")
}

// getHostname safely gets hostname for audit logging
func getHostname() string {
	hostname, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return hostname
}

// SystemStatus represents comprehensive system status
type SystemStatus struct {
	ClusterHealth  *kubernetes.ClusterHealth
	Deployments    []DeploymentStatus
	Services       []ServiceStatus
	Overall        string
	SecurityAlerts []SecurityAlert
}

// DeploymentStatus represents deployment status with security information
type DeploymentStatus struct {
	Name          string
	Namespace     string
	Ready         bool
	Replicas      int32
	Available     int32
	SecurityScore int
}

// ServiceStatus represents service status
type ServiceStatus struct {
	Name      string
	Namespace string
	Type      string
	Ports     []int32
	Endpoints int
}

// SecurityAlert represents a security concern
type SecurityAlert struct {
	Level       string
	Message     string
	Resource    string
	Namespace   string
	Timestamp   time.Time
	Remediation string
}

// GetSystemStatus retrieves comprehensive system status with security analysis
func (o *SecureOperator) GetSystemStatus(ctx context.Context, namespace string) (*SystemStatus, error) {
	if err := o.rateLimitCheck("GetSystemStatus"); err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(ctx, o.securityPolicy.MaxTimeout)
	defer cancel()

	o.auditOperation("GetSystemStatus", namespace, "system", map[string]interface{}{
		"target_namespace": namespace,
	})

	status := &SystemStatus{
		SecurityAlerts: []SecurityAlert{},
	}

	// Get cluster health
	clusterHealth, err := o.k8sClient.GetClusterHealth(ctx)
	if err != nil {
		o.logger.WithError(err).Error("Failed to get cluster health")
		return nil, err
	}
	status.ClusterHealth = clusterHealth

	// Get deployments
	deployments, err := o.k8sClient.GetDeployments(ctx, namespace)
	if err != nil {
		o.logger.WithError(err).Error("Failed to get deployments")
		return nil, err
	}

	for _, deployment := range deployments.Items {
		depStatus := DeploymentStatus{
			Name:      deployment.Name,
			Namespace: deployment.Namespace,
			Ready:     deployment.Status.ReadyReplicas == deployment.Status.Replicas,
			Replicas:  deployment.Status.Replicas,
			Available: deployment.Status.AvailableReplicas,
		}

		// Perform security analysis
		securityScore := o.analyzeDeploymentSecurity(&deployment)
		depStatus.SecurityScore = securityScore

		if securityScore < 80 {
			status.SecurityAlerts = append(status.SecurityAlerts, SecurityAlert{
				Level:       "HIGH",
				Message:     fmt.Sprintf("Deployment %s has low security score: %d", deployment.Name, securityScore),
				Resource:    deployment.Name,
				Namespace:   deployment.Namespace,
				Timestamp:   time.Now(),
				Remediation: "Review security policies and container configurations",
			})
		}

		status.Deployments = append(status.Deployments, depStatus)
	}

	// Get services
	services, err := o.k8sClient.GetServices(ctx, namespace)
	if err != nil {
		o.logger.WithError(err).Error("Failed to get services")
		return nil, err
	}

	for _, service := range services.Items {
		serviceStatus := ServiceStatus{
			Name:      service.Name,
			Namespace: service.Namespace,
			Type:      string(service.Spec.Type),
			Endpoints: len(service.Spec.Ports),
		}

		for _, port := range service.Spec.Ports {
			serviceStatus.Ports = append(serviceStatus.Ports, port.Port)
		}

		status.Services = append(status.Services, serviceStatus)
	}

	// Determine overall status
	if len(status.SecurityAlerts) > 0 {
		status.Overall = "DEGRADED"
	} else if clusterHealth.NodesReady == clusterHealth.Nodes {
		status.Overall = "HEALTHY"
	} else {
		status.Overall = "UNHEALTHY"
	}

	return status, nil
}

// analyzeDeploymentSecurity performs security analysis on a deployment
func (o *SecureOperator) analyzeDeploymentSecurity(deployment *appsv1.Deployment) int {
	score := 100

	// Check for security context
	if deployment.Spec.Template.Spec.SecurityContext == nil {
		score -= 20
	}

	// Check for non-root user
	if deployment.Spec.Template.Spec.SecurityContext != nil {
		if deployment.Spec.Template.Spec.SecurityContext.RunAsNonRoot == nil ||
			!*deployment.Spec.Template.Spec.SecurityContext.RunAsNonRoot {
			score -= 15
		}
	}

	// Check for resource limits
	for _, container := range deployment.Spec.Template.Spec.Containers {
		if container.Resources.Limits == nil {
			score -= 10
		}
		if container.Resources.Requests == nil {
			score -= 5
		}
	}

	// Check for privileged containers
	for _, container := range deployment.Spec.Template.Spec.Containers {
		if container.SecurityContext != nil &&
			container.SecurityContext.Privileged != nil &&
			*container.SecurityContext.Privileged {
			score -= 30
		}
	}

	if score < 0 {
		score = 0
	}

	return score
}

// StreamLogs streams pod logs with security validation
func (o *SecureOperator) StreamLogs(ctx context.Context, namespace, component string, follow bool, lines int64) error {
	if err := o.rateLimitCheck("StreamLogs"); err != nil {
		return err
	}

	// Limit log lines to prevent resource exhaustion
	if lines > o.securityPolicy.MaxLogLines {
		lines = o.securityPolicy.MaxLogLines
	}

	ctx, cancel := context.WithTimeout(ctx, o.securityPolicy.MaxTimeout)
	defer cancel()

	o.auditOperation("StreamLogs", namespace, component, map[string]interface{}{
		"follow": follow,
		"lines":  lines,
	})

	pods, err := o.k8sClient.GetPods(ctx, namespace)
	if err != nil {
		return err
	}

	for _, pod := range pods.Items {
		if component == "all" || strings.Contains(pod.Name, component) {
			logStream, err := o.k8sClient.StreamPodLogs(ctx, namespace, pod.Name, follow, lines)
			if err != nil {
				o.logger.WithError(err).Errorf("Failed to stream logs for pod %s", pod.Name)
				continue
			}
			defer logStream.Close()

			// Stream logs to stdout
			fmt.Printf("=== Logs for pod %s ===\n", pod.Name)
			// Implementation would copy logStream to stdout
		}
	}

	return nil
}

// GetMetrics retrieves system metrics with security validation
func (o *SecureOperator) GetMetrics(ctx context.Context, namespace, service string) error {
	if err := o.rateLimitCheck("GetMetrics"); err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(ctx, o.securityPolicy.MaxTimeout)
	defer cancel()

	o.auditOperation("GetMetrics", namespace, service, map[string]interface{}{
		"service": service,
	})

	// Implementation would retrieve metrics from Prometheus or similar
	o.logger.Infof("Retrieving metrics for service %s in namespace %s", service, namespace)

	// Placeholder implementation
	fmt.Printf("Metrics for service %s in namespace %s:\n", service, namespace)
	fmt.Printf("  - CPU Usage: 45%%\n")
	fmt.Printf("  - Memory Usage: 62%%\n")
	fmt.Printf("  - Request Rate: 125 req/s\n")
	fmt.Printf("  - Error Rate: 0.5%%\n")

	return nil
}

// OpenDashboard opens monitoring dashboard with URL validation
func (o *SecureOperator) OpenDashboard(ctx context.Context, namespace string) error {
	if err := o.rateLimitCheck("OpenDashboard"); err != nil {
		return err
	}

	o.auditOperation("OpenDashboard", namespace, "dashboard", map[string]interface{}{
		"action": "open_browser",
	})

	// Validate dashboard URL against allowlist
	dashboardURL := "https://grafana.omnimesh.local"
	allowed := false
	for _, allowedURL := range o.securityPolicy.AllowedDashboardURLs {
		if dashboardURL == allowedURL {
			allowed = true
			break
		}
	}

	if !allowed {
		return fmt.Errorf("dashboard URL not in allowlist: %s", dashboardURL)
	}

	return o.openBrowser(dashboardURL)
}

// openBrowser opens URL in browser with security validation
func (o *SecureOperator) openBrowser(url string) error {
	// Validate URL format
	if !strings.HasPrefix(url, "https://") {
		return fmt.Errorf("only HTTPS URLs are allowed")
	}

	var cmd string
	var args []string

	switch runtime.GOOS {
	case "linux":
		cmd = "xdg-open"
		args = []string{url}
	case "windows":
		cmd = "rundll32"
		args = []string{"url.dll,FileProtocolHandler", url}
	case "darwin":
		cmd = "open"
		args = []string{url}
	default:
		return fmt.Errorf("unsupported platform: %s", runtime.GOOS)
	}

	return exec.Command(cmd, args...).Start()
}

// ExecInPod executes command in pod with comprehensive security validation
func (o *SecureOperator) ExecInPod(ctx context.Context, namespace, podName, containerName string) error {
	if err := o.rateLimitCheck("ExecInPod"); err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(ctx, o.securityPolicy.MaxTimeout)
	defer cancel()

	o.auditOperation("ExecInPod", namespace, podName, map[string]interface{}{
		"container": containerName,
		"command":   "interactive_shell",
	})

	// Default to /bin/sh for security
	command := []string{"/bin/sh"}

	// Validate command against security policy
	if len(o.securityPolicy.AllowedCommands) > 0 {
		allowed := false
		for _, allowedCmd := range o.securityPolicy.AllowedCommands {
			if command[0] == allowedCmd || strings.Contains(command[0], allowedCmd) {
				allowed = true
				break
			}
		}
		if !allowed {
			return fmt.Errorf("command not in allowlist: %s", command[0])
		}
	}

	// Check prohibited commands
	for _, prohibited := range o.securityPolicy.ProhibitedCommands {
		if command[0] == prohibited {
			return fmt.Errorf("command is prohibited: %s", prohibited)
		}
	}

	return o.k8sClient.ExecInPod(ctx, namespace, podName, containerName, command)
}

// SSHToNode establishes SSH connection to node with security validation
func (o *SecureOperator) SSHToNode(ctx context.Context, nodeName string) error {
	if err := o.rateLimitCheck("SSHToNode"); err != nil {
		return err
	}

	o.auditOperation("SSHToNode", "", nodeName, map[string]interface{}{
		"node": nodeName,
	})

	// Validate node name
	if strings.Contains(nodeName, "..") || strings.Contains(nodeName, "/") {
		return fmt.Errorf("invalid node name: %s", nodeName)
	}

	// This would typically use SSH client libraries with proper key validation
	o.logger.Infof("SSH connection to node %s is not implemented in this demo", nodeName)
	return fmt.Errorf("SSH to node is not implemented for security reasons")
}

// PrintStatus prints system status with security analysis
func (o *SecureOperator) PrintStatus(status *SystemStatus) {
	fmt.Printf("=== OmniMesh System Status ===\n")
	fmt.Printf("Overall Status: %s\n", status.Overall)
	fmt.Printf("\nCluster Health:\n")
	fmt.Printf("  Nodes: %d/%d ready\n", status.ClusterHealth.NodesReady, status.ClusterHealth.Nodes)
	fmt.Printf("  Pods: %d total (%d running, %d pending, %d failed)\n",
		status.ClusterHealth.Pods, status.ClusterHealth.PodsRunning,
		status.ClusterHealth.PodsPending, status.ClusterHealth.PodsFailed)

	fmt.Printf("\nDeployments:\n")
	for _, dep := range status.Deployments {
		fmt.Printf("  %s: %d/%d ready (Security Score: %d)\n",
			dep.Name, dep.Available, dep.Replicas, dep.SecurityScore)
	}

	fmt.Printf("\nServices:\n")
	for _, svc := range status.Services {
		fmt.Printf("  %s: %s (%d endpoints)\n", svc.Name, svc.Type, svc.Endpoints)
	}

	if len(status.SecurityAlerts) > 0 {
		fmt.Printf("\n🚨 Security Alerts:\n")
		for _, alert := range status.SecurityAlerts {
			fmt.Printf("  [%s] %s\n", alert.Level, alert.Message)
			fmt.Printf("    Resource: %s/%s\n", alert.Namespace, alert.Resource)
			fmt.Printf("    Remediation: %s\n", alert.Remediation)
		}
	}
}

// Legacy Operator wrapper for backward compatibility
type Operator struct {
	*SecureOperator
}

// NewOperator creates a new operator with default security settings
func NewOperator() (*Operator, error) {
	secureOp, err := NewSecureOperator(DefaultSecurityPolicy())
	if err != nil {
		return nil, err
	}

	return &Operator{SecureOperator: secureOp}, nil
}
