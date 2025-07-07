package build

import (
	"context"
	"io/ioutil"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestNewBuilder(t *testing.T) {
	builder := NewBuilder("/tmp/test", "test-registry")
	
	if builder == nil {
		t.Error("Builder should not be nil")
	}
	
	if builder.workspace != "/tmp/test" {
		t.Errorf("Expected workspace '/tmp/test', got %s", builder.workspace)
	}
	
	if builder.registry != "test-registry" {
		t.Errorf("Expected registry 'test-registry', got %s", builder.registry)
	}
}

func TestDetectComponents(t *testing.T) {
	// Create a temporary workspace
	tmpDir, err := ioutil.TempDir("", "test-workspace")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)
	
	// Create mock component directories
	rustDir := filepath.Join(tmpDir, "rust-component")
	os.MkdirAll(rustDir, 0755)
	
	// Create Cargo.toml
	cargoContent := `[package]
name = "test-component"
version = "0.1.0"
`
	ioutil.WriteFile(filepath.Join(rustDir, "Cargo.toml"), []byte(cargoContent), 0644)
	
	// Create Dockerfile
	dockerContent := `FROM rust:latest
WORKDIR /app
COPY . .
RUN cargo build --release
`
	ioutil.WriteFile(filepath.Join(rustDir, "Dockerfile"), []byte(dockerContent), 0644)
	
	// Test detection
	builder := NewBuilder(tmpDir, "test-registry")
	components, err := builder.DetectComponents()
	
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}
	
	if len(components) != 1 {
		t.Errorf("Expected 1 component, got %d", len(components))
	}
	
	if len(components) > 0 {
		component := components[0]
		if component.Name != "rust-component" {
			t.Errorf("Expected component name 'rust-component', got %s", component.Name)
		}
		
		if component.Type != ComponentTypeRust {
			t.Errorf("Expected component type Rust, got %s", component.Type)
		}
	}
}

func TestGetComponent(t *testing.T) {
	// Create a temporary workspace with a component
	tmpDir, err := ioutil.TempDir("", "test-workspace")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)
	
	// Create mock Go component
	goDir := filepath.Join(tmpDir, "go-component")
	os.MkdirAll(goDir, 0755)
	
	// Create go.mod
	goModContent := `module test-component
go 1.21
`
	ioutil.WriteFile(filepath.Join(goDir, "go.mod"), []byte(goModContent), 0644)
	
	// Create Dockerfile
	dockerContent := `FROM golang:latest
WORKDIR /app
COPY . .
RUN go build -o app .
`
	ioutil.WriteFile(filepath.Join(goDir, "Dockerfile"), []byte(dockerContent), 0644)
	
	builder := NewBuilder(tmpDir, "test-registry")
	
	// Test getting existing component
	component, err := builder.GetComponent("go-component")
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}
	
	if component == nil {
		t.Error("Expected component, got nil")
	}
	
	if component != nil && component.Type != ComponentTypeGo {
		t.Errorf("Expected component type Go, got %s", component.Type)
	}
	
	// Test getting non-existing component
	_, err = builder.GetComponent("nonexistent")
	if err == nil {
		t.Error("Expected error for non-existing component, got nil")
	}
}

func TestBuildComponent(t *testing.T) {
	// This test would require Docker to be running
	// For now, we'll just test the component creation
	
	component := Component{
		Name:       "test-component",
		Path:       "/tmp/test",
		Type:       ComponentTypeRust,
		Dockerfile: "/tmp/test/Dockerfile",
		ImageName:  "test-registry/test-component",
	}
	
	if component.Name != "test-component" {
		t.Errorf("Expected component name 'test-component', got %s", component.Name)
	}
	
	if component.Type != ComponentTypeRust {
		t.Errorf("Expected component type Rust, got %s", component.Type)
	}
}

func TestComponentType(t *testing.T) {
	// Test component type constants
	if ComponentTypeRust != "rust" {
		t.Errorf("Expected ComponentTypeRust to be 'rust', got %s", ComponentTypeRust)
	}
	
	if ComponentTypeGo != "go" {
		t.Errorf("Expected ComponentTypeGo to be 'go', got %s", ComponentTypeGo)
	}
	
	if ComponentTypeNode != "node" {
		t.Errorf("Expected ComponentTypeNode to be 'node', got %s", ComponentTypeNode)
	}
	
	if ComponentTypeFlutter != "flutter" {
		t.Errorf("Expected ComponentTypeFlutter to be 'flutter', got %s", ComponentTypeFlutter)
	}
}

func TestBuildAllWithTimeout(t *testing.T) {
	// Test that BuildAll respects context timeout
	builder := NewBuilder("/tmp/empty", "test-registry")
	
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()
	
	err := builder.BuildAll(ctx, "test", false)
	// We expect no error because there are no components to build
	if err != nil {
		t.Errorf("Expected no error for empty workspace, got %v", err)
	}
}
