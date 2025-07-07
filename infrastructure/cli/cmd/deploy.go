package cmd

import (
	"fmt"
	"time"

	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/config"
	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/deploy"
	"github.com/spf13/cobra"
)

var deployCmd = &cobra.Command{
	Use:   "deploy [environment]",
	Short: "Deploy to specified environment",
	Long:  `Deploy OmniTide to the specified environment with advanced deployment strategies.`,
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		environment := args[0]
		strategy, _ := cmd.Flags().GetString("strategy")
		canary, _ := cmd.Flags().GetInt("canary")
		wait, _ := cmd.Flags().GetBool("wait")

		fmt.Printf("🚀 Deploying to %s environment\n", environment)
		fmt.Printf("📈 Using strategy: %s\n", strategy)

		if canary > 0 {
			fmt.Printf("🔄 Canary deployment: %d%% traffic\n", canary)
		}

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		envConfig := cfg.GetEnvConfig(environment)

		// Initialize deployer
		deployer, err := deploy.NewDeployer()
		if err != nil {
			return fmt.Errorf("failed to create deployer: %w", err)
		}

		// Configure deployment
		deployConfig := deploy.DeploymentConfig{
			Environment:   environment,
			Namespace:     envConfig.Namespace,
			Strategy:      deploy.DeploymentStrategy(strategy),
			CanaryPercent: canary,
			ImageTag:      "latest", // TODO: Get from build or release
			Timeout:       10 * time.Minute,
		}

		// Perform deployment
		if err := deployer.Deploy(cmd.Context(), deployConfig); err != nil {
			return fmt.Errorf("deployment failed: %w", err)
		}

		if wait {
			fmt.Println("⏳ Waiting for deployment to complete...")
			// Deployment waits by default in the Deploy method
		}

		fmt.Printf("✅ Deployment to %s completed successfully\n", environment)
		return nil
	},
}

var rollbackCmd = &cobra.Command{
	Use:   "rollback [environment]",
	Short: "Rollback deployment",
	Long:  `Rollback to the previous stable deployment.`,
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		environment := args[0]
		toVersion, _ := cmd.Flags().GetString("to")

		fmt.Printf("⏪ Rolling back %s environment", environment)
		if toVersion != "" {
			fmt.Printf(" to version %s", toVersion)
		}
		fmt.Println()

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		envConfig := cfg.GetEnvConfig(environment)

		// Initialize deployer
		deployer, err := deploy.NewDeployer()
		if err != nil {
			return fmt.Errorf("failed to create deployer: %w", err)
		}

		// Perform rollback
		if err := deployer.Rollback(cmd.Context(), envConfig.Namespace, toVersion); err != nil {
			return fmt.Errorf("rollback failed: %w", err)
		}

		fmt.Printf("✅ Rollback of %s completed successfully\n", environment)
		return nil
	},
}

var promoteCmd = &cobra.Command{
	Use:   "promote",
	Short: "Promote deployment between environments",
	Long:  `Promote a deployment from one environment to another (e.g., staging to production).`,
	RunE: func(cmd *cobra.Command, args []string) error {
		from, _ := cmd.Flags().GetString("from")
		to, _ := cmd.Flags().GetString("to")

		fmt.Printf("🎯 Promoting from %s to %s\n", from, to)

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		fromConfig := cfg.GetEnvConfig(from)
		toConfig := cfg.GetEnvConfig(to)

		// Initialize deployer
		deployer, err := deploy.NewDeployer()
		if err != nil {
			return fmt.Errorf("failed to create deployer: %w", err)
		}

		// Get current version from source environment
		// TODO: Implement logic to get current image tags from source namespace

		// Configure deployment for target environment
		deployConfig := deploy.DeploymentConfig{
			Environment: to,
			Namespace:   toConfig.Namespace,
			Strategy:    deploy.StrategyRolling,
			ImageTag:    "latest", // TODO: Get actual version from source environment
			Timeout:     10 * time.Minute,
		}

		// Deploy to target environment
		if err := deployer.Deploy(cmd.Context(), deployConfig); err != nil {
			return fmt.Errorf("promotion deployment failed: %w", err)
		}

		fmt.Printf("✅ Promotion from %s to %s completed successfully\n", from, to)

		// Log which namespace was used for reference
		fmt.Printf("📍 Source namespace: %s\n", fromConfig.Namespace)
		fmt.Printf("📍 Target namespace: %s\n", toConfig.Namespace)

		return nil
	},
}

func init() {
	// Deploy command flags
	deployCmd.Flags().StringP("strategy", "s", "rolling", "Deployment strategy (rolling, blue-green, canary)")
	deployCmd.Flags().IntP("canary", "", 0, "Canary deployment percentage (0-100)")
	deployCmd.Flags().BoolP("wait", "w", true, "Wait for deployment to complete")

	// Rollback command flags
	rollbackCmd.Flags().StringP("to", "", "", "Rollback to specific version")

	// Promote command flags
	promoteCmd.Flags().StringP("from", "", "staging", "Source environment")
	promoteCmd.Flags().StringP("to", "", "production", "Target environment")
	promoteCmd.MarkFlagRequired("from")
	promoteCmd.MarkFlagRequired("to")
}
