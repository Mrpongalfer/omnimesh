package cmd

import (
	"fmt"
	"strings"

	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/config"
	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/ops"
	"github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show system status",
	Long:  `Display comprehensive status of all OmniTide components.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("📊 OmniTide System Status")
		fmt.Println(strings.Repeat("=", 50))

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

		// Get system status
		status, err := operator.GetSystemStatus(cmd.Context(), envConfig.Namespace)
		if err != nil {
			return fmt.Errorf("failed to get system status: %w", err)
		}

		// Print formatted status
		operator.PrintStatus(status)

		return nil
	},
}

var logsCmd = &cobra.Command{
	Use:   "logs",
	Short: "Stream logs from components",
	Long:  `Stream logs from one or more OmniTide components.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		component, _ := cmd.Flags().GetString("component")
		follow, _ := cmd.Flags().GetBool("follow")
		lines, _ := cmd.Flags().GetInt("lines")

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

		if component == "all" {
			fmt.Println("📜 Streaming logs from all components...")
		} else {
			fmt.Printf("📜 Streaming logs from component: %s\n", component)
		}

		// Stream logs
		if err := operator.StreamLogs(cmd.Context(), envConfig.Namespace, component, follow, int64(lines)); err != nil {
			return fmt.Errorf("failed to stream logs: %w", err)
		}

		return nil
	},
}

var metricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Show system metrics",
	Long:  `Display system metrics and performance data.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		service, _ := cmd.Flags().GetString("service")
		dashboard, _ := cmd.Flags().GetBool("dashboard")

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

	RunE: func(cmd *cobra.Command, args []string) error {
		node, _ := cmd.Flags().GetString("node")
		pod, _ := cmd.Flags().GetString("pod")

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

		if node != "" {
			fmt.Printf("🖥️  Opening shell to node: %s\n", node)
			if err := operator.SSHToNode(cmd.Context(), node); err != nil {
				return fmt.Errorf("failed to SSH to node: %w", err)
			}
		} else if pod != "" {
			fmt.Printf("� Opening shell to pod: %s\n", pod)
			if err := operator.ExecInPod(cmd.Context(), envConfig.Namespace, pod, ""); err != nil {
				return fmt.Errorf("failed to exec into pod: %w", err)
			}
		} else {
			return fmt.Errorf("either --node or --pod must be specified")
		}

		return nil
	},
var shellCmd = &cobra.Command{
	Use:   "shell",
	Short: "Open shell to node or pod",
	Long:  `Open an interactive shell to a specific node or pod.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		node, _ := cmd.Flags().GetString("node")
		pod, _ := cmd.Flags().GetString("pod")

		if node != "" {
			fmt.Printf("🖥️  Opening shell to node: %s\n", node)
			// TODO: SSH to node
		} else if pod != "" {
			fmt.Printf("🐳 Opening shell to pod: %s\n", pod)
			// TODO: kubectl exec to pod
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
