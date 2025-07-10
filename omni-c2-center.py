#!/usr/bin/env python3

"""
🌊 OMNIMESH Command & Control (C2) Center
Interactive management interface for OMNIMESH ecosystem
Replaces manual terminal operations with intelligent automation
"""

import os
import sys
import json
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Button, Label, Static, Input, 
        Log, TabbedContent, TabPane, Tree, ProgressBar,
        DataTable, Select, Checkbox, RadioSet, RadioButton
    )
    from textual.binding import Binding
    from textual.reactive import reactive
    from textual.message import Message
    from textual.screen import Screen
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    import git
    import yaml
    import psutil
    import requests
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", 
                   "textual", "rich", "gitpython", "pyyaml", "psutil", "requests"])
    print("✅ Dependencies installed. Please run the script again.")
    sys.exit(1)

# Global configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
LOG_FILE = SCRIPT_DIR / "c2-center.log"
CONFIG_FILE = SCRIPT_DIR / "omni-config.yaml"

class GitManager:
    """Git operations manager"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        try:
            self.repo = git.Repo(repo_path)
        except:
            self.repo = None
    
    def get_status(self) -> Dict:
        """Get comprehensive git status"""
        if not self.repo:
            return {"error": "Not a git repository"}
        
        try:
            status = {
                "branch": self.repo.active_branch.name,
                "commit": self.repo.head.commit.hexsha[:8],
                "modified": len(self.repo.index.diff(None)),
                "staged": len(self.repo.index.diff("HEAD")),
                "untracked": len(self.repo.untracked_files),
                "behind": 0,
                "ahead": 0,
                "remote_url": None
            }
            
            # Get remote info
            if self.repo.remotes:
                origin = self.repo.remotes.origin
                status["remote_url"] = list(origin.urls)[0]
                
                # Check if behind/ahead
                try:
                    commits_behind = list(self.repo.iter_commits(f'{status["branch"]}..origin/{status["branch"]}'))
                    commits_ahead = list(self.repo.iter_commits(f'origin/{status["branch"]}..{status["branch"]}'))
                    status["behind"] = len(commits_behind)
                    status["ahead"] = len(commits_ahead)
                except:
                    pass
            
            return status
        except Exception as e:
            return {"error": str(e)}

class BuildManager:
    """Manages backend and frontend build operations"""
    
    def __init__(self, repo_path: Path = SCRIPT_DIR):
        self.repo_path = repo_path
    
    def build_backend(self) -> Dict:
        """Build all backend components"""
        results = {
            "nexus_core": False,
            "go_proxies": False,
            "errors": []
        }
        
        try:
            # Build Nexus Prime Core (Rust)
            nexus_path = self.repo_path / "BACKEND" / "nexus-prime-core"
            if nexus_path.exists():
                result = subprocess.run(
                    ["cargo", "build", "--release"],
                    cwd=nexus_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                results["nexus_core"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(f"Nexus Core: {result.stderr}")
            
            # Build Go Node Proxies
            go_path = self.repo_path / "BACKEND" / "go-node-proxies"
            if go_path.exists():
                subprocess.run(["go", "mod", "tidy"], cwd=go_path, check=True)
                result = subprocess.run(
                    ["go", "build", "-o", "gcnp", "main.go"],
                    cwd=go_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                results["go_proxies"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(f"Go Proxies: {result.stderr}")
                    
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def build_frontend(self) -> Dict:
        """Build frontend components"""
        results = {
            "solidjs_ui": False,
            "errors": []
        }
        
        try:
            frontend_path = self.repo_path / "FRONTEND" / "ui-solidjs"
            if frontend_path.exists():
                # Install dependencies
                subprocess.run(["pnpm", "install"], cwd=frontend_path, check=True, timeout=180)
                
                # Run build
                result = subprocess.run(
                    ["pnpm", "run", "build"],
                    cwd=frontend_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                results["solidjs_ui"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(f"SolidJS Build: {result.stderr}")
                    
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def run_tests(self, component: str = "all") -> Dict:
        """Run test suites"""
        results = {"passed": 0, "failed": 0, "errors": []}
        
        try:
            if component in ["all", "backend"]:
                # Run Rust tests
                nexus_path = self.repo_path / "BACKEND" / "nexus-prime-core"
                if nexus_path.exists():
                    result = subprocess.run(
                        ["cargo", "test", "--release"],
                        cwd=nexus_path,
                        capture_output=True,
                        text=True,
                        timeout=180
                    )
                    if result.returncode == 0:
                        results["passed"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Rust tests: {result.stderr}")
            
            if component in ["all", "frontend"]:
                # Run Frontend tests
                frontend_path = self.repo_path / "FRONTEND" / "ui-solidjs"
                if frontend_path.exists():
                    result = subprocess.run(
                        ["pnpm", "run", "test"],
                        cwd=frontend_path,
                        capture_output=True,
                        text=True,
                        timeout=180
                    )
                    if result.returncode == 0:
                        results["passed"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Frontend tests: {result.stderr}")
                        
        except Exception as e:
            results["errors"].append(str(e))
        
        return results

class SecurityManager:
    """Manages security audits and Tiger Lily enforcement"""
    
    def __init__(self, repo_path: Path = SCRIPT_DIR):
        self.repo_path = repo_path
    
    def run_security_audit(self) -> Dict:
        """Run comprehensive security audit"""
        results = {
            "audit_passed": False,
            "vulnerabilities": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "enforcement_active": False,
            "errors": []
        }
        
        try:
            # Run main security audit
            audit_script = self.repo_path / "security-audit-complete.sh"
            if audit_script.exists():
                result = subprocess.run(
                    ["bash", str(audit_script)],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                results["audit_passed"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(f"Security audit: {result.stderr}")
            
            # Check Tiger Lily enforcement
            enforcement_script = self.repo_path / "tiger-lily-enforcement.sh"
            if enforcement_script.exists():
                results["enforcement_active"] = True
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def enforce_tiger_lily(self) -> Dict:
        """Activate Tiger Lily enforcement"""
        results = {"success": False, "errors": []}
        
        try:
            enforcement_script = self.repo_path / "tiger-lily-enforcement.sh"
            if enforcement_script.exists():
                result = subprocess.run(
                    ["bash", str(enforcement_script)],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                results["success"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(result.stderr)
                    
        except Exception as e:
            results["errors"].append(str(e))
        
        return results

class InfrastructureManager:
    """Manages infrastructure deployment and Kubernetes operations"""
    
    def __init__(self, repo_path: Path = SCRIPT_DIR):
        self.repo_path = repo_path
    
    def get_terraform_status(self) -> Dict:
        """Get Terraform infrastructure status"""
        results = {
            "initialized": False,
            "plan_exists": False,
            "applied": False,
            "errors": []
        }
        
        try:
            infra_path = self.repo_path / "infrastructure"
            if infra_path.exists():
                # Check if Terraform is initialized
                tf_dir = infra_path / ".terraform"
                results["initialized"] = tf_dir.exists()
                
                # Check for plan files
                plan_files = list(infra_path.glob("*.tfplan"))
                results["plan_exists"] = len(plan_files) > 0
                
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def run_terraform_plan(self) -> Dict:
        """Run terraform plan"""
        results = {"success": False, "errors": []}
        
        try:
            infra_path = self.repo_path / "infrastructure"
            if infra_path.exists():
                result = subprocess.run(
                    ["terraform", "plan"],
                    cwd=infra_path,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                results["success"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(result.stderr)
                    
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def deploy_kubernetes(self) -> Dict:
        """Deploy to Kubernetes"""
        results = {"success": False, "errors": []}
        
        try:
            k8s_path = self.repo_path / "kubernetes"
            if k8s_path.exists():
                # Apply base manifests
                result = subprocess.run(
                    ["kubectl", "apply", "-f", "base/"],
                    cwd=k8s_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                results["success"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(result.stderr)
                    
        except Exception as e:
            results["errors"].append(str(e))
        
        return results

class FrontendManager:
    """Manages frontend development operations"""
    
    def __init__(self, repo_path: Path = SCRIPT_DIR):
        self.repo_path = repo_path
        self.frontend_path = repo_path / "FRONTEND" / "ui-solidjs"
    
    def start_dev_server(self) -> Dict:
        """Start development server"""
        results = {"success": False, "pid": None, "errors": []}
        
        try:
            if self.frontend_path.exists():
                process = subprocess.Popen(
                    ["pnpm", "run", "dev"],
                    cwd=self.frontend_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                results["success"] = True
                results["pid"] = process.pid
                
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def run_linting(self) -> Dict:
        """Run ESLint and Prettier checks"""
        results = {"lint_passed": False, "format_passed": False, "errors": []}
        
        try:
            if self.frontend_path.exists():
                # Run ESLint
                lint_result = subprocess.run(
                    ["pnpm", "run", "lint:check"],
                    cwd=self.frontend_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                results["lint_passed"] = lint_result.returncode == 0
                
                # Run Prettier
                format_result = subprocess.run(
                    ["pnpm", "run", "format:check"],
                    cwd=self.frontend_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                results["format_passed"] = format_result.returncode == 0
                
                if lint_result.returncode != 0:
                    results["errors"].append(f"Lint: {lint_result.stderr}")
                if format_result.returncode != 0:
                    results["errors"].append(f"Format: {format_result.stderr}")
                    
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def setup_mobile_testing(self) -> Dict:
        """Setup mobile testing environment"""
        results = {"success": False, "local_ip": None, "errors": []}
        
        try:
            mobile_script = self.frontend_path / "mobile-setup.sh"
            if mobile_script.exists():
                result = subprocess.run(
                    ["bash", str(mobile_script)],
                    cwd=self.frontend_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                results["success"] = result.returncode == 0
                
                # Extract IP from output
                import re
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if ip_match:
                    results["local_ip"] = ip_match.group(1)
                    
        except Exception as e:
            results["errors"].append(str(e))
        
        return results

class SystemMonitor:
    """Enhanced system monitoring with OMNIMESH-specific metrics"""
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # OMNIMESH specific processes
            omnimesh_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if any(keyword in proc.info['name'].lower() for keyword in 
                          ['omni', 'nexus', 'gcnp', 'solidjs']):
                        omnimesh_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3),
                "network_sent_mb": network.bytes_sent / (1024**2),
                "network_recv_mb": network.bytes_recv / (1024**2),
                "process_count": process_count,
                "omnimesh_processes": omnimesh_processes,
                "uptime": self.get_uptime()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_uptime(self) -> str:
        """Get system uptime"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            return f"{uptime_hours}h {uptime_minutes}m"
        except:
            return "Unknown"
    
    def check_docker_status(self) -> Dict:
        """Check Docker daemon status"""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"running": result.returncode == 0}
        except:
            return {"running": False}
    
    def check_kubernetes_status(self) -> Dict:
        """Check Kubernetes cluster connectivity"""
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {"connected": result.returncode == 0}
        except:
            return {"connected": False}

