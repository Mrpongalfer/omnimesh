package cmd

import (
	"context"
	"fmt"
	"path/filepath"
	"time"

	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/config"
	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/terraform"
	"github.com/spf13/cobra"
)

var infraCmd = &cobra.Command{
	Use:   "infra",
	Short: "Infrastructure management commands",
	Long:  `Manage GCP infrastructure including GKE clusters, VPCs, and supporting services.`,
}

var infraUpCmd = &cobra.Command{
	Use:   "up",
	Short: "Provision infrastructure",
	Long:  `Provision the complete OmniTide infrastructure on Google Cloud Platform.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		env, _ := cmd.Flags().GetString("env")
		fmt.Printf("🚀 Provisioning infrastructure for environment: %s\n", env)

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		envConfig := cfg.GetEnvConfig(env)

		// Initialize Terraform client
		terraformDir := filepath.Join("../") // Assuming running from cli directory
		tfClient, err := terraform.NewClient(terraformDir)
		if err != nil {
			return fmt.Errorf("failed to create terraform client: %w", err)
		}

		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
		defer cancel()

		// Initialize Terraform
		fmt.Println("🔧 Initializing Terraform...")
		if err := tfClient.Init(ctx); err != nil {
			return fmt.Errorf("terraform init failed: %w", err)
		}

		// Create Terraform plan
		fmt.Println("📋 Creating Terraform plan...")
		vars := map[string]string{
			"project_id":  envConfig.ProjectID,
			"region":      envConfig.Region,
			"environment": env,
		}

		planFile, err := tfClient.Plan(ctx, env, vars)
		if err != nil {
			return fmt.Errorf("terraform plan failed: %w", err)
		}

		if planFile == nil {
			fmt.Println("✅ No changes needed")
			return nil
		}

		// Apply Terraform plan
		fmt.Println("🚀 Applying Terraform plan...")
		if err := tfClient.Apply(ctx, *planFile); err != nil {
			return fmt.Errorf("terraform apply failed: %w", err)
		}

		fmt.Printf("✅ Infrastructure provisioned successfully for %s environment\n", env)
		return nil
	},
}

var infraDownCmd = &cobra.Command{
	Use:   "down",
	Short: "Destroy infrastructure",
	Long:  `Safely destroy the OmniTide infrastructure.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		env, _ := cmd.Flags().GetString("env")
		confirm, _ := cmd.Flags().GetBool("confirm")

		if !confirm {
			return fmt.Errorf("--confirm flag required for destructive operations")
		}

		fmt.Printf("🔥 Destroying infrastructure for environment: %s\n", env)

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		envConfig := cfg.GetEnvConfig(env)

		// Initialize Terraform client
		terraformDir := filepath.Join("../")
		tfClient, err := terraform.NewClient(terraformDir)
		if err != nil {
			return fmt.Errorf("failed to create terraform client: %w", err)
		}

		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
		defer cancel()

		// Destroy infrastructure
		vars := map[string]string{
			"project_id":  envConfig.ProjectID,
			"region":      envConfig.Region,
			"environment": env,
		}

		if err := tfClient.Destroy(ctx, env, vars); err != nil {
			return fmt.Errorf("terraform destroy failed: %w", err)
		}

		fmt.Printf("✅ Infrastructure destroyed successfully for %s environment\n", env)
		return nil
	},
}

var infraStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show infrastructure status",
	Long:  `Display the current status of all infrastructure components.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("📊 Infrastructure Status:")

		// Load configuration
		_, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		// Initialize Terraform client
		terraformDir := filepath.Join("../")
		tfClient, err := terraform.NewClient(terraformDir)
		if err != nil {
			return fmt.Errorf("failed to create terraform client: %w", err)
		}

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
		defer cancel()

		// Get Terraform outputs
		outputs, err := tfClient.Output(ctx)
		if err != nil {
			return fmt.Errorf("failed to get terraform outputs: %w", err)
		}

		// Display infrastructure status
		fmt.Println("🏗️  Terraform Infrastructure:")
		if len(outputs) == 0 {
			fmt.Println("  No infrastructure found")
		} else {
			for name, output := range outputs {
				fmt.Printf("  ✅ %s: %v\n", name, output.Value)
			}
		}

		// Get current workspace
		workspace, err := tfClient.GetWorkspaceInfo(ctx)
		if err == nil {
			fmt.Printf("  📁 Current workspace: %s\n", workspace)
		}

		// Show Terraform state summary
		state, err := tfClient.Show(ctx)
		if err == nil && state != nil {
			fmt.Println("  📋 State file exists and is valid")
		}

		return nil
	},
}

func init() {
	// Add subcommands
	infraCmd.AddCommand(infraUpCmd)
	infraCmd.AddCommand(infraDownCmd)
	infraCmd.AddCommand(infraStatusCmd)

	// Add flags
	infraUpCmd.Flags().StringP("env", "e", "dev", "Target environment (dev, staging, prod)")
	infraDownCmd.Flags().StringP("env", "e", "dev", "Target environment (dev, staging, prod)")
	infraDownCmd.Flags().BoolP("confirm", "", false, "Confirm destructive operation")
}
