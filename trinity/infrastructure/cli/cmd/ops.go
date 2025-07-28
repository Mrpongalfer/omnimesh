package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/config"
	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/ops"
)

var opsCmd = &cobra.Command{
	Use:   "ops",
	Short: "Operations and monitoring commands",
	Long:  `Operations and monitoring commands for OmniTide infrastructure.`,
}

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show cluster status",
	Long:  `Show the current status of the OmniTide cluster and its components.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("📊 Checking OmniTide cluster status...")

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		// Get default environment or use dev
		env := "dev"
		envConfig := cfg.GetEnvConfig(env)

		// Initialize operator
		operator, err := ops.NewOperator()
		if err != nil {
			return fmt.Errorf("failed to create operator: %w", err)
		}

		// Get cluster status
		status, err := operator.GetSystemStatus(cmd.Context(), envConfig.Namespace)
		if err != nil {
			return fmt.Errorf("failed to get cluster status: %w", err)
		}

		// Display status
		operator.PrintStatus(status)

		return nil
	},
}

var logsCmd = &cobra.Command{
	Use:   "logs",
	Short: "Show component logs",
	Long:  `Show logs for OmniTide components.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		component, _ := cmd.Flags().GetString("component")
		follow, _ := cmd.Flags().GetBool("follow")
		lines, _ := cmd.Flags().GetInt("lines")

		fmt.Printf("📝 Showing logs for component: %s\n", component)

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		// Get default environment or use dev
		env := "dev"
		envConfig := cfg.GetEnvConfig(env)

		// Initialize operator
		operator, err := ops.NewOperator()
		if err != nil {
			return fmt.Errorf("failed to create operator: %w", err)
		}

		// Get logs
		if err := operator.StreamLogs(cmd.Context(), envConfig.Namespace, component, follow, int64(lines)); err != nil {
			return fmt.Errorf("failed to get logs: %w", err)
		}

		return nil
	},
}

var metricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Show system metrics",
	Long:  `Show metrics for OmniTide components.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		service, _ := cmd.Flags().GetString("service")
		dashboard, _ := cmd.Flags().GetBool("dashboard")

		fmt.Printf("📊 Showing metrics for service: %s\n", service)

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		// Get default environment or use dev
		env := "dev"
		envConfig := cfg.GetEnvConfig(env)

		// Initialize operator
		operator, err := ops.NewOperator()
		if err != nil {
			return fmt.Errorf("failed to create operator: %w", err)
		}

		// Show metrics
		if dashboard {
			if err := operator.OpenDashboard(cmd.Context(), envConfig.Namespace); err != nil {
				return fmt.Errorf("failed to open dashboard: %w", err)
			}
		} else {
			if err := operator.GetMetrics(cmd.Context(), envConfig.Namespace, service); err != nil {
				return fmt.Errorf("failed to get metrics: %w", err)
			}
		}

		return nil
	},
}

var shellCmd = &cobra.Command{
	Use:   "shell",
	Short: "Open shell in cluster",
	Long:  `Open an interactive shell in the OmniTide cluster.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		node, _ := cmd.Flags().GetString("node")
		pod, _ := cmd.Flags().GetString("pod")

		fmt.Println("🐚 Opening shell in cluster...")

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		// Get default environment or use dev
		env := "dev"
		envConfig := cfg.GetEnvConfig(env)

		// Initialize operator
		operator, err := ops.NewOperator()
		if err != nil {
			return fmt.Errorf("failed to create operator: %w", err)
		}

		// Open shell
		if node != "" {
			if err := operator.SSHToNode(cmd.Context(), node); err != nil {
				return fmt.Errorf("failed to SSH to node: %w", err)
			}
		} else if pod != "" {
			if err := operator.ExecInPod(cmd.Context(), envConfig.Namespace, pod, ""); err != nil {
				return fmt.Errorf("failed to exec into pod: %w", err)
			}
		} else {
			return fmt.Errorf("either --node or --pod must be specified")
		}

		return nil
	},
}

var dashboardCmd = &cobra.Command{
	Use:   "dashboard",
	Short: "Open monitoring dashboard",
	Long:  `Open the OmniTide monitoring dashboard in your browser.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("🌐 Opening OmniTide dashboard...")

		// Load configuration
		cfg, err := config.LoadConfig()
		if err != nil {
			return fmt.Errorf("failed to load config: %w", err)
		}

		// Get default environment or use dev
		env := "dev"
		envConfig := cfg.GetEnvConfig(env)

		// Initialize operator
		operator, err := ops.NewOperator()
		if err != nil {
			return fmt.Errorf("failed to create operator: %w", err)
		}

		// Open dashboard
		if err := operator.OpenDashboard(cmd.Context(), envConfig.Namespace); err != nil {
			return fmt.Errorf("failed to open dashboard: %w", err)
		}

		return nil
	},
}

func init() {
	// Add subcommands
	opsCmd.AddCommand(statusCmd)
	opsCmd.AddCommand(logsCmd)
	opsCmd.AddCommand(metricsCmd)
	opsCmd.AddCommand(shellCmd)
	opsCmd.AddCommand(dashboardCmd)

	// Logs command flags
	logsCmd.Flags().StringP("component", "c", "all", "Component to show logs for")
	logsCmd.Flags().BoolP("follow", "f", false, "Follow log output")
	logsCmd.Flags().IntP("lines", "l", 100, "Number of lines to show")

	// Metrics command flags
	metricsCmd.Flags().StringP("service", "s", "all", "Service to show metrics for")
	metricsCmd.Flags().BoolP("dashboard", "", false, "Open Grafana dashboard")

	// Shell command flags
	shellCmd.Flags().StringP("node", "n", "", "Node to connect to")
	shellCmd.Flags().StringP("pod", "p", "", "Pod to connect to")
}
