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
        """Open configuration"""
        # This could open a configuration dialog
        status = self.query_one("#install-status", Static)
        status.update("⚙️ Configuration interface - TODO: Implement config dialog")

class C2CenterApp(App):
    """Main Command & Control Center Application"""
    
    CSS = """
    .panel-title {
        background: #1e3a8a;
        color: white;
        padding: 1;
        margin-bottom: 1;
        text-align: center;
        text-style: bold;
    }
    
    .git-btn, .sys-btn, .cmd-btn, .install-btn {
        margin: 1;
        min-width: 12;
    }
    
    #git-output, #sys-info, #sys-processes, #sys-services, #install-status {
        background: #1f2937;
        color: #f3f4f6;
        padding: 1;
        margin: 1;
        border: solid #374151;
    }
    
    #cmd-log {
        height: 15;
        background: #111827;
        border: solid #374151;
    }
    
    TabbedContent {
        height: 100%;
    }
    
    TabPane {
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("g", "focus_git", "Git Tab"),
        Binding("s", "focus_system", "System Tab"),
        Binding("c", "focus_command", "Command Tab"),
        Binding("i", "focus_installer", "Installer Tab"),
    ]
    
    def __init__(self):
        super().__init__()
        self.git_manager = GitManager(SCRIPT_DIR)
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield TabbedContent(
            TabPane("🔧 Git Operations", GitPanel(self.git_manager), id="git-tab"),
            TabPane("📊 System Monitor", SystemPanel(), id="system-tab"),
            TabPane("⚡ Command Center", CommandPanel(), id="command-tab"),
            TabPane("🚀 Installer", InstallerPanel(), id="installer-tab"),
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self.title = "🌊 OMNIMESH Command & Control Center"
        self.sub_title = f"Managing: {SCRIPT_DIR.name}"
    
    def action_refresh(self) -> None:
        """Refresh current tab"""
        # Trigger refresh on current tab
        pass
    
    def action_focus_git(self) -> None:
        self.query_one(TabbedContent).active = "git-tab"
    
    def action_focus_system(self) -> None:
        self.query_one(TabbedContent).active = "system-tab"
    
    def action_focus_command(self) -> None:
        self.query_one(TabbedContent).active = "command-tab"
    
    def action_focus_installer(self) -> None:
        self.query_one(TabbedContent).active = "installer-tab"

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
