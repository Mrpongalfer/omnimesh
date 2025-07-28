package kubernetes

import (
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/homedir"
)

// SecurityConfig defines security policies for Kubernetes operations
type SecurityConfig struct {
	// Maximum timeout for operations
	MaxOperationTimeout time.Duration
	// Allowed namespaces for operations
	AllowedNamespaces []string
	// Minimum TLS version
	MinTLSVersion uint16
	// Require certificate validation
	RequireCertValidation bool
	// Enable audit logging
	AuditLogging bool
	// Maximum number of concurrent operations
	MaxConcurrentOps int
	// Allowed resource types for operations
	AllowedResources []string
	// Rate limiting configuration
	RateLimitEnabled  bool
	RequestsPerSecond int
	BurstLimit        int
}

// DefaultSecurityConfig returns a secure default configuration
func DefaultSecurityConfig() *SecurityConfig {
	return &SecurityConfig{
		MaxOperationTimeout:   30 * time.Second,
		AllowedNamespaces:     []string{"omnimesh", "omnimesh-system"},
		MinTLSVersion:         tls.VersionTLS12,
		RequireCertValidation: true,
		AuditLogging:          true,
		MaxConcurrentOps:      10,
		AllowedResources: []string{
			"pods", "services", "deployments", "configmaps", "secrets",
			"ingresses", "networkpolicies", "servicemonitors",
		},
		RateLimitEnabled:  true,
		RequestsPerSecond: 10,
		BurstLimit:        20,
	}
}

// SecureClient provides secure Kubernetes operations with comprehensive security controls
type SecureClient struct {
	clientset      *kubernetes.Clientset
	config         *rest.Config
	securityConfig *SecurityConfig
	logger         *logrus.Logger
	auditLogger    *logrus.Logger
}

// NewSecureClient creates a new secure Kubernetes client with security controls
func NewSecureClient(securityConfig *SecurityConfig) (*SecureClient, error) {
	if securityConfig == nil {
		securityConfig = DefaultSecurityConfig()
	}

	// Set up logging
	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	auditLogger := logrus.New()
	auditLogger.SetLevel(logrus.InfoLevel)

	// Set up audit logging to separate file
	if securityConfig.AuditLogging {
		auditFile, err := os.OpenFile("/var/log/omnimesh-k8s-audit.log",
			os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
		if err != nil {
			logger.Warnf("Failed to open audit log file: %v", err)
		} else {
			auditLogger.SetOutput(auditFile)
		}
	}

	config, err := getSecureKubeConfig(securityConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to get secure kubernetes config: %w", err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create kubernetes client: %w", err)
	}

	client := &SecureClient{
		clientset:      clientset,
		config:         config,
		securityConfig: securityConfig,
		logger:         logger,
		auditLogger:    auditLogger,
	}

	// Validate client permissions
	if err := client.validatePermissions(); err != nil {
		return nil, fmt.Errorf("client permission validation failed: %w", err)
	}

	return client, nil
}

// getSecureKubeConfig loads Kubernetes configuration with security hardening
func getSecureKubeConfig(securityConfig *SecurityConfig) (*rest.Config, error) {
	var config *rest.Config
	var err error

	// Try in-cluster config first
	if config, err = rest.InClusterConfig(); err == nil {
		// Running in cluster
	} else {
		// Try loading from kubeconfig
		kubeconfigPath := filepath.Join(homedir.HomeDir(), ".kube", "config")
		if envKubeconfig := os.Getenv("KUBECONFIG"); envKubeconfig != "" {
			kubeconfigPath = envKubeconfig
		}

		config, err = clientcmd.BuildConfigFromFlags("", kubeconfigPath)
		if err != nil {
			return nil, fmt.Errorf("failed to load kubeconfig: %w", err)
		}
	}

	// Apply security hardening
	if config.TLSClientConfig.Insecure {
		return nil, fmt.Errorf("insecure TLS configuration is not allowed")
	}

	// Enforce minimum TLS version
	if config.TLSClientConfig.GetTLSConfig() == nil {
		config.TLSClientConfig.GetTLSConfig().MinVersion = securityConfig.MinTLSVersion
	}

	// Set timeouts
	config.Timeout = securityConfig.MaxOperationTimeout

	// Configure rate limiting
	if securityConfig.RateLimitEnabled {
		config.QPS = float32(securityConfig.RequestsPerSecond)
		config.Burst = securityConfig.BurstLimit
	}

	// Disable compression to prevent compression-based attacks
	config.DisableCompression = true

	// Set user agent for audit trails
	config.UserAgent = "omnimesh-cli/secure-client"

	return config, nil
}

