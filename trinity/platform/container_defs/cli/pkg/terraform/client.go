package terraform

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/hashicorp/terraform-exec/tfexec"
	"github.com/sirupsen/logrus"
)

// Client provides Terraform operations
type Client struct {
	tf      *tfexec.Terraform
	workDir string
	logger  *logrus.Logger
}

// NewClient creates a new Terraform client
func NewClient(workDir string) (*Client, error) {
	// Find terraform binary
	terraformPath, err := exec.LookPath("terraform")
	if err != nil {
		return nil, fmt.Errorf("terraform binary not found in PATH: %w", err)
	}

	tf, err := tfexec.NewTerraform(workDir, terraformPath)
	if err != nil {
		return nil, fmt.Errorf("failed to create terraform client: %w", err)
	}

	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)

	return &Client{
		tf:      tf,
		workDir: workDir,
		logger:  logger,
	}, nil
}

// Init initializes the Terraform working directory
func (c *Client) Init(ctx context.Context) error {
	c.logger.Info("Initializing Terraform...")

	err := c.tf.Init(ctx, tfexec.Upgrade(true))
	if err != nil {
		return fmt.Errorf("terraform init failed: %w", err)
	}

	c.logger.Info("Terraform initialization completed successfully")
	return nil
}

// Plan creates a Terraform execution plan
func (c *Client) Plan(ctx context.Context, env string, vars map[string]string) (*string, error) {
	c.logger.Infof("Creating Terraform plan for environment: %s", env)

	planFile := fmt.Sprintf("%s.tfplan", env)

	// Prepare variables
	var options []tfexec.PlanOption
	options = append(options, tfexec.Out(planFile))

	// Add environment variable
	if vars == nil {
		vars = make(map[string]string)
	}
	vars["environment"] = env

	// Convert vars map to terraform variables
	for key, value := range vars {
		options = append(options, tfexec.Var(fmt.Sprintf("%s=%s", key, value)))
	}

	// Check if terraform.tfvars exists
	tfvarsPath := filepath.Join(c.workDir, "terraform.tfvars")
	if _, err := os.Stat(tfvarsPath); err == nil {
		options = append(options, tfexec.VarFile("terraform.tfvars"))
	}

	hasChanges, err := c.tf.Plan(ctx, options...)
	if err != nil {
		return nil, fmt.Errorf("terraform plan failed: %w", err)
	}

	if hasChanges {
		c.logger.Info("Plan created with changes")
		return &planFile, nil
	}

	c.logger.Info("No changes detected")
	return nil, nil
}

// Apply applies a Terraform execution plan
func (c *Client) Apply(ctx context.Context, planFile string) error {
	if planFile == "" {
		return fmt.Errorf("plan file is required for apply")
	}

	c.logger.Infof("Applying Terraform plan: %s", planFile)

	err := c.tf.Apply(ctx, tfexec.DirOrPlan(planFile))
	if err != nil {
		return fmt.Errorf("terraform apply failed: %w", err)
	}

	c.logger.Info("Terraform apply completed successfully")

	// Clean up plan file
	os.Remove(filepath.Join(c.workDir, planFile))

	return nil
}

// Destroy destroys Terraform-managed infrastructure
func (c *Client) Destroy(ctx context.Context, env string, vars map[string]string) error {
	c.logger.Infof("Destroying infrastructure for environment: %s", env)

	// Prepare variables
	var options []tfexec.DestroyOption

	// Add environment variable
	if vars == nil {
		vars = make(map[string]string)
	}
	vars["environment"] = env

	// Convert vars map to terraform variables
	for key, value := range vars {
		options = append(options, tfexec.Var(fmt.Sprintf("%s=%s", key, value)))
	}

	// Check if terraform.tfvars exists
	tfvarsPath := filepath.Join(c.workDir, "terraform.tfvars")
	if _, err := os.Stat(tfvarsPath); err == nil {
		options = append(options, tfexec.VarFile("terraform.tfvars"))
	}

	err := c.tf.Destroy(ctx, options...)
	if err != nil {
		return fmt.Errorf("terraform destroy failed: %w", err)
	}

	c.logger.Info("Infrastructure destroyed successfully")
	return nil
}

// Output retrieves Terraform outputs
func (c *Client) Output(ctx context.Context) (map[string]tfexec.OutputMeta, error) {
	outputs, err := c.tf.Output(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get terraform outputs: %w", err)
	}

	return outputs, nil
}

// Show displays the current state
func (c *Client) Show(ctx context.Context) (*string, error) {
	show, err := c.tf.Show(ctx)
	if err != nil {
		return nil, fmt.Errorf("terraform show failed: %w", err)
	}

	// Convert state to string representation
	if show != nil {
		stateStr := "Terraform state exists and is valid"
		return &stateStr, nil
	}

	return nil, nil
}

// Validate validates the Terraform configuration
func (c *Client) Validate(ctx context.Context) error {
	c.logger.Info("Validating Terraform configuration...")

	valid, err := c.tf.Validate(ctx)
	if err != nil {
		return fmt.Errorf("terraform validation failed: %w", err)
	}

	if valid != nil && !valid.Valid {
		var diagMessages []string
		for _, diag := range valid.Diagnostics {
			diagMessages = append(diagMessages, diag.Summary)
		}
		return fmt.Errorf("terraform validation failed: %s", strings.Join(diagMessages, "; "))
	}

	c.logger.Info("Terraform configuration is valid")
	return nil
}

// Format formats Terraform configuration files
func (c *Client) Format(ctx context.Context) error {
	c.logger.Info("Formatting Terraform files...")

	err := c.tf.FormatWrite(ctx, tfexec.Recursive(true))
	if err != nil {
		return fmt.Errorf("terraform format failed: %w", err)
	}

	c.logger.Info("Terraform files formatted successfully")
	return nil
}

// GetWorkspaceInfo returns information about the current workspace
func (c *Client) GetWorkspaceInfo(ctx context.Context) (string, error) {
	workspace, err := c.tf.WorkspaceShow(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to get workspace info: %w", err)
	}

	return workspace, nil
}