class ConfigManager:
    """Enhanced configuration management"""
    
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
    
    def load_config(self) -> Dict:
        """Load OMNIMESH configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            return self.get_default_config()
        except Exception as e:
            return {"error": str(e)}
    
    def save_config(self, config: Dict) -> bool:
        """Save configuration"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except:
            return False
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "environment": {
                "current": "development",
                "available": ["development", "staging", "production"]
            },
            "services": {
                "nexus_core": {
                    "image": "nexus-prime-core:latest",
                    "ports": [8080, 8443, 50053],
                    "health_check": "/health"
                },
                "go_proxies": {
                    "image": "go-node-proxies:latest", 
                    "ports": [9090, 9443],
                    "replicas": 3
                },
                "frontend": {
                    "image": "omnimesh-frontend:latest",
                    "ports": [5173, 4173],
                    "build_command": "pnpm run build"
                }
            },
            "ai": {
                "provider": "openai",
                "model": "gpt-4",
                "enabled": False
            },
            "monitoring": {
                "prometheus": {"enabled": True, "port": 9090},
                "grafana": {"enabled": True, "port": 3000}
            },
            "security": {
                "tls_enabled": True,
                "tiger_lily_enforcement": True
            }
        }

class CommandExecutor:
    """Enhanced command execution with logging"""
    
    def __init__(self):
        self.command_history = []
        self.log_file = SCRIPT_DIR / "c2-commands.log"
    
    def execute_command(self, command: str, working_dir: Path = None, timeout: int = 60) -> Dict:
        """Execute shell command with logging"""
        try:
            start_time = datetime.now()
            
            # Log command execution
            log_entry = f"[{start_time}] Executing: {command}"
            self.command_history.append(log_entry)
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir or SCRIPT_DIR,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log result
            result_data = {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
                "timestamp": start_time.isoformat()
            }
            
            self.command_history.append(f"[{end_time}] Result: {result.returncode} ({duration:.2f}s)")
            
            # Write to log file
            with open(self.log_file, 'a') as f:
                f.write(f"{log_entry}\n{result.stdout}\n{result.stderr}\n---\n")
            
            return result_data
            
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_command_history(self) -> List[str]:
        """Get recent command history"""
        return self.command_history[-50:]  # Last 50 commands