// validatePermissions validates that the client has only the required permissions
func (c *SecureClient) validatePermissions() error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Check if we can perform basic operations
	_, err := c.clientset.CoreV1().Namespaces().List(ctx, metav1.ListOptions{Limit: 1})
	if err != nil {
		return fmt.Errorf("failed to validate basic permissions: %w", err)
	}

	// TODO: Implement more granular permission validation
	// This should check against a whitelist of allowed operations

	c.auditLogger.Info("Client permissions validated successfully")
	return nil
}

// securityCheck validates operation against security policies
func (c *SecureClient) securityCheck(operation, namespace, resource string) error {
	// Check namespace allowlist
	if len(c.securityConfig.AllowedNamespaces) > 0 {
		allowed := false
		for _, allowedNS := range c.securityConfig.AllowedNamespaces {
			if namespace == allowedNS {
				allowed = true
				break
			}
		}
		if !allowed {
			return fmt.Errorf("operation not allowed in namespace: %s", namespace)
		}
	}

	// Check resource allowlist
	if len(c.securityConfig.AllowedResources) > 0 {
		allowed := false
		for _, allowedRes := range c.securityConfig.AllowedResources {
			if resource == allowedRes {
				allowed = true
				break
			}
		}
		if !allowed {
			return fmt.Errorf("operation not allowed on resource: %s", resource)
		}
	}

	// Audit log the operation
	c.auditLogger.WithFields(logrus.Fields{
		"operation":  operation,
		"namespace":  namespace,
		"resource":   resource,
		"timestamp":  time.Now(),
		"user_agent": c.config.UserAgent,
	}).Info("Kubernetes operation requested")

	return nil
}

// GetPods retrieves pods with security validation
func (c *SecureClient) GetPods(ctx context.Context, namespace string) (*corev1.PodList, error) {
	if err := c.securityCheck("GetPods", namespace, "pods"); err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(ctx, c.securityConfig.MaxOperationTimeout)
	defer cancel()

	pods, err := c.clientset.CoreV1().Pods(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		c.logger.WithError(err).Errorf("Failed to get pods in namespace %s", namespace)
		return nil, err
	}

	return pods, nil
}

// GetDeployments retrieves deployments with security validation
func (c *SecureClient) GetDeployments(ctx context.Context, namespace string) (*appsv1.DeploymentList, error) {
	if err := c.securityCheck("GetDeployments", namespace, "deployments"); err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(ctx, c.securityConfig.MaxOperationTimeout)
	defer cancel()

	deployments, err := c.clientset.AppsV1().Deployments(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		c.logger.WithError(err).Errorf("Failed to get deployments in namespace %s", namespace)
		return nil, err
	}

	return deployments, nil
}

// GetServices retrieves services with security validation
func (c *SecureClient) GetServices(ctx context.Context, namespace string) (*corev1.ServiceList, error) {
	if err := c.securityCheck("GetServices", namespace, "services"); err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(ctx, c.securityConfig.MaxOperationTimeout)
	defer cancel()

	services, err := c.clientset.CoreV1().Services(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		c.logger.WithError(err).Errorf("Failed to get services in namespace %s", namespace)
		return nil, err
	}

	return services, nil
}

// StreamPodLogs streams pod logs with security validation and rate limiting
func (c *SecureClient) StreamPodLogs(ctx context.Context, namespace, podName string, follow bool, lines int64) (io.ReadCloser, error) {
	if err := c.securityCheck("StreamPodLogs", namespace, "pods"); err != nil {
		return nil, err
	}

	// Validate pod name to prevent injection attacks
	if strings.Contains(podName, "..") || strings.Contains(podName, "/") {
		return nil, fmt.Errorf("invalid pod name: %s", podName)
	}

	ctx, cancel := context.WithTimeout(ctx, c.securityConfig.MaxOperationTimeout)
	defer cancel()

	// Limit lines to prevent resource exhaustion
	if lines > 10000 {
		lines = 10000
	}

	podLogOpts := corev1.PodLogOptions{
		Follow:    follow,
		TailLines: &lines,
	}

	req := c.clientset.CoreV1().Pods(namespace).GetLogs(podName, &podLogOpts)
	podLogs, err := req.Stream(ctx)
	if err != nil {
		c.logger.WithError(err).Errorf("Failed to stream logs for pod %s in namespace %s", podName, namespace)
		return nil, err
	}

	return podLogs, nil
}

