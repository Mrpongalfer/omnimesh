package main

import (
	"testing"
	"os"
	"path/filepath"
	"strings"
)

func TestCLIVersion(t *testing.T) {
	// Test that the CLI reports a version
	cmd := rootCmd
	cmd.SetArgs([]string{"--version"})
	
	err := cmd.Execute()
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}
}

func TestCLIHelp(t *testing.T) {
	// Test that the CLI shows help
	cmd := rootCmd
	cmd.SetArgs([]string{"--help"})
	
	err := cmd.Execute()
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}
}

func TestConfigPaths(t *testing.T) {
	// Test configuration file paths
	homeDir, err := os.UserHomeDir()
	if err != nil {
		t.Skip("Cannot get user home directory")
	}
	
	configPaths := []string{
		".",
		filepath.Join(homeDir, ".config", "omni-cli"),
		homeDir,
	}
	
	for _, path := range configPaths {
		if _, err := os.Stat(path); err != nil && !os.IsNotExist(err) {
			t.Errorf("Error checking path %s: %v", path, err)
		}
	}
}

func TestCommandStructure(t *testing.T) {
	// Test that all expected commands are registered
	expectedCommands := []string{
		"infra",
		"build",
		"release",
		"deploy",
		"rollback",
		"promote",
		"status",
		"logs",
		"metrics",
		"shell",
		"dashboard",
		"config",
	}
	
	for _, cmdName := range expectedCommands {
		found := false
		for _, cmd := range rootCmd.Commands() {
			if cmd.Name() == cmdName {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected command %s not found", cmdName)
		}
	}
}

func TestInfraCommandStructure(t *testing.T) {
	// Test infra subcommands
	infraCmd := rootCmd.Find([]string{"infra"})
	if infraCmd == nil {
		t.Fatal("infra command not found")
	}
	
	expectedSubcommands := []string{"up", "down", "status"}
	for _, subCmd := range expectedSubcommands {
		found := false
		for _, cmd := range infraCmd.Commands() {
			if cmd.Name() == subCmd {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected infra subcommand %s not found", subCmd)
		}
	}
}

func TestFlagRegistration(t *testing.T) {
	// Test that persistent flags are registered
	expectedFlags := []string{
		"config",
		"project",
		"region",
		"verbose",
		"dry-run",
	}
	
	for _, flagName := range expectedFlags {
		flag := rootCmd.PersistentFlags().Lookup(flagName)
		if flag == nil {
			t.Errorf("Expected persistent flag %s not found", flagName)
		}
	}
}

func TestCommandDescriptions(t *testing.T) {
	// Test that commands have descriptions
	for _, cmd := range rootCmd.Commands() {
		if cmd.Short == "" {
			t.Errorf("Command %s has no short description", cmd.Name())
		}
		if cmd.Long == "" {
			t.Errorf("Command %s has no long description", cmd.Name())
		}
	}
}

func TestRootCommandMetadata(t *testing.T) {
	// Test root command metadata
	if rootCmd.Use == "" {
		t.Error("Root command has no usage string")
	}
	
	if rootCmd.Short == "" {
		t.Error("Root command has no short description")
	}
	
	if rootCmd.Long == "" {
		t.Error("Root command has no long description")
	}
	
	if rootCmd.Version == "" {
		t.Error("Root command has no version")
	}
}

func TestExampleUsage(t *testing.T) {
	// Test that examples are present in help text
	if !strings.Contains(rootCmd.Long, "Examples:") {
		t.Error("Root command long description should contain examples")
	}
}

func TestCommandUsage(t *testing.T) {
	// Test that commands have proper usage strings
	commands := []string{"infra", "build", "deploy", "logs"}
	
	for _, cmdName := range commands {
		cmd := rootCmd.Find([]string{cmdName})
		if cmd == nil {
			t.Errorf("Command %s not found", cmdName)
			continue
		}
		
		if cmd.Use == "" {
			t.Errorf("Command %s has no usage string", cmdName)
		}
	}
}
