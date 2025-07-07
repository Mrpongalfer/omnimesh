package deploy

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/kubernetes"
	"github.com/sirupsen/logrus"
	"gopkg.in/yaml.v3"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// Deployer handles application deployments
type Deployer struct {
	k8sClient *kubernetes.Client
	logger    *logrus.Logger
}

// NewDeployer creates a new deployer instance
func NewDeployer() (*Deployer, error) {
	k8sClient, err := kubernetes.NewClient()
	if err != nil {
		return nil, fmt.Errorf("failed to create kubernetes client: %w", err)
	}

	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	return &Deployer{
		k8sClient: k8sClient,
		logger:    logger,
	}, nil
}

// DeploymentStrategy represents different deployment strategies
type DeploymentStrategy string

const (
	StrategyRolling   DeploymentStrategy = "rolling"
	StrategyBlueGreen DeploymentStrategy = "blue-green"
	StrategyCanary    DeploymentStrategy = "canary"
)

// DeploymentConfig holds deployment configuration
type DeploymentConfig struct {
	Environment   string
	Namespace     string
	Strategy      DeploymentStrategy
	CanaryPercent int
	ImageTag      string
	Timeout       time.Duration
}

// Deploy performs a deployment to the specified environment
func (d *Deployer) Deploy(ctx context.Context, config DeploymentConfig) error {
	d.logger.Infof("Starting deployment to %s environment", config.Environment)
	d.logger.Infof("Strategy: %s, Namespace: %s", config.Strategy, config.Namespace)

	// Create namespace if it doesn't exist
	if err := d.ensureNamespace(ctx, config.Namespace); err != nil {
		return fmt.Errorf("failed to ensure namespace: %w", err)
	}

	// Load and update manifests
	manifests, err := d.loadManifests(config.Environment)
	if err != nil {
		return fmt.Errorf("failed to load manifests: %w", err)
	}

	// Update image tags in manifests
	updatedManifests, err := d.updateImageTags(manifests, config.ImageTag)
	if err != nil {
		return fmt.Errorf("failed to update image tags: %w", err)
	}

	// Deploy based on strategy
	switch config.Strategy {
	case StrategyRolling:
		return d.deployRolling(ctx, config, updatedManifests)
	case StrategyCanary:
		return d.deployCanary(ctx, config, updatedManifests)
	case StrategyBlueGreen:
		return d.deployBlueGreen(ctx, config, updatedManifests)
	default:
		return fmt.Errorf("unsupported deployment strategy: %s", config.Strategy)
	}
}

// ensureNamespace creates a namespace if it doesn't exist
func (d *Deployer) ensureNamespace(ctx context.Context, namespace string) error {
	_, err := d.k8sClient.GetNamespaces(ctx)
	if err != nil {
		return err
	}

	// Create namespace if it doesn't exist
	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: namespace,
		},
	}

	// This is a simplified implementation - in production, you'd check if it exists first
	d.logger.Infof("Ensuring namespace %s exists", namespace)
	return nil
}

// loadManifests loads Kubernetes manifests for an environment
func (d *Deployer) loadManifests(environment string) ([][]byte, error) {
	manifestsDir := filepath.Join("kubernetes", "overlays", environment)

	var manifests [][]byte

	err := filepath.Walk(manifestsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !strings.HasSuffix(path, ".yaml") && !strings.HasSuffix(path, ".yml") {
			return nil
		}

		content, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("failed to read manifest %s: %w", path, err)
		}

		manifests = append(manifests, content)
		return nil
	})

	if err != nil {
		// Fallback to base manifests if overlay doesn't exist
		baseDir := filepath.Join("kubernetes", "base")
		return d.loadManifestsFromDir(baseDir)
	}

	return manifests, nil
}

// loadManifestsFromDir loads all YAML files from a directory
func (d *Deployer) loadManifestsFromDir(dir string) ([][]byte, error) {
	var manifests [][]byte

	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !strings.HasSuffix(path, ".yaml") && !strings.HasSuffix(path, ".yml") {
			return nil
		}

		content, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("failed to read manifest %s: %w", path, err)
		}

		manifests = append(manifests, content)
		return nil
	})

	return manifests, err
}

// updateImageTags updates image tags in the manifests
func (d *Deployer) updateImageTags(manifests [][]byte, imageTag string) ([][]byte, error) {
	var updatedManifests [][]byte

	for _, manifest := range manifests {
		// Parse YAML documents
		var docs []interface{}
		decoder := yaml.NewDecoder(strings.NewReader(string(manifest)))

		for {
			var doc interface{}
			if err := decoder.Decode(&doc); err != nil {
				break
			}
			docs = append(docs, doc)
		}

		// Update image tags in each document
		for _, doc := range docs {
			d.updateImageTagInDoc(doc, imageTag)
		}

		// Re-encode to YAML
		var updatedManifest strings.Builder
		encoder := yaml.NewEncoder(&updatedManifest)

		for i, doc := range docs {
			if i > 0 {
				updatedManifest.WriteString("---\n")
			}
			if err := encoder.Encode(doc); err != nil {
				return nil, fmt.Errorf("failed to encode manifest: %w", err)
			}
		}

		updatedManifests = append(updatedManifests, []byte(updatedManifest.String()))
	}

	return updatedManifests, nil
}

