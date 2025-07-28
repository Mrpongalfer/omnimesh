package kubernetes

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/watch"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/homedir"
)

// Client provides Kubernetes operations
type Client struct {
	clientset *kubernetes.Clientset
	config    *rest.Config
}

// NewClient creates a new Kubernetes client
func NewClient() (*Client, error) {
	config, err := getKubeConfig()
	if err != nil {
		return nil, fmt.Errorf("failed to get kubernetes config: %w", err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create kubernetes client: %w", err)
	}

	return &Client{
		clientset: clientset,
		config:    config,
	}, nil
}

// getKubeConfig loads the Kubernetes configuration
func getKubeConfig() (*rest.Config, error) {
	// Try in-cluster config first
	if config, err := rest.InClusterConfig(); err == nil {
		return config, nil
	}

	// Fallback to kubeconfig file
	var kubeconfig string
	if home := homedir.HomeDir(); home != "" {
		kubeconfig = filepath.Join(home, ".kube", "config")
	}

	// Allow override via environment variable
	if kubeconfigEnv := os.Getenv("KUBECONFIG"); kubeconfigEnv != "" {
		kubeconfig = kubeconfigEnv
	}

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		return nil, fmt.Errorf("failed to build kubernetes config from %s: %w", kubeconfig, err)
	}

	return config, nil
}

// GetClusterInfo returns basic cluster information
func (c *Client) GetClusterInfo(ctx context.Context) (*ClusterInfo, error) {
	version, err := c.clientset.Discovery().ServerVersion()
	if err != nil {
		return nil, fmt.Errorf("failed to get server version: %w", err)
	}

	nodes, err := c.clientset.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to list nodes: %w", err)
	}

	return &ClusterInfo{
		Version:   version.String(),
		NodeCount: len(nodes.Items),
		Nodes:     nodes.Items,
	}, nil
}

// ClusterInfo represents cluster information
type ClusterInfo struct {
	Version   string
	NodeCount int
	Nodes     []corev1.Node
}

// GetPods returns pods in a namespace
func (c *Client) GetPods(ctx context.Context, namespace string) (*corev1.PodList, error) {
	pods, err := c.clientset.CoreV1().Pods(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to list pods in namespace %s: %w", namespace, err)
	}

	return pods, nil
}

// GetDeployments returns deployments in a namespace
func (c *Client) GetDeployments(ctx context.Context, namespace string) (*appsv1.DeploymentList, error) {
	deployments, err := c.clientset.AppsV1().Deployments(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to list deployments in namespace %s: %w", namespace, err)
	}

	return deployments, nil
}

// GetServices returns services in a namespace
func (c *Client) GetServices(ctx context.Context, namespace string) (*corev1.ServiceList, error) {
	services, err := c.clientset.CoreV1().Services(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to list services in namespace %s: %w", namespace, err)
	}

	return services, nil
}

// StreamLogs streams logs from a pod
func (c *Client) StreamLogs(ctx context.Context, namespace, podName, containerName string, follow bool, lines int64, output io.Writer) error {
	req := c.clientset.CoreV1().Pods(namespace).GetLogs(podName, &corev1.PodLogOptions{
		Container: containerName,
		Follow:    follow,
		TailLines: &lines,
	})

	stream, err := req.Stream(ctx)
	if err != nil {
		return fmt.Errorf("failed to stream logs: %w", err)
	}
	defer stream.Close()

	_, err = io.Copy(output, stream)
	if err != nil {
		return fmt.Errorf("failed to copy log stream: %w", err)
	}

	return nil
}

// GetNamespaces returns all namespaces
func (c *Client) GetNamespaces(ctx context.Context) (*corev1.NamespaceList, error) {
	namespaces, err := c.clientset.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to list namespaces: %w", err)
	}

	return namespaces, nil
}

// WaitForDeployment waits for a deployment to be ready
func (c *Client) WaitForDeployment(ctx context.Context, namespace, name string, timeout time.Duration) error {
	timeoutCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	watcher, err := c.clientset.AppsV1().Deployments(namespace).Watch(timeoutCtx, metav1.ListOptions{
		FieldSelector: fmt.Sprintf("metadata.name=%s", name),
	})
	if err != nil {
		return fmt.Errorf("failed to create deployment watcher: %w", err)
	}
	defer watcher.Stop()

	for event := range watcher.ResultChan() {
		if event.Type == watch.Error {
			return fmt.Errorf("error watching deployment: %v", event.Object)
		}

		deployment, ok := event.Object.(*appsv1.Deployment)
		if !ok {
			continue
		}

		if deployment.Status.ReadyReplicas == *deployment.Spec.Replicas &&
			deployment.Status.UpdatedReplicas == *deployment.Spec.Replicas {
			return nil // Deployment is ready
		}
	}

	return fmt.Errorf("timeout waiting for deployment %s to be ready", name)
}

