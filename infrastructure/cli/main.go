package main

import (
	"fmt"
	"os"

	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/cmd"
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "omni-cli",
	Short: "OmniTide Compute Fabric CLI",
	Long: `omni-cli is a unified command-line interface for managing the complete
lifecycle of the OmniTide Compute Fabric, from infrastructure provisioning
to application deployment and operations.

Examples:
  omni-cli infra up --env production
  omni-cli build --component nexus --push
  omni-cli deploy production --strategy canary --canary 10
  omni-cli status
  omni-cli logs --component nexus --follow`,
	Version: "1.0.0",
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func init() {
	// Add all command groups
	rootCmd.AddCommand(cmd.InfraCmd)
	rootCmd.AddCommand(cmd.BuildCmd)
	rootCmd.AddCommand(cmd.ReleaseCmd)
	rootCmd.AddCommand(cmd.DeployCmd)
	rootCmd.AddCommand(cmd.RollbackCmd)
	rootCmd.AddCommand(cmd.PromoteCmd)
	rootCmd.AddCommand(cmd.StatusCmd)
	rootCmd.AddCommand(cmd.LogsCmd)
	rootCmd.AddCommand(cmd.MetricsCmd)
	rootCmd.AddCommand(cmd.ShellCmd)
	rootCmd.AddCommand(cmd.DashboardCmd)
	rootCmd.AddCommand(cmd.ConfigCmd)

	// Add persistent flags that apply to all commands
	rootCmd.PersistentFlags().StringP("config", "c", "", "config file (default is $HOME/.omni-cli.yaml)")
	rootCmd.PersistentFlags().StringP("project", "p", "", "GCP project ID")
	rootCmd.PersistentFlags().StringP("region", "r", "us-central1", "GCP region")
	rootCmd.PersistentFlags().BoolP("verbose", "v", false, "verbose output")
	rootCmd.PersistentFlags().BoolP("dry-run", "d", false, "dry run mode")
}