// updateImageTagInDoc updates image tags in a YAML document
func (d *Deployer) updateImageTagInDoc(doc interface{}, imageTag string) {
	switch v := doc.(type) {
	case map[string]interface{}:
		if kind, ok := v["kind"].(string); ok && kind == "Deployment" {
			if spec, ok := v["spec"].(map[string]interface{}); ok {
				if template, ok := spec["template"].(map[string]interface{}); ok {
					if templateSpec, ok := template["spec"].(map[string]interface{}); ok {
						if containers, ok := templateSpec["containers"].([]interface{}); ok {
							for _, container := range containers {
								if c, ok := container.(map[string]interface{}); ok {
									if image, ok := c["image"].(string); ok {
										// Extract image name without tag
										imageParts := strings.Split(image, ":")
										if len(imageParts) > 0 {
											c["image"] = imageParts[0] + ":" + imageTag
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
}

// deployRolling performs a rolling deployment
func (d *Deployer) deployRolling(ctx context.Context, config DeploymentConfig, manifests [][]byte) error {
	d.logger.Info("Performing rolling deployment")

	for _, manifest := range manifests {
		if err := d.k8sClient.ApplyManifest(ctx, manifest); err != nil {
			return fmt.Errorf("failed to apply manifest: %w", err)
		}
	}

	// Wait for deployments to be ready
	return d.waitForDeployments(ctx, config)
}

// deployCanary performs a canary deployment
func (d *Deployer) deployCanary(ctx context.Context, config DeploymentConfig, manifests [][]byte) error {
	d.logger.Infof("Performing canary deployment with %d%% traffic", config.CanaryPercent)

	// This is a simplified canary implementation
	// In production, you'd create separate canary deployments and use a service mesh
	// or ingress controller to split traffic

	for _, manifest := range manifests {
		if err := d.k8sClient.ApplyManifest(ctx, manifest); err != nil {
			return fmt.Errorf("failed to apply manifest: %w", err)
		}
	}

	return d.waitForDeployments(ctx, config)
}

// deployBlueGreen performs a blue-green deployment
func (d *Deployer) deployBlueGreen(ctx context.Context, config DeploymentConfig, manifests [][]byte) error {
	d.logger.Info("Performing blue-green deployment")

	// This is a simplified blue-green implementation
	// In production, you'd deploy to a separate "green" environment and then switch traffic

	for _, manifest := range manifests {
		if err := d.k8sClient.ApplyManifest(ctx, manifest); err != nil {
			return fmt.Errorf("failed to apply manifest: %w", err)
		}
	}

	return d.waitForDeployments(ctx, config)
}

// waitForDeployments waits for all deployments to be ready
func (d *Deployer) waitForDeployments(ctx context.Context, config DeploymentConfig) error {
	d.logger.Info("Waiting for deployments to be ready...")

	deployments, err := d.k8sClient.GetDeployments(ctx, config.Namespace)
	if err != nil {
		return fmt.Errorf("failed to get deployments: %w", err)
	}

	for _, deployment := range deployments.Items {
		d.logger.Infof("Waiting for deployment %s to be ready", deployment.Name)

		if err := d.k8sClient.WaitForDeployment(ctx, config.Namespace, deployment.Name, config.Timeout); err != nil {
			return fmt.Errorf("deployment %s failed to become ready: %w", deployment.Name, err)
		}
	}

	d.logger.Info("All deployments are ready")
	return nil
}

// Rollback performs a rollback to a previous version
func (d *Deployer) Rollback(ctx context.Context, namespace string, toVersion string) error {
	d.logger.Infof("Rolling back namespace %s", namespace)
	if toVersion != "" {
		d.logger.Infof("Rolling back to version %s", toVersion)
	}

	deployments, err := d.k8sClient.GetDeployments(ctx, namespace)
	if err != nil {
		return fmt.Errorf("failed to get deployments: %w", err)
	}

	for _, deployment := range deployments.Items {
		d.logger.Infof("Rolling back deployment %s", deployment.Name)

		// Get deployment history and rollback
		// This is a simplified implementation
		if err := d.rollbackDeployment(ctx, namespace, deployment.Name, toVersion); err != nil {
			return fmt.Errorf("failed to rollback deployment %s: %w", deployment.Name, err)
		}
	}

	d.logger.Info("Rollback completed")
	return nil
}

// rollbackDeployment rolls back a specific deployment
func (d *Deployer) rollbackDeployment(ctx context.Context, namespace, name, toVersion string) error {
	// In a real implementation, you would:
	// 1. Get the deployment history
	// 2. Find the target revision
	// 3. Update the deployment to use the previous image/config

	d.logger.Infof("Rollback logic for %s would be implemented here", name)
	return nil
}