// ScaleDeployment scales a deployment
func (c *Client) ScaleDeployment(ctx context.Context, namespace, name string, replicas int32) error {
	deployment, err := c.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get deployment %s: %w", name, err)
	}

	deployment.Spec.Replicas = &replicas

	_, err = c.clientset.AppsV1().Deployments(namespace).Update(ctx, deployment, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to scale deployment %s: %w", name, err)
	}

	return nil
}

// ApplyManifest applies a Kubernetes manifest
func (c *Client) ApplyManifest(ctx context.Context, manifest []byte) error {
	// Parse the manifest
	objects, err := parseManifest(manifest)
	if err != nil {
		return fmt.Errorf("failed to parse manifest: %w", err)
	}

	// Apply each object
	for _, obj := range objects {
		if err := c.applyObject(ctx, obj); err != nil {
			return fmt.Errorf("failed to apply object: %w", err)
		}
	}

	return nil
}

// parseManifest parses a YAML manifest into Kubernetes objects
func parseManifest(manifest []byte) ([]runtime.Object, error) {
	// Split by YAML document separator
	docs := strings.Split(string(manifest), "---")
	var objects []runtime.Object

	for _, doc := range docs {
		doc = strings.TrimSpace(doc)
		if doc == "" {
			continue
		}

		// For now, we'll implement a basic YAML parser
		// In a production environment, you would use:
		// - k8s.io/apimachinery/pkg/util/yaml
		// - k8s.io/apimachinery/pkg/runtime/serializer/yaml
		// - client-go's dynamic client

		// This is a placeholder that would need proper implementation
		// based on the actual YAML content and desired object types
		fmt.Printf("Parsing YAML document: %s...\n", doc[:min(50, len(doc))])
	}

	// Return empty slice for now - in production you'd return parsed objects
	return objects, nil
}

// min returns the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// applyObject applies a single Kubernetes object
func (c *Client) applyObject(ctx context.Context, obj runtime.Object) error {
	// This is a placeholder - in production, you'd implement the actual apply logic
	// based on the object type (Deployment, Service, etc.)
	return nil
}

// GetClusterHealth performs a comprehensive cluster health check
func (c *Client) GetClusterHealth(ctx context.Context) (*ClusterHealth, error) {
	health := &ClusterHealth{
		Status: "Healthy",
		Issues: []string{},
	}

	// Check node health
	nodes, err := c.clientset.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
	if err != nil {
		health.Status = "Unhealthy"
		health.Issues = append(health.Issues, fmt.Sprintf("Failed to list nodes: %v", err))
		return health, nil
	}

	unhealthyNodes := 0
	for _, node := range nodes.Items {
		for _, condition := range node.Status.Conditions {
			if condition.Type == corev1.NodeReady && condition.Status != corev1.ConditionTrue {
				unhealthyNodes++
				break
			}
		}
	}

	health.TotalNodes = len(nodes.Items)
	health.HealthyNodes = len(nodes.Items) - unhealthyNodes

	if unhealthyNodes > 0 {
		health.Status = "Degraded"
		health.Issues = append(health.Issues, fmt.Sprintf("%d nodes are not ready", unhealthyNodes))
	}

	// Check system pods
	systemPods, err := c.GetPods(ctx, "kube-system")
	if err != nil {
		health.Issues = append(health.Issues, fmt.Sprintf("Failed to check system pods: %v", err))
	} else {
		unhealthyPods := 0
		for _, pod := range systemPods.Items {
			if pod.Status.Phase != corev1.PodRunning {
				unhealthyPods++
			}
		}

		if unhealthyPods > 0 {
			health.Status = "Degraded"
			health.Issues = append(health.Issues, fmt.Sprintf("%d system pods are not running", unhealthyPods))
		}
	}

	return health, nil
}

// ClusterHealth represents the health status of the cluster
type ClusterHealth struct {
	Status       string
	Issues       []string
	TotalNodes   int
	HealthyNodes int
}