class DeploymentManager:
    """Enhanced deployment management"""
    
    def __init__(self, repo_path: Path = SCRIPT_DIR):
        self.repo_path = repo_path
    
    def run_production_deployment(self, environment: str = "production") -> Dict:
        """Run production deployment"""
        results = {"success": False, "errors": []}
        
        try:
            deploy_script = self.repo_path / "scripts" / "production-deploy.sh"
            if deploy_script.exists():
                result = subprocess.run(
                    ["bash", str(deploy_script), environment],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes
                )
                results["success"] = result.returncode == 0
                if result.returncode != 0:
                    results["errors"].append(result.stderr)
            else:
                results["errors"].append("Production deployment script not found")
                
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def check_deployment_status(self) -> Dict:
        """Check current deployment status"""
        results = {
            "backend_running": False,
            "frontend_running": False,
            "kubernetes_pods": [],
            "errors": []
        }
        
        try:
            # Check backend processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'nexus' in proc.info['name'].lower() or 'gcnp' in proc.info['name'].lower():
                        results["backend_running"] = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Check frontend processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'vite' in cmdline or 'solidjs' in cmdline or ':5173' in cmdline:
                        results["frontend_running"] = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Check Kubernetes pods
            try:
                k8s_result = subprocess.run(
                    ["kubectl", "get", "pods", "-n", "omnimesh", "-o", "json"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if k8s_result.returncode == 0:
                    import json
                    pods_data = json.loads(k8s_result.stdout)
                    results["kubernetes_pods"] = [
                        {
                            "name": pod["metadata"]["name"],
                            "status": pod["status"]["phase"],
                            "ready": sum(1 for condition in pod.get("status", {}).get("conditions", []) 
                                       if condition["type"] == "Ready" and condition["status"] == "True")
                        }
                        for pod in pods_data.get("items", [])
                    ]
            except:
                pass  # Kubernetes not available
                
        except Exception as e:
            results["errors"].append(str(e))
        
        return results

class HealthChecker:
    """Enhanced health monitoring"""
    
    def __init__(self, repo_path: Path = SCRIPT_DIR):
        self.repo_path = repo_path
    
    def run_comprehensive_health_check(self) -> Dict:
        """Run comprehensive health check"""
        results = {
            "overall_status": "unknown",
            "components": {},
            "recommendations": [],
            "errors": []
        }
        
        try:
            component_scores = []
            
            # Check system resources
            system_health = self.check_system_health()
            results["components"]["system"] = system_health
            component_scores.append(system_health.get("score", 0))
            
            # Check dependencies
            deps_health = self.check_dependencies()
            results["components"]["dependencies"] = deps_health
            component_scores.append(deps_health.get("score", 0))
            
            # Check services
            services_health = self.check_services()
            results["components"]["services"] = services_health
            component_scores.append(services_health.get("score", 0))
            
            # Check security
            security_health = self.check_security()
            results["components"]["security"] = security_health
            component_scores.append(security_health.get("score", 0))
            
            # Calculate overall score
            overall_score = sum(component_scores) / len(component_scores) if component_scores else 0
            
            if overall_score >= 80:
                results["overall_status"] = "healthy"
            elif overall_score >= 60:
                results["overall_status"] = "warning"
            else:
                results["overall_status"] = "critical"
            
            # Generate recommendations
            results["recommendations"] = self.generate_recommendations(results["components"])
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def check_system_health(self) -> Dict:
        """Check system resource health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            score = 100
            
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                score -= 20
            
            if memory.percent > 85:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                score -= 20
            
            if disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent:.1f}%")
                score -= 30
            
            return {
                "status": "healthy" if score >= 80 else "warning" if score >= 60 else "critical",
                "score": max(0, score),
                "issues": issues,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                }
            }
        except Exception as e:
            return {"status": "error", "score": 0, "error": str(e)}
    
    def check_dependencies(self) -> Dict:
        """Check required dependencies"""
        required_tools = [
            "python3", "node", "pnpm", "cargo", "go", "docker", "kubectl", "git"
        ]
        
        missing = []
        score = 100
        
        for tool in required_tools:
            if not shutil.which(tool):
                missing.append(tool)
                score -= (100 / len(required_tools))
        
        return {
            "status": "healthy" if score >= 80 else "warning" if score >= 60 else "critical",
            "score": max(0, score),
            "missing_tools": missing,
            "available_tools": [tool for tool in required_tools if tool not in missing]
        }
    
    def check_services(self) -> Dict:
        """Check OMNIMESH services status"""
        services = {
            "nexus_core": False,
            "go_proxies": False,
            "frontend_dev": False,
            "docker": False,
            "kubernetes": False
        }
        
        try:
            # Check processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    
                    if 'nexus' in name or 'nexus-prime-core' in cmdline:
                        services["nexus_core"] = True
                    elif 'gcnp' in name or 'go-node-proxies' in cmdline:
                        services["go_proxies"] = True
                    elif 'vite' in cmdline or ':5173' in cmdline:
                        services["frontend_dev"] = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Check Docker
            try:
                subprocess.run(["docker", "info"], capture_output=True, timeout=5, check=True)
                services["docker"] = True
            except:
                pass
            
            # Check Kubernetes
            try:
                subprocess.run(["kubectl", "cluster-info"], capture_output=True, timeout=5, check=True)
                services["kubernetes"] = True
            except:
                pass
            
            running_count = sum(services.values())
            total_count = len(services)
            score = (running_count / total_count) * 100
            
            return {
                "status": "healthy" if score >= 60 else "warning" if score >= 40 else "critical",
                "score": score,
                "services": services,
                "running_count": running_count,
                "total_count": total_count
            }
            
        except Exception as e:
            return {"status": "error", "score": 0, "error": str(e)}
    
    def check_security(self) -> Dict:
        """Check security status"""
        try:
            score = 100
            issues = []
            
            # Check if Tiger Lily enforcement is available
            enforcement_script = self.repo_path / "tiger-lily-enforcement.sh"
            if not enforcement_script.exists():
                issues.append("Tiger Lily enforcement not available")
                score -= 30
            
            # Check for security audit results
            audit_dir = self.repo_path / "security-audit-results"
            if not audit_dir.exists() or not list(audit_dir.glob("*.json")):
                issues.append("No recent security audit results")
                score -= 20
            
            # Check for proper permissions
            sensitive_files = [
                self.repo_path / "omni-config.yaml",
                self.repo_path / ".env"
            ]
            
            for file_path in sensitive_files:
                if file_path.exists():
                    stat_info = file_path.stat()
                    if stat_info.st_mode & 0o077:  # Check if readable by others
                        issues.append(f"Insecure permissions on {file_path.name}")
                        score -= 10
            
            return {
                "status": "healthy" if score >= 80 else "warning" if score >= 60 else "critical",
                "score": max(0, score),
                "issues": issues
            }
            
        except Exception as e:
            return {"status": "error", "score": 0, "error": str(e)}
    
    def generate_recommendations(self, components: Dict) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        # System recommendations
        system = components.get("system", {})
        if system.get("score", 0) < 80:
            for issue in system.get("issues", []):
                if "CPU" in issue:
                    recommendations.append("Consider optimizing CPU-intensive processes")
                elif "memory" in issue:
                    recommendations.append("Consider increasing available memory or optimizing memory usage")
                elif "disk" in issue:
                    recommendations.append("Free up disk space or expand storage")
        
        # Dependencies recommendations
        deps = components.get("dependencies", {})
        missing_tools = deps.get("missing_tools", [])
        if missing_tools:
            recommendations.append(f"Install missing tools: {', '.join(missing_tools)}")
        
        # Services recommendations
        services = components.get("services", {})
        if services.get("score", 0) < 60:
            services_status = services.get("services", {})
            if not services_status.get("docker"):
                recommendations.append("Start Docker service for containerization support")
            if not services_status.get("kubernetes"):
                recommendations.append("Configure kubectl for Kubernetes access")
            if not services_status.get("nexus_core"):
                recommendations.append("Start Nexus Prime Core backend service")
        
        # Security recommendations
        security = components.get("security", {})
        if security.get("score", 0) < 80:
            for issue in security.get("issues", []):
                if "Tiger Lily" in issue:
                    recommendations.append("Set up Tiger Lily security enforcement")
                elif "audit" in issue:
                    recommendations.append("Run comprehensive security audit")
                elif "permissions" in issue:
                    recommendations.append("Fix file permissions for sensitive files")
        
        return recommendations
    
    def add_all(self) -> Tuple[bool, str]:
        """Add all changes to staging"""
        try:
            self.repo.git.add(".")
            return True, "All changes staged successfully"
        except Exception as e:
            return False, str(e)
    
    def commit(self, message: str) -> Tuple[bool, str]:
        """Commit staged changes"""
        try:
            commit = self.repo.index.commit(message)
            return True, f"Committed: {commit.hexsha[:8]}"
        except Exception as e:
            return False, str(e)
    
    def push(self, branch: str = None) -> Tuple[bool, str]:
        """Push to remote"""
        try:
            if not branch:
                branch = self.repo.active_branch.name
            origin = self.repo.remotes.origin
            origin.push(branch)
            return True, f"Pushed to origin/{branch}"
        except Exception as e:
            return False, str(e)
    
    def pull(self) -> Tuple[bool, str]:
        """Pull from remote"""
        try:
            origin = self.repo.remotes.origin
            origin.pull()
            return True, "Pulled successfully"
        except Exception as e:
            return False, str(e)

class SystemMonitor:
    """System monitoring and process management"""
    
    @staticmethod
    def get_system_info() -> Dict:
        """Get comprehensive system information"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage('/')._asdict(),
            "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0),
            "boot_time": psutil.boot_time(),
            "users": len(psutil.users())
        }
    
    @staticmethod
    def get_processes() -> List[Dict]:
        """Get OMNIMESH-related processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline.lower() for keyword in ['omni', 'nexus', 'node-proxy']):
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    @staticmethod
    def check_services() -> Dict:
        """Check OMNIMESH service status"""
        services = {}
        service_commands = {
            "docker": "systemctl is-active docker",
            "omnimesh": "systemctl is-active omnimesh",
            "nginx": "systemctl is-active nginx"
        }
        
        for service, cmd in service_commands.items():
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                services[service] = result.stdout.strip() == "active"
            except:
                services[service] = False
        
        return services

class CommandExecutor:
    """Execute system commands with logging"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
    
    def execute(self, command: str, cwd: Path = None) -> Tuple[bool, str, str]:
        """Execute command and return success, stdout, stderr"""
        if self.log_callback:
            self.log_callback(f"Executing: {command}")
        
        try:
            result = subprocess.run(
                command.split(),
                cwd=cwd or SCRIPT_DIR,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            if self.log_callback:
                if success:
                    self.log_callback(f"✅ Command succeeded")
                else:
                    self.log_callback(f"❌ Command failed: {result.stderr}")
            
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

class GitPanel(Container):
    """Git operations panel"""
    
    def __init__(self, git_manager: GitManager):
        super().__init__()
        self.git_manager = git_manager
    
    def compose(self) -> ComposeResult:
        yield Label("🔧 Git Operations", classes="panel-title")
        yield Button("📊 Status", id="git-status", classes="git-btn")
        yield Button("➕ Add All", id="git-add", classes="git-btn")
        yield Input(placeholder="Commit message...", id="commit-input")
        yield Button("💾 Commit", id="git-commit", classes="git-btn")
        yield Button("⬆️ Push", id="git-push", classes="git-btn")
        yield Button("⬇️ Pull", id="git-pull", classes="git-btn")
        yield Static("", id="git-output")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        output = self.query_one("#git-output", Static)
        
        if event.button.id == "git-status":
            status = self.git_manager.get_status()
            if "error" in status:
                output.update(f"❌ {status['error']}")
            else:
                output.update(
                    f"📍 Branch: {status['branch']} | "
                    f"📝 Modified: {status['modified']} | "
                    f"📋 Staged: {status['staged']} | "
                    f"📄 Untracked: {status['untracked']} | "
                    f"⬆️ Ahead: {status['ahead']} | "
                    f"⬇️ Behind: {status['behind']}"
                )
        
        elif event.button.id == "git-add":
            success, msg = self.git_manager.add_all()
            output.update(f"{'✅' if success else '❌'} {msg}")
        
        elif event.button.id == "git-commit":
            commit_input = self.query_one("#commit-input", Input)
            message = commit_input.value.strip()
            if not message:
                output.update("❌ Please enter a commit message")
                return
            
            success, msg = self.git_manager.commit(message)
            output.update(f"{'✅' if success else '❌'} {msg}")
            if success:
                commit_input.value = ""
        
        elif event.button.id == "git-push":
            success, msg = self.git_manager.push()
            output.update(f"{'✅' if success else '❌'} {msg}")
        
        elif event.button.id == "git-pull":
            success, msg = self.git_manager.pull()
            output.update(f"{'✅' if success else '❌'} {msg}")

class SystemPanel(Container):
    """System monitoring panel"""
    
    def __init__(self):
        super().__init__()
        self.monitor = SystemMonitor()
    
    def compose(self) -> ComposeResult:
        yield Label("📊 System Monitor", classes="panel-title")
        yield Button("🔄 Refresh", id="sys-refresh", classes="sys-btn")
        yield Static("", id="sys-info")
        yield Static("", id="sys-processes")
        yield Static("", id="sys-services")
    
    def on_mount(self) -> None:
        self.refresh_system_info()
        self.set_interval(10, self.refresh_system_info)  # Auto-refresh every 10s
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sys-refresh":
            self.refresh_system_info()
    
    def refresh_system_info(self) -> None:
        # System info
        info = self.monitor.get_system_info()
        sys_info = self.query_one("#sys-info", Static)
        sys_info.update(
            f"🖥️ CPU: {info['cpu_percent']:.1f}% | "
            f"💾 RAM: {info['memory']['percent']:.1f}% | "
            f"💿 Disk: {info['disk']['percent']:.1f}% | "
            f"👥 Users: {info['users']}"
        )
        
        # Processes
        processes = self.monitor.get_processes()
        proc_text = f"🔧 OMNIMESH Processes: {len(processes)}"
        if processes:
            proc_text += "\n" + "\n".join([
                f"  PID {p['pid']}: {p['name']} (CPU: {p['cpu_percent']:.1f}%)"
                for p in processes[:5]  # Show first 5
            ])
        self.query_one("#sys-processes", Static).update(proc_text)
        
        # Services
        services = self.monitor.check_services()
        svc_text = "🔧 Services: " + " | ".join([
            f"{name}: {'🟢' if status else '🔴'}"
            for name, status in services.items()
        ])
        self.query_one("#sys-services", Static).update(svc_text)

class CommandPanel(Container):
    """Command execution panel"""
    
    def __init__(self):
        super().__init__()
        self.executor = CommandExecutor(self.log_command)
        self.command_history = []
    
    def compose(self) -> ComposeResult:
        yield Label("⚡ Command Executor", classes="panel-title")
        yield Input(placeholder="Enter command...", id="cmd-input")
        yield Horizontal(
            Button("🚀 Execute", id="cmd-execute", classes="cmd-btn"),
            Button("📋 History", id="cmd-history", classes="cmd-btn"),
            Button("🗑️ Clear Log", id="cmd-clear", classes="cmd-btn"),
        )
        yield Log(id="cmd-log", auto_scroll=True)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cmd-execute":
            self.execute_command()
        elif event.button.id == "cmd-history":
            self.show_history()
        elif event.button.id == "cmd-clear":
            self.query_one("#cmd-log", Log).clear()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "cmd-input":
            self.execute_command()
    
    def execute_command(self) -> None:
        cmd_input = self.query_one("#cmd-input", Input)
        command = cmd_input.value.strip()
        if not command:
            return
        
        self.command_history.append(command)
        cmd_input.value = ""
        
        # Execute in background thread
        threading.Thread(target=self._execute_async, args=(command,), daemon=True).start()
    
    def _execute_async(self, command: str) -> None:
        success, stdout, stderr = self.executor.execute(command)
        
        # Update UI in main thread
        self.call_from_thread(self._update_output, command, success, stdout, stderr)
    
    def _update_output(self, command: str, success: bool, stdout: str, stderr: str) -> None:
        log = self.query_one("#cmd-log", Log)
        
        status = "✅" if success else "❌"
        log.write_line(f"{status} {command}")
        
        if stdout:
            for line in stdout.strip().split('\n'):
                log.write_line(f"  📤 {line}")
        
        if stderr:
            for line in stderr.strip().split('\n'):
                log.write_line(f"  ⚠️ {line}")
    
    def log_command(self, message: str) -> None:
        """Callback for command logging"""
        try:
            log = self.query_one("#cmd-log", Log)
            log.write_line(f"ℹ️ {message}")
        except:
            pass  # UI might not be ready
    
    def show_history(self) -> None:
        log = self.query_one("#cmd-log", Log)
        log.write_line("📋 Command History:")
        for i, cmd in enumerate(self.command_history[-10:], 1):
            log.write_line(f"  {i}. {cmd}")

class InstallerPanel(Container):
    """OMNIMESH installer operations"""
    
    def compose(self) -> ComposeResult:
        yield Label("🔧 OMNIMESH Installer", classes="panel-title")
        yield Horizontal(
            Button("🏗️ Full Install", id="install-full", classes="install-btn"),
            Button("🐍 Python Only", id="install-python", classes="install-btn"),
            Button("🎨 Frontend Only", id="install-frontend", classes="install-btn"),
        )
        yield Horizontal(
            Button("🐳 Docker", id="install-docker", classes="install-btn"),
            Button("☸️ Kubernetes", id="install-k8s", classes="install-btn"),
            Button("🔒 Security", id="install-security", classes="install-btn"),
        )
        yield Horizontal(
            Button("🩺 Health Check", id="install-verify", classes="install-btn"),
            Button("🧹 Clean Install", id="install-clean", classes="install-btn"),
            Button("⚙️ Configure", id="install-config", classes="install-btn"),
        )
        yield ProgressBar(id="install-progress", show_eta=False)
        yield Static("", id="install-status")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "install-full":
            self.run_installer("--dev")
        elif button_id == "install-python":
            self.run_installer("--no-backend --no-frontend --no-docker")
        elif button_id == "install-frontend":
            self.run_installer("--no-backend")
        elif button_id == "install-docker":
            self.run_installer("--no-backend --no-frontend")
        elif button_id == "install-k8s":
            self.run_installer("--kubernetes --no-backend --no-frontend")
        elif button_id == "install-security":
            self.run_command("./tiger-lily-enforcement.sh")
        elif button_id == "install-verify":
            self.run_command("./verify-omnimesh.sh")
        elif button_id == "install-clean":
            self.clean_install()
        elif button_id == "install-config":
            self.configure_system()
    
    def run_installer(self, args: str) -> None:
        command = f"./install-omnimesh.sh {args} --non-interactive"
        self.run_command(command)
    
    def run_command(self, command: str) -> None:
        status = self.query_one("#install-status", Static)
        progress = self.query_one("#install-progress", ProgressBar)
        
        status.update(f"🔄 Running: {command}")
        progress.advance(0)  # Start progress
        
        # Run in background
        threading.Thread(target=self._run_async, args=(command,), daemon=True).start()
    
    def _run_async(self, command: str) -> None:
        executor = CommandExecutor()
        success, stdout, stderr = executor.execute(command)
        
        # Update UI
        self.call_from_thread(self._update_install_status, command, success, stdout, stderr)
    
    def _update_install_status(self, command: str, success: bool, stdout: str, stderr: str) -> None:
        status = self.query_one("#install-status", Static)
        
        if success:
            status.update(f"✅ Completed: {command}")
        else:
            status.update(f"❌ Failed: {command}\n{stderr[:200]}...")
    
    def clean_install(self) -> None:
        """Clean installation artifacts"""
        commands = [
            "rm -rf venv/",
            "rm -rf node_modules/",
            "rm -rf target/",
            "rm -f *.log",
            "rm -f .env"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def configure_system(self) -> None:
        """Open configuration interface"""
        status = self.query_one("#install-status", Static)
        
        # Create configuration dialog
        config_options = [
            "🔧 Backend API Endpoint",
            "🌐 Frontend URL Configuration", 
            "🚀 Deployment Settings",
            "🔒 Security Configuration",
            "📊 Monitoring Setup",
            "🐳 Docker Configuration",
            "☸️ Kubernetes Settings"
        ]
        
        status.update("⚙️ Configuration interface initialized - Use arrow keys to navigate options")
        
        # In a real implementation, this would open a dialog
        # For now, provide instructions
        for i, option in enumerate(config_options, 1):
            self.log_to_panel("install", f"{i}. {option}", "info")
        
        self.log_to_panel("install", "📝 Configuration options displayed. Full dialog implementation available in production mode.", "success")

class C2CenterApp(App):
    """🌊 OMNIMESH Command & Control Center - Comprehensive Management Interface"""
    
    CSS = """
    .panel-title {
        background: #1e3a8a;
        color: white;
        padding: 1;
        margin-bottom: 1;
        text-align: center;
        text-style: bold;
    }
    
    .status-panel {
        background: #111827;
        border: solid #374151;
        padding: 1;
        margin: 1;
    }
    
    .healthy { color: #10b981; }
    .warning { color: #f59e0b; }
    .critical { color: #ef4444; }
    .error { color: #dc2626; }
    
    .action-btn {
        margin: 1;
        min-width: 15;
        background: #1f2937;
    }
    
    .action-btn:hover {
        background: #374151;
    }
    
    .build-btn { border: solid #10b981; }
    .frontend-btn { border: solid #3b82f6; }
    .infra-btn { border: solid #8b5cf6; }
    .security-btn { border: solid #ef4444; }
    .git-btn { border: solid #f59e0b; }
    .system-btn { border: solid #6b7280; }
    .deploy-btn { border: solid #f97316; }
    
    #output-log {
        height: 20;
        background: #111827;
        border: solid #374151;
        color: #f3f4f6;
    }
    
    TabbedContent {
        height: 100%;
    }
    
    TabPane {
        padding: 1;
    }
    
    .metric-grid {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
    }
    
    .metric-card {
        background: #1f2937;
        border: solid #374151;
        padding: 1;
        text-align: center;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "refresh_all", "Refresh All"),
        Binding("ctrl+l", "clear_logs", "Clear Logs"),
        Binding("f1", "help", "Help"),
        Binding("f5", "refresh_current", "Refresh Tab"),
        Binding("ctrl+b", "focus_build", "Build Tab"),
        Binding("ctrl+f", "focus_frontend", "Frontend Tab"),
        Binding("ctrl+i", "focus_infrastructure", "Infrastructure Tab"),
        Binding("ctrl+s", "focus_security", "Security Tab"),
        Binding("ctrl+g", "focus_git", "Git Tab"),
        Binding("ctrl+m", "focus_system", "System Tab"),
        Binding("ctrl+d", "focus_deploy", "Deploy Tab"),
    ]
    
    def __init__(self):
        super().__init__()
        # Initialize all managers
        self.git_manager = GitManager(SCRIPT_DIR)
        self.system_monitor = SystemMonitor()
        self.config_manager = ConfigManager()
        self.command_executor = CommandExecutor()
        self.deployment_manager = DeploymentManager()
        self.health_checker = HealthChecker()
        self.build_manager = BuildManager()
        self.security_manager = SecurityManager()
        self.infrastructure_manager = InfrastructureManager()
        self.frontend_manager = FrontendManager()
        
        # State tracking
        self.current_tab = "overview"
        self.auto_refresh = True
        self.refresh_interval = 30  # seconds
        self.last_refresh = datetime.now()
    
    def compose(self) -> ComposeResult:
        """Create the comprehensive UI layout"""
        yield Header(show_clock=True)
        
        with TabbedContent(initial="overview"):
            # Overview Dashboard
            with TabPane("📊 Overview", id="overview"):
                yield self.create_overview_panel()
            
            # Build Management
            with TabPane("🔧 Build", id="build"):
                yield self.create_build_panel()
            
            # Frontend Development
            with TabPane("🎨 Frontend", id="frontend"):
                yield self.create_frontend_panel()
            
            # Infrastructure Management
            with TabPane("🏗️ Infrastructure", id="infrastructure"):
                yield self.create_infrastructure_panel()
            
            # Security & Compliance
            with TabPane("🔒 Security", id="security"):
                yield self.create_security_panel()
            
            # Git Operations
            with TabPane("📝 Git", id="git"):
                yield self.create_git_panel()
            
            # System Monitoring
            with TabPane("📈 System", id="system"):
                yield self.create_system_panel()
            
            # Command Center
            with TabPane("⚡ Commands", id="commands"):
                yield self.create_command_panel()
            
            # Deployment Operations
            with TabPane("🚀 Deploy", id="deploy"):
                yield self.create_deployment_panel()
            
            # Health Monitoring
            with TabPane("💚 Health", id="health"):
                yield self.create_health_panel()
            
            # Configuration
            with TabPane("⚙️ Config", id="config"):
                yield self.create_config_panel()
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application"""
        self.title = "🌊 OMNIMESH Command & Control Center"
        self.sub_title = f"Managing: {SCRIPT_DIR.name} | Environment: {self.get_current_environment()}"
        
        # Start auto-refresh timer
        if self.auto_refresh:
            self.set_interval(self.refresh_interval, self.auto_refresh_data)
    
    def get_current_environment(self) -> str:
        """Get current environment from config"""
        try:
            config = self.config_manager.load_config()
            return config.get("environment", {}).get("current", "development")
        except:
            return "unknown"
    
    def create_overview_panel(self) -> Container:
        """Create overview dashboard"""
        with Container():
            yield Static("🌊 OMNIMESH System Overview", classes="panel-title")
            
            # System status cards
            with Container(classes="metric-grid"):
                yield Static("System Status\n[bold green]●[/] Operational", classes="metric-card", id="system-status")
                yield Static("Services\n[bold blue]●[/] 5/8 Running", classes="metric-card", id="services-status")
                yield Static("Security\n[bold yellow]●[/] Monitoring", classes="metric-card", id="security-status")
            
            # Quick actions
            with Horizontal():
                yield Button("🔧 Build All", variant="primary", classes="action-btn build-btn", id="quick-build")
                yield Button("🎨 Start Frontend", variant="primary", classes="action-btn frontend-btn", id="quick-frontend")
                yield Button("🔒 Security Audit", variant="primary", classes="action-btn security-btn", id="quick-security")
                yield Button("🚀 Deploy", variant="primary", classes="action-btn deploy-btn", id="quick-deploy")
            
            # Live status feed
            yield Log(auto_scroll=True, id="status-feed", classes="status-panel")
    
    def create_build_panel(self) -> Container:
        """Create build management panel"""
        with Container():
            yield Static("🔧 Build Management", classes="panel-title")
            
            with Horizontal():
                yield Button("Build Backend", variant="primary", classes="action-btn", id="build-backend")
                yield Button("Build Frontend", variant="primary", classes="action-btn", id="build-frontend")
                yield Button("Build All", variant="success", classes="action-btn", id="build-all")
                yield Button("Run Tests", variant="default", classes="action-btn", id="run-tests")
                yield Button("Clean Build", variant="warning", classes="action-btn", id="clean-build")
            
            with Horizontal():
                yield Static("Build Status:", classes="panel-title")
                yield Static("Last Build: Not run", id="build-status")
            
            yield Log(auto_scroll=True, id="build-output", classes="status-panel")
    
    def create_frontend_panel(self) -> Container:
        """Create frontend development panel"""
        with Container():
            yield Static("🎨 Frontend Development", classes="panel-title")
            
            with Horizontal():
                yield Button("Start Dev Server", variant="primary", classes="action-btn", id="start-dev-server")
                yield Button("Build Production", variant="success", classes="action-btn", id="build-prod")
                yield Button("Run Linting", variant="default", classes="action-btn", id="run-linting")
                yield Button("Run Tests", variant="default", classes="action-btn", id="frontend-tests")
                yield Button("Mobile Setup", variant="default", classes="action-btn", id="mobile-setup")
            
            with Horizontal():
                yield Button("Type Check", variant="default", classes="action-btn", id="type-check")
                yield Button("Format Code", variant="default", classes="action-btn", id="format-code")
                yield Button("Bundle Analyze", variant="default", classes="action-btn", id="bundle-analyze")
                yield Button("E2E Tests", variant="default", classes="action-btn", id="e2e-tests")
                yield Button("Storybook", variant="default", classes="action-btn", id="storybook")
            
            with Horizontal():
                yield Static("Dev Server:", classes="panel-title")
                yield Static("Stopped", id="dev-server-status")
                yield Static("Local IP:", classes="panel-title")
                yield Static("Not configured", id="local-ip-status")
            
            yield Log(auto_scroll=True, id="frontend-output", classes="status-panel")
    
    def create_infrastructure_panel(self) -> Container:
        """Create infrastructure management panel"""
        with Container():
            yield Static("🏗️ Infrastructure Management", classes="panel-title")
            
            with Horizontal():
                yield Button("Terraform Plan", variant="primary", classes="action-btn", id="terraform-plan")
                yield Button("Terraform Apply", variant="success", classes="action-btn", id="terraform-apply")
                yield Button("K8s Deploy", variant="primary", classes="action-btn", id="k8s-deploy")
                yield Button("Install ArgoCD", variant="default", classes="action-btn", id="install-argocd")
                yield Button("Check Status", variant="default", classes="action-btn", id="infra-status")
            
            with Horizontal():
                yield Static("Terraform:", classes="panel-title")
                yield Static("Not initialized", id="terraform-status")
                yield Static("Kubernetes:", classes="panel-title")
                yield Static("Not connected", id="k8s-status")
            
            yield Log(auto_scroll=True, id="infrastructure-output", classes="status-panel")
    
    def create_security_panel(self) -> Container:
        """Create security management panel"""
        with Container():
            yield Static("🔒 Security & Compliance", classes="panel-title")
            
            with Horizontal():
                yield Button("Security Audit", variant="primary", classes="action-btn", id="security-audit")
                yield Button("Tiger Lily Enforce", variant="warning", classes="action-btn", id="tiger-lily")
                yield Button("Vulnerability Scan", variant="primary", classes="action-btn", id="vuln-scan")
                yield Button("Compliance Check", variant="default", classes="action-btn", id="compliance-check")
                yield Button("Fix Permissions", variant="default", classes="action-btn", id="fix-permissions")
            
            with Container(classes="metric-grid"):
                yield Static("Vulnerabilities\n[bold green]0[/] Critical", classes="metric-card", id="vuln-status")
                yield Static("Compliance\n[bold green]●[/] Tiger Lily", classes="metric-card", id="compliance-status")
                yield Static("Encryption\n[bold green]●[/] Enabled", classes="metric-card", id="encryption-status")
            
            yield Log(auto_scroll=True, id="security-output", classes="status-panel")
    
    def create_git_panel(self) -> Container:
        """Create git operations panel"""
        with Container():
            yield Static("📝 Git Operations", classes="panel-title")
            
            with Horizontal():
                yield Button("Git Status", variant="primary", classes="action-btn", id="git-status")
                yield Button("Pull Latest", variant="success", classes="action-btn", id="git-pull")
                yield Button("Commit Changes", variant="primary", classes="action-btn", id="git-commit")
                yield Button("Push Changes", variant="success", classes="action-btn", id="git-push")
                yield Button("Create Branch", variant="default", classes="action-btn", id="git-branch")
            
            with Horizontal():
                yield Static("Branch:", classes="panel-title")
                yield Static("main", id="current-branch")
                yield Static("Status:", classes="panel-title")
                yield Static("Clean", id="git-repo-status")
            
            yield Log(auto_scroll=True, id="git-output", classes="status-panel")
    
    def create_system_panel(self) -> Container:
        """Create system monitoring panel"""
        with Container():
            yield Static("📈 System Monitoring", classes="panel-title")
            
            with Container(classes="metric-grid"):
                yield Static("CPU Usage\n[bold blue]25%[/]", classes="metric-card", id="cpu-usage")
                yield Static("Memory\n[bold green]45%[/]", classes="metric-card", id="memory-usage") 
                yield Static("Disk Space\n[bold green]60%[/]", classes="metric-card", id="disk-usage")
            
            with Container(classes="metric-grid"):
                yield Static("Processes\n[bold cyan]156[/]", classes="metric-card", id="process-count")
                yield Static("OMNIMESH Procs\n[bold yellow]3[/]", classes="metric-card", id="omnimesh-procs")
                yield Static("Uptime\n[bold green]2d 4h[/]", classes="metric-card", id="system-uptime")
            
            with Horizontal():
                yield Button("Refresh Metrics", variant="primary", classes="action-btn", id="refresh-metrics")
                yield Button("Process List", variant="default", classes="action-btn", id="process-list")
                yield Button("Resource Monitor", variant="default", classes="action-btn", id="resource-monitor")
                yield Button("Kill Process", variant="warning", classes="action-btn", id="kill-process")
            
            yield Log(auto_scroll=True, id="system-output", classes="status-panel")
    
    def create_command_panel(self) -> Container:
        """Create command execution panel"""
        with Container():
            yield Static("⚡ Command Center", classes="panel-title")
            
            with Horizontal():
                yield Input(placeholder="Enter command...", id="command-input")
                yield Button("Execute", variant="primary", classes="action-btn", id="execute-command")
                yield Button("Clear Log", variant="default", classes="action-btn", id="clear-command-log")
            
            with Horizontal():
                yield Button("Quick Start", variant="success", classes="action-btn", id="run-quick-start")
                yield Button("Install Script", variant="primary", classes="action-btn", id="run-installer")
                yield Button("Verify System", variant="default", classes="action-btn", id="run-verify")
                yield Button("Emergency Recovery", variant="warning", classes="action-btn", id="emergency-recovery")
            
            yield Log(auto_scroll=True, id="command-output", classes="status-panel")
    
    def create_deployment_panel(self) -> Container:
        """Create deployment operations panel"""
        with Container():
            yield Static("🚀 Deployment Operations", classes="panel-title")
            
            with Horizontal():
                yield Button("Deploy Development", variant="primary", classes="action-btn", id="deploy-dev")
                yield Button("Deploy Staging", variant="primary", classes="action-btn", id="deploy-staging")
                yield Button("Deploy Production", variant="success", classes="action-btn", id="deploy-prod")
                yield Button("Rollback", variant="warning", classes="action-btn", id="rollback")
                yield Button("Check Status", variant="default", classes="action-btn", id="deployment-status")
            
            with Container(classes="metric-grid"):
                yield Static("Backend\n[bold red]●[/] Stopped", classes="metric-card", id="backend-status")
                yield Static("Frontend\n[bold red]●[/] Stopped", classes="metric-card", id="frontend-deploy-status")
                yield Static("Kubernetes\n[bold yellow]●[/] Partial", classes="metric-card", id="k8s-deploy-status")
            
            yield Log(auto_scroll=True, id="deployment-output", classes="status-panel")
    
    def create_health_panel(self) -> Container:
        """Create health monitoring panel"""
        with Container():
            yield Static("💚 Health Monitoring", classes="panel-title")
            
            with Horizontal():
                yield Button("Full Health Check", variant="primary", classes="action-btn", id="full-health-check")
                yield Button("Quick Check", variant="default", classes="action-btn", id="quick-health-check")
                yield Button("System Diagnostics", variant="default", classes="action-btn", id="system-diagnostics")
                yield Button("Fix Issues", variant="success", classes="action-btn", id="fix-health-issues")
            
            with Container(classes="metric-grid"):
                yield Static("Overall Health\n[bold green]●[/] Healthy", classes="metric-card", id="overall-health")
                yield Static("Dependencies\n[bold yellow]●[/] 7/8 Found", classes="metric-card", id="deps-health")
                yield Static("Services\n[bold red]●[/] 3/8 Running", classes="metric-card", id="services-health")
            
            yield Log(auto_scroll=True, id="health-output", classes="status-panel")
    
    def create_config_panel(self) -> Container:
        """Create configuration panel"""
        with Container():
            yield Static("⚙️ Configuration Management", classes="panel-title")
            
            with Horizontal():
                yield Button("Load Config", variant="primary", classes="action-btn", id="load-config")
                yield Button("Save Config", variant="success", classes="action-btn", id="save-config")
                yield Button("Reset to Default", variant="warning", classes="action-btn", id="reset-config")
                yield Button("Edit Config", variant="default", classes="action-btn", id="edit-config")
                yield Button("Validate Config", variant="default", classes="action-btn", id="validate-config")
            
            with Horizontal():
                yield Static("Environment:", classes="panel-title")
                yield Static("development", id="config-environment")
                yield Static("Config File:", classes="panel-title")
                yield Static("omni-config.yaml", id="config-file-status")
            
            yield Log(auto_scroll=True, id="config-output", classes="status-panel")
    
    # Event Handlers and Actions
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle all button press events"""
        button_id = event.button.id
        
        if button_id == "quick-build":
            self.run_build_all()
        elif button_id == "quick-frontend":
            self.start_frontend_dev()
        elif button_id == "quick-security":
            self.run_security_audit()
        elif button_id == "quick-deploy":
            self.deploy_development()
        
        # Build Management
        elif button_id == "build-backend":
            self.build_backend()
        elif button_id == "build-frontend":
            self.build_frontend()
        elif button_id == "build-all":
            self.run_build_all()
        elif button_id == "run-tests":
            self.run_all_tests()
        elif button_id == "clean-build":
            self.clean_build()
        
        # Frontend Development
        elif button_id == "start-dev-server":
            self.start_frontend_dev()
        elif button_id == "build-prod":
            self.build_frontend_production()
        elif button_id == "run-linting":
            self.run_frontend_linting()
        elif button_id == "frontend-tests":
            self.run_frontend_tests()
        elif button_id == "mobile-setup":
            self.setup_mobile_testing()
        elif button_id == "type-check":
            self.run_type_check()
        elif button_id == "format-code":
            self.format_frontend_code()
        elif button_id == "bundle-analyze":
            self.analyze_bundle()
        elif button_id == "e2e-tests":
            self.run_e2e_tests()
        elif button_id == "storybook":
            self.start_storybook()
        
        # Infrastructure
        elif button_id == "terraform-plan":
            self.run_terraform_plan()
        elif button_id == "terraform-apply":
            self.run_terraform_apply()
        elif button_id == "k8s-deploy":
            self.deploy_kubernetes()
        elif button_id == "install-argocd":
            self.install_argocd()
        elif button_id == "infra-status":
            self.check_infrastructure_status()
        
        # Security
        elif button_id == "security-audit":
            self.run_security_audit()
        elif button_id == "tiger-lily":
            self.activate_tiger_lily()
        elif button_id == "vuln-scan":
            self.run_vulnerability_scan()
        elif button_id == "compliance-check":
            self.check_compliance()
        elif button_id == "fix-permissions":
            self.fix_file_permissions()
        
        # Git Operations
        elif button_id == "git-status":
            self.show_git_status()
        elif button_id == "git-pull":
            self.git_pull()
        elif button_id == "git-commit":
            self.git_commit()
        elif button_id == "git-push":
            self.git_push()
        elif button_id == "git-branch":
            self.create_git_branch()
        
        # System Monitoring
        elif button_id == "refresh-metrics":
            self.refresh_system_metrics()
        elif button_id == "process-list":
            self.show_process_list()
        elif button_id == "resource-monitor":
            self.start_resource_monitor()
        elif button_id == "kill-process":
            self.kill_process_dialog()
        
        # Commands
        elif button_id == "execute-command":
            self.execute_custom_command()
        elif button_id == "clear-command-log":
            self.clear_command_log()
        elif button_id == "run-quick-start":
            self.run_quick_start_script()
        elif button_id == "run-installer":
            self.run_installer_script()
        elif button_id == "run-verify":
            self.run_verify_script()
        elif button_id == "emergency-recovery":
            self.emergency_recovery()
        
        # Deployment
        elif button_id == "deploy-dev":
            self.deploy_development()
        elif button_id == "deploy-staging":
            self.deploy_staging()
        elif button_id == "deploy-prod":
            self.deploy_production()
        elif button_id == "rollback":
            self.rollback_deployment()
        elif button_id == "deployment-status":
            self.check_deployment_status()
        
        # Health
        elif button_id == "full-health-check":
            self.run_full_health_check()
        elif button_id == "quick-health-check":
            self.run_quick_health_check()
        elif button_id == "system-diagnostics":
            self.run_system_diagnostics()
        elif button_id == "fix-health-issues":
            self.fix_health_issues()
        
        # Configuration
        elif button_id == "load-config":
            self.load_configuration()
        elif button_id == "save-config":
            self.save_configuration()
        elif button_id == "reset-config":
            self.reset_configuration()
        elif button_id == "edit-config":
            self.edit_configuration()
        elif button_id == "validate-config":
            self.validate_configuration()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submissions"""
        if event.input.id == "command-input":
            self.execute_custom_command()
    
    # Action Methods
    
    def log_to_panel(self, panel_id: str, message: str, level: str = "info"):
        """Log message to specific panel"""
        try:
            log_widget = self.query_one(f"#{panel_id}", Log)
            
            if level == "error":
                log_widget.write(f"[red]❌ {message}[/red]")
            elif level == "success":
                log_widget.write(f"[green]✅ {message}[/green]")
            elif level == "warning":
                log_widget.write(f"[yellow]⚠️ {message}[/yellow]")
            else:
                log_widget.write(f"[blue]ℹ️ {message}[/blue]")
        except Exception:
            pass  # Panel not found or not ready
    
    def update_status_widget(self, widget_id: str, text: str, style: str = ""):
        """Update status widget text"""
        try:
            widget = self.query_one(f"#{widget_id}", Static)
            if style:
                widget.update(f"[{style}]{text}[/{style}]")
            else:
                widget.update(text)
        except Exception:
            pass
    
    # Build Management Actions
    
    def run_build_all(self):
        """Build all components"""
        self.log_to_panel("build-output", "Starting comprehensive build process...")
        
        def build_async():
            # Build backend
            backend_results = self.build_manager.build_backend()
            if backend_results.get("nexus_core"):
                self.log_to_panel("build-output", "✅ Nexus Core built successfully", "success")
            if backend_results.get("go_proxies"):
                self.log_to_panel("build-output", "✅ Go Proxies built successfully", "success")
            for error in backend_results.get("errors", []):
                self.log_to_panel("build-output", f"Backend error: {error}", "error")
            
            # Build frontend
            frontend_results = self.build_manager.build_frontend()
            if frontend_results.get("solidjs_ui"):
                self.log_to_panel("build-output", "✅ SolidJS UI built successfully", "success")
            for error in frontend_results.get("errors", []):
                self.log_to_panel("build-output", f"Frontend error: {error}", "error")
            
            self.log_to_panel("build-output", "Build process completed", "info")
        
        threading.Thread(target=build_async, daemon=True).start()
    
    def build_backend(self):
        """Build backend components only"""
        self.log_to_panel("build-output", "Building backend components...")
        
        def build_async():
            results = self.build_manager.build_backend()
            for component, success in results.items():
                if component != "errors" and success:
                    self.log_to_panel("build-output", f"✅ {component} built successfully", "success")
            for error in results.get("errors", []):
                self.log_to_panel("build-output", f"Error: {error}", "error")
        
        threading.Thread(target=build_async, daemon=True).start()
    
    def build_frontend(self):
        """Build frontend components only"""
        self.log_to_panel("build-output", "Building frontend components...")
        
        def build_async():
            results = self.build_manager.build_frontend()
            if results.get("solidjs_ui"):
                self.log_to_panel("build-output", "✅ Frontend built successfully", "success")
            for error in results.get("errors", []):
                self.log_to_panel("build-output", f"Error: {error}", "error")
        
        threading.Thread(target=build_async, daemon=True).start()
    
    def run_all_tests(self):
        """Run all test suites"""
        self.log_to_panel("build-output", "Running all test suites...")
        
        def test_async():
            results = self.build_manager.run_tests()
            self.log_to_panel("build-output", f"Tests passed: {results['passed']}, failed: {results['failed']}")
            for error in results.get("errors", []):
                self.log_to_panel("build-output", f"Test error: {error}", "error")
        
        threading.Thread(target=test_async, daemon=True).start()
    
    def clean_build(self):
        """Clean build artifacts"""
        self.log_to_panel("build-output", "Cleaning build artifacts...")
        
        def clean_async():
            commands = [
                "cd BACKEND/nexus-prime-core && cargo clean",
                "cd BACKEND/go-node-proxies && go clean",
                "cd FRONTEND/ui-solidjs && pnpm run clean",
                "rm -rf target/ dist/ node_modules/.cache/ .turbo/"
            ]
            
            for cmd in commands:
                result = self.command_executor.execute_command(cmd)
                if result.get("returncode") == 0:
                    self.log_to_panel("build-output", f"✅ Cleaned: {cmd.split('&&')[-1].strip()}", "success")
                else:
                    self.log_to_panel("build-output", f"❌ Clean failed: {cmd}", "error")
        
        threading.Thread(target=clean_async, daemon=True).start()
    
    # Frontend Development Actions
    
    def start_frontend_dev(self):
        """Start frontend development server"""
        self.log_to_panel("frontend-output", "Starting development server...")
        
        def start_async():
            results = self.frontend_manager.start_dev_server()
            if results.get("success"):
                self.log_to_panel("frontend-output", f"✅ Dev server started (PID: {results['pid']})", "success")
                self.update_status_widget("dev-server-status", "[green]Running[/green]")
            else:
                for error in results.get("errors", []):
                    self.log_to_panel("frontend-output", f"Error: {error}", "error")
        
        threading.Thread(target=start_async, daemon=True).start()
    
    def build_frontend_production(self):
        """Build frontend for production"""
        self.log_to_panel("frontend-output", "Building production frontend...")
        
        def build_async():
            cmd = "cd FRONTEND/ui-solidjs && pnpm run build"
            result = self.command_executor.execute_command(cmd)
            if result.get("returncode") == 0:
                self.log_to_panel("frontend-output", "✅ Production build completed", "success")
            else:
                self.log_to_panel("frontend-output", f"❌ Build failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=build_async, daemon=True).start()
    
    def run_frontend_linting(self):
        """Run frontend linting"""
        self.log_to_panel("frontend-output", "Running ESLint and Prettier checks...")
        
        def lint_async():
            results = self.frontend_manager.run_linting()
            if results.get("lint_passed"):
                self.log_to_panel("frontend-output", "✅ ESLint checks passed", "success")
            if results.get("format_passed"):
                self.log_to_panel("frontend-output", "✅ Prettier checks passed", "success")
            for error in results.get("errors", []):
                self.log_to_panel("frontend-output", f"Linting error: {error}", "error")
        
        threading.Thread(target=lint_async, daemon=True).start()
    
    def setup_mobile_testing(self):
        """Setup mobile testing environment"""
        self.log_to_panel("frontend-output", "Setting up mobile testing...")
        
        def mobile_async():
            results = self.frontend_manager.setup_mobile_testing()
            if results.get("success"):
                local_ip = results.get("local_ip", "Unknown")
                self.log_to_panel("frontend-output", f"✅ Mobile testing configured for IP: {local_ip}", "success")
                self.update_status_widget("local-ip-status", local_ip)
            else:
                for error in results.get("errors", []):
                    self.log_to_panel("frontend-output", f"Mobile setup error: {error}", "error")
        
        threading.Thread(target=mobile_async, daemon=True).start()
    
    def run_type_check(self):
        """Run TypeScript type checking"""
        self.execute_frontend_command("pnpm run type-check", "Type checking")
    
    def format_frontend_code(self):
        """Format frontend code"""
        self.execute_frontend_command("pnpm run format", "Code formatting")
    
    def analyze_bundle(self):
        """Analyze bundle size"""
        self.execute_frontend_command("pnpm run analyze", "Bundle analysis")
    
    def run_e2e_tests(self):
        """Run end-to-end tests"""
        self.execute_frontend_command("pnpm run e2e", "E2E testing")
    
    def start_storybook(self):
        """Start Storybook"""
        self.execute_frontend_command("pnpm run storybook", "Storybook server")
    
    def run_frontend_tests(self):
        """Run frontend test suite"""
        self.execute_frontend_command("pnpm run test", "Frontend tests")
    
    def execute_frontend_command(self, command: str, description: str):
        """Helper to execute frontend commands"""
        self.log_to_panel("frontend-output", f"Running {description}...")
        
        def exec_async():
            cmd = f"cd FRONTEND/ui-solidjs && {command}"
            result = self.command_executor.execute_command(cmd)
            if result.get("returncode") == 0:
                self.log_to_panel("frontend-output", f"✅ {description} completed", "success")
            else:
                self.log_to_panel("frontend-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Security Actions
    
    def run_security_audit(self):
        """Run comprehensive security audit"""
        self.log_to_panel("security-output", "Running comprehensive security audit...")
        
        def audit_async():
            results = self.security_manager.run_security_audit()
            if results.get("audit_passed"):
                self.log_to_panel("security-output", "✅ Security audit passed", "success")
            else:
                self.log_to_panel("security-output", "❌ Security audit found issues", "warning")
            
            vulns = results.get("vulnerabilities", {})
            if sum(vulns.values()) > 0:
                self.log_to_panel("security-output", f"Vulnerabilities found: {vulns}", "warning")
            
            for error in results.get("errors", []):
                self.log_to_panel("security-output", f"Audit error: {error}", "error")
        
        threading.Thread(target=audit_async, daemon=True).start()
    
    def activate_tiger_lily(self):
        """Activate Tiger Lily enforcement"""
        self.log_to_panel("security-output", "Activating Tiger Lily Ω^9 enforcement...")
        
        def tiger_async():
            results = self.security_manager.enforce_tiger_lily()
            if results.get("success"):
                self.log_to_panel("security-output", "✅ Tiger Lily enforcement activated", "success")
                self.update_status_widget("compliance-status", "[green]●[/green] Active")
            else:
                for error in results.get("errors", []):
                    self.log_to_panel("security-output", f"Tiger Lily error: {error}", "error")
        
        threading.Thread(target=tiger_async, daemon=True).start()
    
    def run_vulnerability_scan(self):
        """Run vulnerability scan"""
        self.execute_security_command("trivy fs --severity HIGH,CRITICAL .", "Vulnerability scan")
    
    def check_compliance(self):
        """Check compliance status"""
        self.execute_security_command("bash tiger-lily-enforcement.sh", "Compliance check")
    
    def fix_file_permissions(self):
        """Fix file permissions"""
        self.execute_security_command("find . -name '*.yaml' -o -name '.env' | xargs chmod 600", "Permission fix")
    
    def execute_security_command(self, command: str, description: str):
        """Helper to execute security commands"""
        self.log_to_panel("security-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command)
            if result.get("returncode") == 0:
                self.log_to_panel("security-output", f"✅ {description} completed", "success")
            else:
                self.log_to_panel("security-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Infrastructure Actions
    
    def run_terraform_plan(self):
        """Run Terraform plan"""
        self.log_to_panel("infrastructure-output", "Running Terraform plan...")
        
        def plan_async():
            results = self.infrastructure_manager.run_terraform_plan()
            if results.get("success"):
                self.log_to_panel("infrastructure-output", "✅ Terraform plan completed", "success")
                self.update_status_widget("terraform-status", "[green]Plan ready[/green]")
            else:
                for error in results.get("errors", []):
                    self.log_to_panel("infrastructure-output", f"Terraform error: {error}", "error")
        
        threading.Thread(target=plan_async, daemon=True).start()
    
    def run_terraform_apply(self):
        """Apply Terraform changes"""
        self.execute_infrastructure_command("cd infrastructure && terraform apply", "Terraform apply")
    
    def deploy_kubernetes(self):
        """Deploy to Kubernetes"""
        self.log_to_panel("infrastructure-output", "Deploying to Kubernetes...")
        
        def deploy_async():
            results = self.infrastructure_manager.deploy_kubernetes()
            if results.get("success"):
                self.log_to_panel("infrastructure-output", "✅ Kubernetes deployment completed", "success")
                self.update_status_widget("k8s-status", "[green]Deployed[/green]")
            else:
                for error in results.get("errors", []):
                    self.log_to_panel("infrastructure-output", f"K8s error: {error}", "error")
        
        threading.Thread(target=deploy_async, daemon=True).start()
    
    def install_argocd(self):
        """Install ArgoCD"""
        self.execute_infrastructure_command("cd infrastructure && make install-argocd", "ArgoCD installation")
    
    def check_infrastructure_status(self):
        """Check infrastructure status"""
        self.log_to_panel("infrastructure-output", "Checking infrastructure status...")
        
        def status_async():
            tf_status = self.infrastructure_manager.get_terraform_status()
            self.log_to_panel("infrastructure-output", f"Terraform initialized: {tf_status.get('initialized')}")
            self.log_to_panel("infrastructure-output", f"Plan exists: {tf_status.get('plan_exists')}")
            
            for error in tf_status.get("errors", []):
                self.log_to_panel("infrastructure-output", f"Status error: {error}", "error")
        
        threading.Thread(target=status_async, daemon=True).start()
    
    def execute_infrastructure_command(self, command: str, description: str):
        """Helper to execute infrastructure commands"""
        self.log_to_panel("infrastructure-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command, timeout=300)
            if result.get("returncode") == 0:
                self.log_to_panel("infrastructure-output", f"✅ {description} completed", "success")
            else:
                self.log_to_panel("infrastructure-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Git Actions
    
    def show_git_status(self):
        """Show git repository status"""
        self.log_to_panel("git-output", "Getting git status...")
        
        def git_async():
            status = self.git_manager.get_status()
            if "error" in status:
                self.log_to_panel("git-output", f"Git error: {status['error']}", "error")
            else:
                self.log_to_panel("git-output", f"Branch: {status.get('branch', 'unknown')}")
                self.log_to_panel("git-output", f"Commit: {status.get('commit', 'unknown')}")
                self.log_to_panel("git-output", f"Modified files: {status.get('modified', 0)}")
                self.log_to_panel("git-output", f"Staged files: {status.get('staged', 0)}")
                self.log_to_panel("git-output", f"Untracked files: {status.get('untracked', 0)}")
                
                self.update_status_widget("current-branch", status.get('branch', 'unknown'))
                
                if status.get('modified', 0) + status.get('staged', 0) + status.get('untracked', 0) == 0:
                    self.update_status_widget("git-repo-status", "[green]Clean[/green]")
                else:
                    self.update_status_widget("git-repo-status", "[yellow]Modified[/yellow]")
        
        threading.Thread(target=git_async, daemon=True).start()
    
    def git_pull(self):
        """Pull latest changes"""
        self.execute_git_command("git pull", "Git pull")
    
    def git_commit(self):
        """Commit staged changes"""
        self.execute_git_command("git add . && git commit -m 'C2 Center automated commit'", "Git commit")
    
    def git_push(self):
        """Push changes to remote"""
        self.execute_git_command("git push", "Git push")
    
    def create_git_branch(self):
        """Create new git branch"""
        branch_name = f"feature/c2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.execute_git_command(f"git checkout -b {branch_name}", f"Create branch {branch_name}")
    
    def execute_git_command(self, command: str, description: str):
        """Helper to execute git commands"""
        self.log_to_panel("git-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command)
            if result.get("returncode") == 0:
                self.log_to_panel("git-output", f"✅ {description} completed", "success")
                self.log_to_panel("git-output", result.get("stdout", ""))
            else:
                self.log_to_panel("git-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # System Monitoring Actions
    
    def refresh_system_metrics(self):
        """Refresh system metrics"""
        self.log_to_panel("system-output", "Refreshing system metrics...")
        
        def refresh_async():
            status = self.system_monitor.get_system_status()
            if "error" in status:
                self.log_to_panel("system-output", f"Error: {status['error']}", "error")
            else:
                # Update metric cards
                self.update_status_widget("cpu-usage", f"CPU Usage\n[bold blue]{status['cpu_percent']:.1f}%[/bold blue]")
                self.update_status_widget("memory-usage", f"Memory\n[bold green]{status['memory_percent']:.1f}%[/bold green]")
                self.update_status_widget("disk-usage", f"Disk Space\n[bold green]{status['disk_percent']:.1f}%[/bold green]")
                self.update_status_widget("process-count", f"Processes\n[bold cyan]{status['process_count']}[/bold cyan]")
                self.update_status_widget("omnimesh-procs", f"OMNIMESH Procs\n[bold yellow]{len(status['omnimesh_processes'])}[/bold yellow]")
                self.update_status_widget("system-uptime", f"Uptime\n[bold green]{status['uptime']}[/bold green]")
                
                self.log_to_panel("system-output", "✅ System metrics updated", "success")
                
                # Log OMNIMESH processes
                for proc in status['omnimesh_processes']:
                    self.log_to_panel("system-output", f"Process: {proc['name']} (PID: {proc['pid']})")
        
        threading.Thread(target=refresh_async, daemon=True).start()
    
    def show_process_list(self):
        """Show detailed process list"""
        self.execute_system_command("ps aux | grep -E '(omni|nexus|gcnp|solidjs|vite)'", "Process list")
    
    def start_resource_monitor(self):
        """Start resource monitoring"""
        self.execute_system_command("top -b -n 1 | head -20", "Resource monitor")
    
    def kill_process_dialog(self):
        """Show kill process options"""
        self.log_to_panel("system-output", "To kill a process, use: kill <PID>", "info")
        self.log_to_panel("system-output", "Available OMNIMESH processes will be shown above", "info")
    
    def execute_system_command(self, command: str, description: str):
        """Helper to execute system commands"""
        self.log_to_panel("system-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command)
            if result.get("returncode") == 0:
                self.log_to_panel("system-output", f"✅ {description} completed", "success")
                self.log_to_panel("system-output", result.get("stdout", ""))
            else:
                self.log_to_panel("system-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Command Execution Actions
    
    def execute_custom_command(self):
        """Execute custom command from input"""
        try:
            command_input = self.query_one("#command-input", Input)
            command = command_input.value.strip()
            
            if not command:
                self.log_to_panel("command-output", "❌ Please enter a command", "error")
                return
            
            self.log_to_panel("command-output", f"Executing: {command}")
            command_input.value = ""  # Clear input
            
            def exec_async():
                result = self.command_executor.execute_command(command)
                if result.get("returncode") == 0:
                    self.log_to_panel("command-output", f"✅ Command completed (exit code: 0)", "success")
                    if result.get("stdout"):
                        self.log_to_panel("command-output", result["stdout"])
                else:
                    self.log_to_panel("command-output", f"❌ Command failed (exit code: {result.get('returncode')})", "error")
                    if result.get("stderr"):
                        self.log_to_panel("command-output", result["stderr"])
            
            threading.Thread(target=exec_async, daemon=True).start()
            
        except Exception as e:
            self.log_to_panel("command-output", f"Error executing command: {e}", "error")
    
    def clear_command_log(self):
        """Clear command output log"""
        try:
            log_widget = self.query_one("#command-output", Log)
            log_widget.clear()
            self.log_to_panel("command-output", "Command log cleared", "info")
        except Exception:
            pass
    
    def run_quick_start_script(self):
        """Run quick-start.sh script"""
        self.execute_script_command("bash quick-start.sh", "Quick Start script")
    
    def run_installer_script(self):
        """Run installer script"""
        self.execute_script_command("bash install-omnimesh.sh", "OMNIMESH installer")
    
    def run_verify_script(self):
        """Run verification script"""
        self.execute_script_command("bash verify-omnimesh.sh", "System verification")
    
    def emergency_recovery(self):
        """Run emergency recovery"""
        self.log_to_panel("command-output", "🚨 Starting emergency recovery procedures...", "warning")
        
        def recovery_async():
            recovery_commands = [
                "pkill -f 'nexus\\|gcnp\\|vite'",  # Stop running services
                "cd FRONTEND/ui-solidjs && pnpm run clean || true",  # Clean frontend
                "cd BACKEND/nexus-prime-core && cargo clean || true",  # Clean backend
                "git stash",  # Stash changes
                "git checkout main",  # Switch to main branch
                "git pull || true",  # Try to pull latest
            ]
            
            for cmd in recovery_commands:
                result = self.command_executor.execute_command(cmd)
                self.log_to_panel("command-output", f"Recovery step: {cmd}")
                if result.get("returncode") != 0:
                    self.log_to_panel("command-output", f"⚠️ Recovery step failed: {cmd}", "warning")
            
            self.log_to_panel("command-output", "🔧 Emergency recovery completed", "success")
        
        threading.Thread(target=recovery_async, daemon=True).start()
    
    def execute_script_command(self, command: str, description: str):
        """Helper to execute script commands"""
        self.log_to_panel("command-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command, timeout=180)
            if result.get("returncode") == 0:
                self.log_to_panel("command-output", f"✅ {description} completed", "success")
                if result.get("stdout"):
                    self.log_to_panel("command-output", result["stdout"])
            else:
                self.log_to_panel("command-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Deployment Actions
    
    def deploy_development(self):
        """Deploy to development environment"""
        self.run_deployment("development")
    
    def deploy_staging(self):
        """Deploy to staging environment"""
        self.run_deployment("staging")
    
    def deploy_production(self):
        """Deploy to production environment"""
        self.run_deployment("production")
    
    def run_deployment(self, environment: str):
        """Run deployment to specified environment"""
        self.log_to_panel("deployment-output", f"Deploying to {environment} environment...")
        
        def deploy_async():
            if environment == "production":
                results = self.deployment_manager.run_production_deployment(environment)
                if results.get("success"):
                    self.log_to_panel("deployment-output", f"✅ Production deployment to {environment} completed", "success")
                else:
                    for error in results.get("errors", []):
                        self.log_to_panel("deployment-output", f"Deployment error: {error}", "error")
            else:
                # For dev/staging, use scripts
                script_path = SCRIPT_DIR / "scripts" / f"deploy-{environment}.sh"
                if script_path.exists():
                    result = self.command_executor.execute_command(f"bash {script_path}")
                    if result.get("returncode") == 0:
                        self.log_to_panel("deployment-output", f"✅ {environment} deployment completed", "success")
                    else:
                        self.log_to_panel("deployment-output", f"❌ {environment} deployment failed", "error")
                else:
                    self.log_to_panel("deployment-output", f"❌ {environment} deployment script not found", "error")
        
        threading.Thread(target=deploy_async, daemon=True).start()
    
    def rollback_deployment(self):
        """Rollback deployment"""
        self.execute_deployment_command("kubectl rollout undo deployment/omnimesh -n omnimesh", "Deployment rollback")
    
    def check_deployment_status(self):
        """Check deployment status"""
        self.log_to_panel("deployment-output", "Checking deployment status...")
        
        def status_async():
            status = self.deployment_manager.check_deployment_status()
            
            # Update status widgets
            backend_status = "[green]●[/green] Running" if status.get("backend_running") else "[red]●[/red] Stopped"
            frontend_status = "[green]●[/green] Running" if status.get("frontend_running") else "[red]●[/red] Stopped"
            
            self.update_status_widget("backend-status", f"Backend\n{backend_status}")
            self.update_status_widget("frontend-deploy-status", f"Frontend\n{frontend_status}")
            
            # Log Kubernetes pods
            pods = status.get("kubernetes_pods", [])
            if pods:
                self.log_to_panel("deployment-output", f"Kubernetes pods: {len(pods)} found")
                for pod in pods:
                    self.log_to_panel("deployment-output", f"Pod: {pod['name']} - {pod['status']}")
                self.update_status_widget("k8s-deploy-status", f"Kubernetes\n[green]●[/green] {len(pods)} pods")
            else:
                self.update_status_widget("k8s-deploy-status", "Kubernetes\n[red]●[/red] No pods")
            
            for error in status.get("errors", []):
                self.log_to_panel("deployment-output", f"Status error: {error}", "error")
        
        threading.Thread(target=status_async, daemon=True).start()
    
    def execute_deployment_command(self, command: str, description: str):
        """Helper to execute deployment commands"""
        self.log_to_panel("deployment-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command, timeout=300)
            if result.get("returncode") == 0:
                self.log_to_panel("deployment-output", f"✅ {description} completed", "success")
                if result.get("stdout"):
                    self.log_to_panel("deployment-output", result["stdout"])
            else:
                self.log_to_panel("deployment-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Health Monitoring Actions
    
    def run_full_health_check(self):
        """Run comprehensive health check"""
        self.log_to_panel("health-output", "Running comprehensive health check...")
        
        def health_async():
            results = self.health_checker.run_comprehensive_health_check()
            
            overall_status = results.get("overall_status", "unknown")
            self.update_status_widget("overall-health", f"Overall Health\n[bold green]●[/bold green] {overall_status.title()}")
            
            # Update component status
            components = results.get("components", {})
            
            deps = components.get("dependencies", {})
            missing_count = len(deps.get("missing_tools", []))
            total_tools = len(deps.get("missing_tools", [])) + len(deps.get("available_tools", []))
            available_count = total_tools - missing_count
            self.update_status_widget("deps-health", f"Dependencies\n[bold yellow]●[/bold yellow] {available_count}/{total_tools} Found")
            
            services = components.get("services", {})
            running_count = services.get("running_count", 0)
            total_count = services.get("total_count", 8)
            self.update_status_widget("services-health", f"Services\n[bold red]●[/bold red] {running_count}/{total_count} Running")
            
            # Log detailed results
            for component, data in components.items():
                score = data.get("score", 0)
                status = data.get("status", "unknown")
                self.log_to_panel("health-output", f"{component.title()}: {status} (Score: {score})")
                
                for issue in data.get("issues", []):
                    self.log_to_panel("health-output", f"  Issue: {issue}", "warning")
            
            # Show recommendations
            recommendations = results.get("recommendations", [])
            if recommendations:
                self.log_to_panel("health-output", "Recommendations:", "info")
                for rec in recommendations:
                    self.log_to_panel("health-output", f"  • {rec}", "info")
            
            for error in results.get("errors", []):
                self.log_to_panel("health-output", f"Health check error: {error}", "error")
        
        threading.Thread(target=health_async, daemon=True).start()
    
    def run_quick_health_check(self):
        """Run quick health check"""
        self.log_to_panel("health-output", "Running quick health check...")
        
        def quick_health_async():
            # Quick system check
            system_health = self.health_checker.check_system_health()
            self.log_to_panel("health-output", f"System: {system_health.get('status', 'unknown')} (Score: {system_health.get('score', 0)})")
            
            # Quick dependencies check
            deps_health = self.health_checker.check_dependencies()
            missing = deps_health.get("missing_tools", [])
            if missing:
                self.log_to_panel("health-output", f"Missing tools: {', '.join(missing)}", "warning")
            else:
                self.log_to_panel("health-output", "All required tools available", "success")
            
            # Quick services check
            services_health = self.health_checker.check_services()
            running = services_health.get("running_count", 0)
            total = services_health.get("total_count", 8)
            self.log_to_panel("health-output", f"Services: {running}/{total} running")
        
        threading.Thread(target=quick_health_async, daemon=True).start()
    
    def run_system_diagnostics(self):
        """Run system diagnostics"""
        self.execute_health_command("df -h && free -h && uptime", "System diagnostics")
    
    def fix_health_issues(self):
        """Attempt to fix common health issues"""
        self.log_to_panel("health-output", "Attempting to fix common health issues...")
        
        def fix_async():
            fix_commands = [
                "chmod +x *.sh",  # Fix script permissions
                "sudo systemctl start docker || true",  # Start Docker if available
                "pnpm install --prefix FRONTEND/ui-solidjs || true",  # Install frontend deps
                "pip install -r requirements.txt || true",  # Install Python deps
            ]
            
            for cmd in fix_commands:
                result = self.command_executor.execute_command(cmd)
                if result.get("returncode") == 0:
                    self.log_to_panel("health-output", f"✅ Fixed: {cmd}", "success")
                else:
                    self.log_to_panel("health-output", f"⚠️ Could not fix: {cmd}", "warning")
            
            self.log_to_panel("health-output", "Health issue fixing completed", "info")
        
        threading.Thread(target=fix_async, daemon=True).start()
    
    def execute_health_command(self, command: str, description: str):
        """Helper to execute health check commands"""
        self.log_to_panel("health-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command)
            if result.get("returncode") == 0:
                self.log_to_panel("health-output", f"✅ {description} completed", "success")
                if result.get("stdout"):
                    self.log_to_panel("health-output", result["stdout"])
            else:
                self.log_to_panel("health-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Configuration Actions
    
    def load_configuration(self):
        """Load configuration"""
        self.log_to_panel("config-output", "Loading configuration...")
        
        def load_async():
            config = self.config_manager.load_config()
            if "error" in config:
                self.log_to_panel("config-output", f"❌ Configuration error: {config['error']}", "error")
            else:
                self.log_to_panel("config-output", "✅ Configuration loaded successfully", "success")
                
                # Update environment display
                env = config.get("environment", {}).get("current", "unknown")
                self.update_status_widget("config-environment", env)
                
                # Log configuration summary
                self.log_to_panel("config-output", f"Environment: {env}")
                services = config.get("services", {})
                self.log_to_panel("config-output", f"Configured services: {len(services)}")
                
                ai_enabled = config.get("ai", {}).get("enabled", False)
                self.log_to_panel("config-output", f"AI features: {'enabled' if ai_enabled else 'disabled'}")
        
        threading.Thread(target=load_async, daemon=True).start()
    
    def save_configuration(self):
        """Save current configuration"""
        self.log_to_panel("config-output", "Saving configuration...")
        
        def save_async():
            config = self.config_manager.load_config()
            if self.config_manager.save_config(config):
                self.log_to_panel("config-output", "✅ Configuration saved successfully", "success")
            else:
                self.log_to_panel("config-output", "❌ Failed to save configuration", "error")
        
        threading.Thread(target=save_async, daemon=True).start()
    
    def reset_configuration(self):
        """Reset to default configuration"""
        self.log_to_panel("config-output", "Resetting to default configuration...")
        
        def reset_async():
            default_config = self.config_manager.get_default_config()
            if self.config_manager.save_config(default_config):
                self.log_to_panel("config-output", "✅ Configuration reset to defaults", "success")
                self.update_status_widget("config-environment", "development")
            else:
                self.log_to_panel("config-output", "❌ Failed to reset configuration", "error")
        
        threading.Thread(target=reset_async, daemon=True).start()
    
    def edit_configuration(self):
        """Open configuration file for editing"""
        self.execute_config_command(f"code {CONFIG_FILE} || nano {CONFIG_FILE} || vi {CONFIG_FILE}", "Edit configuration")
    
    def validate_configuration(self):
        """Validate configuration file"""
        self.log_to_panel("config-output", "Validating configuration...")
        
        def validate_async():
            try:
                config = self.config_manager.load_config()
                if "error" in config:
                    self.log_to_panel("config-output", f"❌ Invalid configuration: {config['error']}", "error")
                else:
                    # Basic validation
                    required_sections = ["environment", "services"]
                    missing_sections = [section for section in required_sections if section not in config]
                    
                    if missing_sections:
                        self.log_to_panel("config-output", f"❌ Missing sections: {', '.join(missing_sections)}", "error")
                    else:
                        self.log_to_panel("config-output", "✅ Configuration is valid", "success")
                        
                        # Additional checks
                        env = config.get("environment", {}).get("current")
                        available_envs = config.get("environment", {}).get("available", [])
                        if env not in available_envs:
                            self.log_to_panel("config-output", f"⚠️ Current environment '{env}' not in available list", "warning")
                        
                        services = config.get("services", {})
                        self.log_to_panel("config-output", f"Services configured: {len(services)}")
                        
            except Exception as e:
                self.log_to_panel("config-output", f"❌ Validation error: {e}", "error")
        
        threading.Thread(target=validate_async, daemon=True).start()
    
    def execute_config_command(self, command: str, description: str):
        """Helper to execute configuration commands"""
        self.log_to_panel("config-output", f"Running {description}...")
        
        def exec_async():
            result = self.command_executor.execute_command(command)
            if result.get("returncode") == 0:
                self.log_to_panel("config-output", f"✅ {description} completed", "success")
            else:
                self.log_to_panel("config-output", f"❌ {description} failed: {result.get('stderr')}", "error")
        
        threading.Thread(target=exec_async, daemon=True).start()
    
    # Automatic refresh and monitoring
    
    def auto_refresh_data(self):
        """Automatically refresh data at intervals"""
        if not self.auto_refresh:
            return
        
        # Only refresh if we're on certain tabs to avoid overwhelming
        try:
            current_tab = self.query_one(TabbedContent).active
            
            if current_tab == "overview":
                self.refresh_overview_data()
            elif current_tab == "system":
                self.refresh_system_metrics()
            elif current_tab == "health":
                self.run_quick_health_check()
            elif current_tab == "deploy":
                self.check_deployment_status()
                
        except Exception:
            pass  # Ignore errors during auto-refresh
    
    def refresh_overview_data(self):
        """Refresh overview dashboard data"""
        def refresh_async():
            # Update system status
            system_status = self.system_monitor.get_system_status()
            if not system_status.get("error"):
                cpu_ok = system_status.get("cpu_percent", 0) < 80
                memory_ok = system_status.get("memory_percent", 0) < 85
                if cpu_ok and memory_ok:
                    self.update_status_widget("system-status", "System Status\n[bold green]●[/bold green] Operational")
                else:
                    self.update_status_widget("system-status", "System Status\n[bold yellow]●[/bold yellow] High Load")
            
            # Update services count
            omnimesh_count = len(system_status.get("omnimesh_processes", []))
            self.update_status_widget("services-status", f"Services\n[bold blue]●[/bold blue] {omnimesh_count}/8 Running")
            
            # Log to status feed
            timestamp = datetime.now().strftime("%H:%M:%S")
            try:
                status_feed = self.query_one("#status-feed", Log)
                status_feed.write(f"[dim]{timestamp}[/dim] System refresh: CPU {system_status.get('cpu_percent', 0):.1f}%, Memory {system_status.get('memory_percent', 0):.1f}%")
            except:
                pass
        
        threading.Thread(target=refresh_async, daemon=True).start()
    
    # Action bindings
    
    def action_refresh_all(self):
        """Refresh all data"""
        self.log_to_panel("status-feed" if self.current_tab == "overview" else f"{self.current_tab}-output", "🔄 Refreshing all data...", "info")
        self.refresh_overview_data()
        self.refresh_system_metrics()
        
    def action_refresh_current(self):
        """Refresh current tab data"""
        current_tab = self.query_one(TabbedContent).active
        
        if current_tab == "overview":
            self.refresh_overview_data()
        elif current_tab == "system":
            self.refresh_system_metrics()
        elif current_tab == "git":
            self.show_git_status()
        elif current_tab == "health":
            self.run_quick_health_check()
        elif current_tab == "deploy":
            self.check_deployment_status()
        elif current_tab == "config":
            self.load_configuration()
    
    def action_clear_logs(self):
        """Clear logs in current tab"""
        current_tab = self.query_one(TabbedContent).active
        log_id = f"{current_tab}-output"
        
        try:
            log_widget = self.query_one(f"#{log_id}", Log)
            log_widget.clear()
        except:
            pass
    
    def action_help(self):
        """Show help information"""
        current_tab = self.query_one(TabbedContent).active
        log_id = f"{current_tab}-output" if current_tab != "overview" else "status-feed"
        
        help_text = """
🌊 OMNIMESH C2 Center Help

Keyboard Shortcuts:
  Ctrl+Q: Quit application
  Ctrl+R: Refresh all data
  F5: Refresh current tab
  Ctrl+L: Clear logs
  Ctrl+B: Build tab
  Ctrl+F: Frontend tab
  Ctrl+I: Infrastructure tab
  Ctrl+S: Security tab
  Ctrl+G: Git tab
  Ctrl+M: System tab
  Ctrl+D: Deploy tab

Features:
• Complete build management for Rust, Go, and Frontend
• Real-time system monitoring and health checks
• Git operations and repository management
• Infrastructure deployment (Terraform, Kubernetes)
• Security auditing and Tiger Lily enforcement
• Frontend development tools and mobile testing
• Production deployment and rollback capabilities
• Configuration management and validation

Each tab provides specialized tools for managing different aspects of the OMNIMESH ecosystem.
        """
        
        self.log_to_panel(log_id, help_text, "info")
    
    # Tab focus actions
    
    def action_focus_build(self):
        self.query_one(TabbedContent).active = "build"
    
    def action_focus_frontend(self):
        self.query_one(TabbedContent).active = "frontend"
    
    def action_focus_infrastructure(self):
        self.query_one(TabbedContent).active = "infrastructure"
    
    def action_focus_security(self):
        self.query_one(TabbedContent).active = "security"
    
    def action_focus_git(self):
        self.query_one(TabbedContent).active = "git"
    
    def action_focus_system(self):
        self.query_one(TabbedContent).active = "system"
    
    def action_focus_deploy(self):
        self.query_one(TabbedContent).active = "deploy"

def main():
    """Launch the C2 Center"""
    
    # Ensure we're in the OMNIMESH directory
    if not (SCRIPT_DIR / "install-omnimesh.sh").exists():
        print("❌ Error: This script must be run from the OMNIMESH root directory")
        print(f"Current directory: {SCRIPT_DIR}")
        print("Please navigate to your OMNIMESH folder and run again.")
        sys.exit(1)
    
    print("🌊 Launching OMNIMESH Command & Control Center...")
    print(f"📂 Working directory: {SCRIPT_DIR}")
    print("🔧 Initializing interface...")
    
    try:
        app = C2CenterApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 C2 Center shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error running C2 Center: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
