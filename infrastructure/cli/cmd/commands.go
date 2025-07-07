package cmd

// Export all commands for use in main.go
var (
	InfraCmd    = infraCmd
	BuildCmd    = buildCmd
	ReleaseCmd  = releaseCmd
	DeployCmd   = deployCmd
	RollbackCmd = rollbackCmd
	PromoteCmd  = promoteCmd
	OpsCmd      = opsCmd
	ConfigCmd   = configCmd
)
