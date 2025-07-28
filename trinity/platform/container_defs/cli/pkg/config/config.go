package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

// Config represents the CLI configuration
type Config struct {
	ProjectID    string               `mapstructure:"project_id"`
	Region       string               `mapstructure:"region"`
	Environment  string               `mapstructure:"environment"`
	Environments map[string]EnvConfig `mapstructure:"environments"`
}

// EnvConfig represents environment-specific configuration
type EnvConfig struct {
	ProjectID     string `mapstructure:"project_id"`
	Region        string `mapstructure:"region"`
	ClusterName   string `mapstructure:"cluster_name"`
	Namespace     string `mapstructure:"namespace"`
	ImageRegistry string `mapstructure:"image_registry"`
}

// LoadConfig loads configuration from file and environment variables
func LoadConfig() (*Config, error) {
	viper.SetConfigName("omni-cli")
	viper.SetConfigType("yaml")

	// Config file locations
	viper.AddConfigPath(".")
	viper.AddConfigPath("$HOME/.config/omni-cli")
	viper.AddConfigPath("$HOME")

	// Environment variable prefix
	viper.SetEnvPrefix("OMNI")
	viper.AutomaticEnv()

	// Set defaults
	viper.SetDefault("region", "us-central1")
	viper.SetDefault("environment", "dev")

	// Read config file
	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return nil, fmt.Errorf("error reading config file: %w", err)
		}
		// Config file not found; ignore error and use defaults/env vars
	}

	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("error unmarshaling config: %w", err)
	}

	// Validate required fields
	if config.ProjectID == "" {
		return nil, fmt.Errorf("project_id is required (set via config file, --project flag, or OMNI_PROJECT_ID env var)")
	}

	return &config, nil
}

// GetEnvConfig returns configuration for a specific environment
func (c *Config) GetEnvConfig(env string) EnvConfig {
	if envConfig, exists := c.Environments[env]; exists {
		// Override with global defaults if not set
		if envConfig.ProjectID == "" {
			envConfig.ProjectID = c.ProjectID
		}
		if envConfig.Region == "" {
			envConfig.Region = c.Region
		}
		if envConfig.ClusterName == "" {
			envConfig.ClusterName = fmt.Sprintf("%s-omnimesh-cluster", env)
		}
		if envConfig.Namespace == "" {
			envConfig.Namespace = fmt.Sprintf("omnitide-%s", env)
		}
		if envConfig.ImageRegistry == "" {
			envConfig.ImageRegistry = fmt.Sprintf("%s-docker.pkg.dev/%s/%s-omnimesh", c.Region, c.ProjectID, env)
		}
		return envConfig
	}

	// Return default config for environment
	return EnvConfig{
		ProjectID:     c.ProjectID,
		Region:        c.Region,
		ClusterName:   fmt.Sprintf("%s-omnimesh-cluster", env),
		Namespace:     fmt.Sprintf("omnitide-%s", env),
		ImageRegistry: fmt.Sprintf("%s-docker.pkg.dev/%s/%s-omnimesh", c.Region, c.ProjectID, env),
	}
}

// CreateSampleConfig creates a sample configuration file
func CreateSampleConfig() error {
	configDir := filepath.Join(os.Getenv("HOME"), ".config", "omni-cli")
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return fmt.Errorf("error creating config directory: %w", err)
	}

	configFile := filepath.Join(configDir, "omni-cli.yaml")

	sampleConfig := `# OmniTide CLI Configuration
project_id: "your-gcp-project-id"
region: "us-central1"
environment: "dev"

environments:
  dev:
    project_id: "your-dev-project"
    region: "us-central1"
    cluster_name: "dev-omnimesh-cluster"
    namespace: "omnitide-dev"
    image_registry: "us-central1-docker.pkg.dev/your-project/dev-omnimesh"
  
  staging:
    project_id: "your-staging-project"
    region: "us-central1"
    cluster_name: "staging-omnimesh-cluster"
    namespace: "omnitide-staging"
    image_registry: "us-central1-docker.pkg.dev/your-project/staging-omnimesh"
  
  prod:
    project_id: "your-prod-project"
    region: "us-central1"
    cluster_name: "prod-omnimesh-cluster"
    namespace: "omnitide-prod"
    image_registry: "us-central1-docker.pkg.dev/your-project/prod-omnimesh"
`

	if err := os.WriteFile(configFile, []byte(sampleConfig), 0644); err != nil {
		return fmt.Errorf("error writing config file: %w", err)
	}

	fmt.Printf("Sample configuration created at: %s\n", configFile)
	fmt.Println("Please edit this file with your project details.")

	return nil
}