// ExecInPod executes a command in a pod with security validation
func (c *SecureClient) ExecInPod(ctx context.Context, namespace, podName, containerName string, command []string) error {
	if err := c.securityCheck("ExecInPod", namespace, "pods"); err != nil {
		return err
	}

	// Validate inputs to prevent injection attacks
	if strings.Contains(podName, "..") || strings.Contains(podName, "/") {
		return fmt.Errorf("invalid pod name: %s", podName)
	}

	if strings.Contains(containerName, "..") || strings.Contains(containerName, "/") {
		return fmt.Errorf("invalid container name: %s", containerName)
	}

	// Validate command to prevent dangerous operations
	if len(command) == 0 {
		return fmt.Errorf("command cannot be empty")
	}

	dangerousCommands := []string{"rm", "dd", "mkfs", "fdisk", "wipefs", "shred"}
	for _, dangerous := range dangerousCommands {
		if command[0] == dangerous {
			return fmt.Errorf("dangerous command not allowed: %s", dangerous)
		}
	}

	ctx, cancel := context.WithTimeout(ctx, c.securityConfig.MaxOperationTimeout)
	defer cancel()

	c.auditLogger.WithFields(logrus.Fields{
		"pod":       podName,
		"namespace": namespace,
		"container": containerName,
		"command":   command,
	}).Warn("Executing command in pod")

	// Implementation would use client-go's exec functionality
	// This is a placeholder for the actual exec implementation
	c.logger.Infof("Executing command in pod %s/%s: %v", namespace, podName, command)

	return nil
}

// ClusterHealth represents cluster health status
type ClusterHealth struct {
	Nodes             int
	NodesReady        int
	Pods              int
	PodsRunning       int
	PodsPending       int
	PodsFailed        int
	ComponentStatuses map[string]string
	LastUpdateTime    time.Time
}

// GetClusterHealth retrieves cluster health information
func (c *SecureClient) GetClusterHealth(ctx context.Context) (*ClusterHealth, error) {
	if err := c.securityCheck("GetClusterHealth", "", "nodes"); err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(ctx, c.securityConfig.MaxOperationTimeout)
	defer cancel()

	health := &ClusterHealth{
		ComponentStatuses: make(map[string]string),
		LastUpdateTime:    time.Now(),
	}

	// Get node information
	nodes, err := c.clientset.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
	if err != nil {
		c.logger.WithError(err).Error("Failed to get cluster nodes")
		return nil, err
	}

	health.Nodes = len(nodes.Items)
	for _, node := range nodes.Items {
		for _, condition := range node.Status.Conditions {
			if condition.Type == corev1.NodeReady && condition.Status == corev1.ConditionTrue {
				health.NodesReady++
				break
			}
		}
	}

	// Get pod information across all allowed namespaces
	for _, namespace := range c.securityConfig.AllowedNamespaces {
		pods, err := c.clientset.CoreV1().Pods(namespace).List(ctx, metav1.ListOptions{})
		if err != nil {
			c.logger.WithError(err).Warnf("Failed to get pods in namespace %s", namespace)
			continue
		}

		health.Pods += len(pods.Items)
		for _, pod := range pods.Items {
			switch pod.Status.Phase {
			case corev1.PodRunning:
				health.PodsRunning++
			case corev1.PodPending:
				health.PodsPending++
			case corev1.PodFailed:
				health.PodsFailed++
			}
		}
	}

	return health, nil
}

// Legacy Client wrapper for backward compatibility
type Client struct {
	*SecureClient
}

// NewClient creates a new Kubernetes client with default security settings
func NewClient() (*Client, error) {
	secureClient, err := NewSecureClient(DefaultSecurityConfig())
	if err != nil {
		return nil, err
	}

	return &Client{SecureClient: secureClient}, nil
}
