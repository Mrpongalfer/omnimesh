package build

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/sirupsen/logrus"
)

// Builder handles building and containerizing components
type Builder struct {
	logger    *logrus.Logger
	workspace string
	registry  string
}

// NewBuilder creates a new builder instance
func NewBuilder(workspace, registry string) *Builder {
	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	return &Builder{
		logger:    logger,
		workspace: workspace,
		registry:  registry,
	}
}

// Component represents a buildable component
type Component struct {
	Name       string
	Path       string
	Type       ComponentType
	Dockerfile string
	ImageName  string
}

// ComponentType represents the type of component
type ComponentType string

const (
	ComponentTypeRust    ComponentType = "rust"
	ComponentTypeGo      ComponentType = "go"
	ComponentTypeNode    ComponentType = "node"
	ComponentTypeFlutter ComponentType = "flutter"
)

// DetectComponents discovers all buildable components in the workspace
func (b *Builder) DetectComponents() ([]Component, error) {
	var components []Component

	// Walk the workspace to find components
	err := filepath.Walk(b.workspace, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			return nil
		}

		// Skip hidden directories and vendor/node_modules
		if strings.HasPrefix(info.Name(), ".") ||
			info.Name() == "vendor" ||
			info.Name() == "node_modules" ||
			info.Name() == "target" {
			return filepath.SkipDir
		}

		component := b.detectComponent(path)
		if component != nil {
			components = append(components, *component)
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to walk workspace: %w", err)
	}

	return components, nil
}

// detectComponent detects the type of component in a directory
func (b *Builder) detectComponent(dir string) *Component {
	// Check for Rust component (Cargo.toml)
	if _, err := os.Stat(filepath.Join(dir, "Cargo.toml")); err == nil {
		dockerfile := filepath.Join(dir, "Dockerfile")
		if _, err := os.Stat(dockerfile); err == nil {
			name := filepath.Base(dir)
			return &Component{
				Name:       name,
				Path:       dir,
				Type:       ComponentTypeRust,
				Dockerfile: dockerfile,
				ImageName:  fmt.Sprintf("%s/%s", b.registry, name),
			}
		}
	}

	// Check for Go component (go.mod)
	if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
		dockerfile := filepath.Join(dir, "Dockerfile")
		if _, err := os.Stat(dockerfile); err == nil {
			name := filepath.Base(dir)
			return &Component{
				Name:       name,
				Path:       dir,
				Type:       ComponentTypeGo,
				Dockerfile: dockerfile,
				ImageName:  fmt.Sprintf("%s/%s", b.registry, name),
			}
		}
	}

	// Check for Node.js component (package.json)
	if _, err := os.Stat(filepath.Join(dir, "package.json")); err == nil {
		dockerfile := filepath.Join(dir, "Dockerfile")
		if _, err := os.Stat(dockerfile); err == nil {
			name := filepath.Base(dir)
			return &Component{
				Name:       name,
				Path:       dir,
				Type:       ComponentTypeNode,
				Dockerfile: dockerfile,
				ImageName:  fmt.Sprintf("%s/%s", b.registry, name),
			}
		}
	}

	// Check for Flutter component (pubspec.yaml)
	if _, err := os.Stat(filepath.Join(dir, "pubspec.yaml")); err == nil {
		dockerfile := filepath.Join(dir, "Dockerfile")
		if _, err := os.Stat(dockerfile); err == nil {
			name := filepath.Base(dir)
			return &Component{
				Name:       name,
				Path:       dir,
				Type:       ComponentTypeFlutter,
				Dockerfile: dockerfile,
				ImageName:  fmt.Sprintf("%s/%s", b.registry, name),
			}
		}
	}

	return nil
}

// BuildComponent builds a specific component
func (b *Builder) BuildComponent(ctx context.Context, component Component, tag string) error {
	b.logger.Infof("Building component: %s (%s)", component.Name, component.Type)

	// Build the Docker image
	imageTag := fmt.Sprintf("%s:%s", component.ImageName, tag)

	cmd := exec.CommandContext(ctx, "docker", "build", "-t", imageTag, component.Path)
	cmd.Dir = component.Path
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to build image for %s: %w", component.Name, err)
	}

	b.logger.Infof("Successfully built %s", imageTag)
	return nil
}

// PushComponent pushes a component image to the registry
func (b *Builder) PushComponent(ctx context.Context, component Component, tag string) error {
	imageTag := fmt.Sprintf("%s:%s", component.ImageName, tag)
	b.logger.Infof("Pushing image: %s", imageTag)

	cmd := exec.CommandContext(ctx, "docker", "push", imageTag)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to push image %s: %w", imageTag, err)
	}

	b.logger.Infof("Successfully pushed %s", imageTag)
	return nil
}

// BuildAll builds all detected components
func (b *Builder) BuildAll(ctx context.Context, tag string, push bool) error {
	components, err := b.DetectComponents()
	if err != nil {
		return fmt.Errorf("failed to detect components: %w", err)
	}

	if len(components) == 0 {
		b.logger.Info("No buildable components found")
		return nil
	}

	b.logger.Infof("Found %d components to build", len(components))

	for _, component := range components {
		if err := b.BuildComponent(ctx, component, tag); err != nil {
			return err
		}

		if push {
			if err := b.PushComponent(ctx, component, tag); err != nil {
				return err
			}
		}
	}

	b.logger.Info("All components built successfully")
	return nil
}

// GetComponent finds a component by name
func (b *Builder) GetComponent(name string) (*Component, error) {
	components, err := b.DetectComponents()
	if err != nil {
		return nil, err
	}

	for _, component := range components {
		if component.Name == name {
			return &component, nil
		}
	}

	return nil, fmt.Errorf("component '%s' not found", name)
}
