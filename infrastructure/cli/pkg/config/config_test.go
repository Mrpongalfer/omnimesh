package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadConfig(t *testing.T) {
	// Test loading configuration
	// For now, we'll test that it handles missing config gracefully

	// Set environment variables for testing
	os.Setenv("OMNI_PROJECT_ID", "test-project")
	os.Setenv("OMNI_REGION", "us-west1")
	defer func() {
		os.Unsetenv("OMNI_PROJECT_ID")
		os.Unsetenv("OMNI_REGION")
	}()

	config, err := LoadConfig()
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if config.ProjectID != "test-project" {
		t.Errorf("Expected project ID 'test-project', got %s", config.ProjectID)
	}

	if config.Region != "us-west1" {
		t.Errorf("Expected region 'us-west1', got %s", config.Region)
	}
}

func TestGetEnvConfig(t *testing.T) {
	config := &Config{
		ProjectID: "global-project",
		Region:    "us-central1",
		Environments: map[string]EnvConfig{
			"test": {
				ProjectID: "test-project",
				Region:    "us-west1",
			},
		},
	}

	// Test existing environment
	envConfig := config.GetEnvConfig("test")
	if envConfig.ProjectID != "test-project" {
		t.Errorf("Expected project ID 'test-project', got %s", envConfig.ProjectID)
	}

	// Test non-existing environment (should use defaults)
	envConfig = config.GetEnvConfig("nonexistent")
	if envConfig.ProjectID != "global-project" {
		t.Errorf("Expected project ID 'global-project', got %s", envConfig.ProjectID)
	}
}

func TestCreateSampleConfig(t *testing.T) {
	// Test creating sample configuration
	// Use a temporary directory
	tmpDir, err := os.MkdirTemp("", "omni-cli-test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Override home directory for testing
	originalHome := os.Getenv("HOME")
	os.Setenv("HOME", tmpDir)
	defer os.Setenv("HOME", originalHome)

	err = CreateSampleConfig()
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	// Check if config file was created
	configPath := filepath.Join(tmpDir, ".config", "omni-cli", "omni-cli.yaml")
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		t.Error("Sample config file was not created")
	}
}

func TestConfigDefaults(t *testing.T) {
	// Test that default values are set correctly
	config := &Config{}

	envConfig := config.GetEnvConfig("dev")

	if envConfig.ClusterName == "" {
		t.Error("Cluster name should have a default value")
	}

	if envConfig.Namespace == "" {
		t.Error("Namespace should have a default value")
	}

	if envConfig.ImageRegistry == "" {
		t.Error("Image registry should have a default value")
	}
}
