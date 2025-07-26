package cmd

import (
	"fmt"

	"github.com/Mrpongalfer/omnimesh/infrastructure/cli/pkg/config"
	"github.com/spf13/cobra"
)

var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Configuration management commands",
	Long:  `Manage omni-cli configuration files and settings.`,
}

var configInitCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize configuration file",
	Long:  `Create a sample configuration file with default values.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("🔧 Initializing omni-cli configuration...")

		if err := config.CreateSampleConfig(); err != nil {
			return fmt.Errorf("failed to create sample config: %w", err)
		}

		return nil
	},
}

func init() {
	configCmd.AddCommand(configInitCmd)
}
