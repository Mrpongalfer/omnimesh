#!/usr/bin/env python3
"""
🌊 OmniMesh Interactive CLI - BubbleTea Style
Modern, clicky, keyboard-navigable package manager interface
"""

import asyncio
import subprocess
import webbrowser
from pathlib import Path
from rich.console import Console
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import (
    Header, Footer, Static, Button, Label, 
    ListItem, ListView, OptionList, TabPane, 
    TabbedContent, ProgressBar, Log, Tree
)
from textual.screen import Screen
from textual.reactive import reactive
from textual import events
import time
import psutil

class InterfaceCard(Static):
    """A clickable card for each interface"""
    
    def __init__(self, interface_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.interface_data = interface_data
        self.can_focus = True
    
    def compose(self) -> ComposeResult:
        data = self.interface_data
        yield Static(f"[bold cyan]{data['icon']} {data['name']}[/]", classes="card-title")
        yield Static(f"[dim]{data['description']}[/]", classes="card-description")
        yield Static(f"[green]● Ready[/] [dim]| {data['shortcut']}[/]", classes="card-status")
    
    def on_click(self) -> None:
        """Handle card clicks"""
        self.app.launch_interface(self.interface_data)
    
    def on_focus(self) -> None:
        """Handle focus events"""
        self.add_class("focused")
    
    def on_blur(self) -> None:
        """Handle blur events"""
        self.remove_class("focused")

class SystemMetrics(Static):
    """Real-time system metrics display"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
    
    def compose(self) -> ComposeResult:
        yield Static("[bold]📊 System Metrics[/]", classes="metrics-title")
        yield Static("", id="cpu-metric")
        yield Static("", id="memory-metric")
        yield Static("[red]🔥 Tiger Lily Ω^9[/]", classes="tiger-lily-status")
        yield ProgressBar(total=100, show_eta=False, id="cpu-bar")
        yield ProgressBar(total=100, show_eta=False, id="memory-bar")
    
    def on_mount(self) -> None:
        """Start metrics updates when mounted"""
        self.set_interval(2.0, self.update_metrics)
    
    def update_metrics(self) -> None:
        """Update system metrics"""
        try:
            self.cpu_usage = psutil.cpu_percent(interval=0.1)
            self.memory_usage = psutil.virtual_memory().percent
            
            # Update displays
            cpu_color = "red" if self.cpu_usage > 50 else "green"
            memory_color = "red" if self.memory_usage > 70 else "green"
            
            self.query_one("#cpu-metric").update(
                f"[{cpu_color}]CPU: {self.cpu_usage:.1f}%[/]"
            )
            self.query_one("#memory-metric").update(
                f"[{memory_color}]Memory: {self.memory_usage:.1f}%[/]"
            )
            
            # Update progress bars
            self.query_one("#cpu-bar").progress = self.cpu_usage
            self.query_one("#memory-bar").progress = self.memory_usage
            
        except Exception:
            pass

class QuickActions(Static):
    """Quick action buttons"""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold]⚡ Quick Actions[/]", classes="section-title")
        yield Button("🔍 System Status", id="btn-status", variant="primary")
        yield Button("🧪 Run Tests", id="btn-test", variant="success")
        yield Button("🚀 Deploy", id="btn-deploy", variant="warning")
        yield Button("🔒 Security", id="btn-security", variant="error")
        yield Button("❓ Help", id="btn-help", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        if button_id == "btn-status":
            self.app.run_command("./quick-start.sh status")
        elif button_id == "btn-test":
            self.app.run_command("./quick-start.sh test")
        elif button_id == "btn-deploy":
            self.app.run_command("./quick-start.sh deploy")
        elif button_id == "btn-security":
            self.app.run_command("./quick-start.sh security")
        elif button_id == "btn-help":
            self.app.push_screen("help")

class TigerLilyPanel(Static):
    """Tiger Lily enforcement panel"""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold red]🔥 Tiger Lily Enforcement Ω^9[/]", classes="section-title")
        yield Static("[red]● ACTIVE[/] [dim]Absolute Dominion Mode[/]", classes="status-line")
        yield Button("🛡️ Setup Enforcement", id="btn-tiger-setup", variant="error")
        yield Button("🔍 Compliance Check", id="btn-tiger-check", variant="warning")
        yield Button("✅ Verify Status", id="btn-tiger-verify", variant="success")
        yield Static("[dim]Factor: 729 | Level: Ω^9 | Mode: Zero-Tolerance[/]", classes="tiger-stats")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Tiger Lily button presses"""
        button_id = event.button.id
        if button_id == "btn-tiger-setup":
            self.app.run_command("./quick-start.sh tiger-lily")
        elif button_id == "btn-tiger-check":
            self.app.run_command("./quick-start.sh compliance")
        elif button_id == "btn-tiger-verify":
            self.app.run_command("./quick-start.sh enforcement")

class CommandOutput(Screen):
    """Screen for showing command output"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Quit"),
    ]
    
    def __init__(self, command: str, **kwargs):
        super().__init__(**kwargs)
        self.command = command
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"[bold]🌊 Executing: {self.command}[/]", classes="command-header"),
            Log(id="command-log", auto_scroll=True),
            id="output-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Execute command when screen mounts"""
        self.run_command_async()
    
    async def run_command_async(self) -> None:
        """Run command asynchronously and stream output"""
        log = self.query_one("#command-log")
        log.write_line(f"🚀 Starting: {self.command}")
        log.write_line("═" * 50)
        
        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=Path(__file__).parent
            )
            
            # Stream output
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                log.write_line(line.decode().rstrip())
            
            await process.wait()
            
            if process.returncode == 0:
                log.write_line("═" * 50)
                log.write_line("✅ Command completed successfully!")
            else:
                log.write_line("═" * 50)
                log.write_line(f"❌ Command failed with exit code: {process.returncode}")
                
        except Exception as e:
            log.write_line(f"❌ Error executing command: {e}")
    
    def action_dismiss(self) -> None:
        """Close the screen"""
        self.app.pop_screen()

class HelpScreen(Screen):
    """Help and documentation screen"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("[bold cyan]🌊 OmniMesh Help & Documentation[/]", classes="help-header"),
            TabbedContent(
                TabPane("Quick Start", self.create_quickstart_content()),
                TabPane("Interfaces", self.create_interfaces_content()),
                TabPane("Tiger Lily", self.create_tigerlily_content()),
                TabPane("Keyboard", self.create_keyboard_content()),
                id="help-tabs"
            ),
            id="help-container"
        )
        yield Footer()
    
    def create_quickstart_content(self) -> Container:
        """Create quick start help content"""
        return Container(
            Static("""
[bold]🚀 Quick Start Guide[/]

[cyan]Getting Started:[/]
• Use ↑↓ arrow keys to navigate
• Press Enter to select items
• Click with mouse for quick access
• Press 'w' to launch web interface
• Press 'q' to quit

[cyan]Core Interfaces:[/]
• CLI - Interactive command-line interface
• TUI - Full-screen terminal interface
• Web - Browser-based control panel
• AI - AI-powered automation system
• Orchestrator - Recursive improvement engine

[cyan]Quick Commands:[/]
• 's' - System status
• 't' - Run tests
• 'd' - Deploy system
• 'h' - Show this help
            """.strip()),
            classes="help-content"
        )
    
    def create_interfaces_content(self) -> Container:
        """Create interfaces help content"""
        return Container(
            Static("""
[bold]🖥️ Available Interfaces[/]

[cyan]📝 Interactive CLI (Ctrl+1)[/]
Rich command-line interface with guided prompts
• Questionnaire-based workflows
• Interactive command selection
• Built-in help and validation

[cyan]🎨 Textual TUI (Ctrl+2)[/]
Full-screen terminal user interface
• Real-time system monitoring
• Visual navigation and controls
• Advanced keyboard shortcuts

[cyan]🌐 Web Interface (Ctrl+3)[/]
Browser-based control panel
• Clickable buttons and controls
• Real-time metrics dashboard
• Modern responsive design

[cyan]🤖 AI Ultimate System (Ctrl+4)[/]
AI-powered automation and monitoring
• Intelligent system management
• Predictive maintenance
• Automated optimization

[cyan]🔄 System Orchestrator (Ctrl+5)[/]
Recursive improvement engine
• Self-healing capabilities
• Continuous optimization
• Exponential enhancement cycles
            """.strip()),
            classes="help-content"
        )
    
    def create_tigerlily_content(self) -> Container:
        """Create Tiger Lily help content"""
        return Container(
            Static("""
[bold red]🔥 Tiger Lily Enforcement Ω^9[/]

[cyan]Enforcement Levels:[/]
• Ω^1 - Basic enforcement (warnings as errors)
• Ω^3 - Aggressive monitoring (zero tolerance)
• Ω^6 - Invasive auditing (recursive examination)
• Ω^9 - Absolute dominion (structural dissolution)

[cyan]Current Thresholds:[/]
• CPU Usage: < 50% (dissolution trigger)
• Memory Usage: < 70% (termination trigger)
• Build Time: < 5 minutes (auditing trigger)
• Coverage: > 95% (penalty trigger)

[cyan]Enforcement Actions:[/]
• Setup perpetual monitoring
• Manual compliance checking
• Status verification
• Resource restriction
• Structural dissolution

[red]⚠️ Warning: Tiger Lily Ω^9 operates in zero-tolerance mode
Any threshold violation triggers immediate enforcement[/]
            """.strip()),
            classes="help-content"
        )
    
    def create_keyboard_content(self) -> Container:
        """Create keyboard shortcuts help content"""
        return Container(
            Static("""
[bold]⌨️ Keyboard Shortcuts[/]

[cyan]Navigation:[/]
• ↑↓ - Navigate interface cards
• ←→ - Navigate between panels
• Tab - Switch focus areas
• Enter - Activate focused item
• Space - Select/activate

[cyan]Quick Launch:[/]
• Ctrl+1 - Launch CLI interface
• Ctrl+2 - Launch TUI interface  
• Ctrl+3 - Launch Web interface
• Ctrl+4 - Launch AI Ultimate
• Ctrl+5 - Launch Orchestrator

[cyan]System Actions:[/]
• s - System status
• t - Run tests
• d - Deploy system
• m - Monitor resources
• h - Show help

[cyan]Tiger Lily:[/]
• f - Setup enforcement
• c - Compliance check
• v - Verify status

[cyan]General:[/]
• w - Open web interface
• q - Quit application
• Esc - Close current screen
• Ctrl+c - Force quit
            """.strip()),
            classes="help-content"
        )
    
    def action_dismiss(self) -> None:
        """Close the help screen"""
        self.app.pop_screen()

class OmniMeshInteractiveCLI(App):
    """Main interactive CLI application"""
    
    CSS = """
    Screen {
        background: #0a0e27;
    }
    
    Header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        height: 3;
    }
    
    Footer {
        background: #1a1a2e;
        color: #64ffda;
    }
    
    .main-grid {
        grid-size: 3 2;
        grid-gutter: 1;
        margin: 1;
    }
    
    .interface-grid {
        grid-size: 1 5;
        grid-gutter: 1;
    }
    
    InterfaceCard {
        background: rgba(255, 255, 255, 0.1);
        border: solid #64ffda;
        border-radius: 1;
        padding: 1;
        margin: 0 1;
        height: 6;
    }
    
    InterfaceCard.focused {
        background: rgba(100, 255, 218, 0.2);
        border: solid #00ff88;
    }
    
    InterfaceCard:hover {
        background: rgba(100, 255, 218, 0.15);
    }
    
    .card-title {
        text-align: center;
        margin-bottom: 1;
    }
    
    .card-description {
        text-align: center;
        margin-bottom: 1;
    }
    
    .card-status {
        text-align: center;
    }
    
    SystemMetrics {
        background: rgba(255, 255, 255, 0.05);
        border: solid #667eea;
        border-radius: 1;
        padding: 1;
        height: 100%;
    }
    
    .metrics-title {
        text-align: center;
        margin-bottom: 1;
    }
    
    .tiger-lily-status {
        text-align: center;
        margin: 1 0;
    }
    
    QuickActions {
        background: rgba(255, 255, 255, 0.05);
        border: solid #ffd93d;
        border-radius: 1;
        padding: 1;
        height: 100%;
    }
    
    TigerLilyPanel {
        background: rgba(255, 107, 107, 0.1);
        border: solid #ff4757;
        border-radius: 1;
        padding: 1;
        height: 100%;
    }
    
    .section-title {
        text-align: center;
        margin-bottom: 1;
    }
    
    .status-line {
        text-align: center;
        margin-bottom: 1;
    }
    
    .tiger-stats {
        text-align: center;
        margin-top: 1;
    }
    
    Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    #output-container {
        padding: 1;
    }
    
    .command-header {
        text-align: center;
        margin-bottom: 1;
        padding: 1;
        background: rgba(100, 255, 218, 0.1);
        border-radius: 1;
    }
    
    #help-container {
        padding: 1;
    }
    
    .help-header {
        text-align: center;
        margin-bottom: 1;
        padding: 1;
        background: rgba(100, 255, 218, 0.1);
        border-radius: 1;
    }
    
    .help-content {
        padding: 2;
        line-height: 1.5;
    }
    
    ProgressBar {
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("h", "help", "Help"),
        Binding("w", "web", "Web Interface"),
        Binding("s", "status", "Status"),
        Binding("t", "test", "Test"),
        Binding("d", "deploy", "Deploy"),
        Binding("f", "tiger_setup", "Tiger Lily Setup"),
        Binding("c", "compliance", "Compliance"),
        Binding("v", "verify", "Verify"),
        Binding("ctrl+1", "launch_cli", "CLI"),
        Binding("ctrl+2", "launch_tui", "TUI"),
        Binding("ctrl+3", "launch_web", "Web"),
        Binding("ctrl+4", "launch_ai", "AI"),
        Binding("ctrl+5", "launch_orchestrator", "Orchestrator"),
    ]
    
    TITLE = "🌊 OmniMesh Interactive Control Center"
    SUB_TITLE = "Tiger Lily Ω^9 Enhanced • Press 'h' for help"
    
    def __init__(self):
        super().__init__()
        self.interfaces = [
            {
                "id": "cli",
                "name": "Interactive CLI",
                "icon": "📝",
                "description": "Rich command-line interface with guided prompts",
                "shortcut": "Ctrl+1",
                "command": "python3 omni-interactive-tui.py"
            },
            {
                "id": "tui",
                "name": "Textual TUI",
                "icon": "🎨",
                "description": "Full-screen terminal user interface",
                "shortcut": "Ctrl+2",
                "command": "python3 omni_textual_tui.py"
            },
            {
                "id": "web",
                "name": "Web Interface",
                "icon": "🌐",
                "description": "Browser-based control panel",
                "shortcut": "Ctrl+3",
                "command": "python3 omni-web-server.py"
            },
            {
                "id": "ai",
                "name": "AI Ultimate",
                "icon": "🤖",
                "description": "AI-powered automation system",
                "shortcut": "Ctrl+4",
                "command": "python3 omni_ultimate_system.py"
            },
            {
                "id": "orchestrator",
                "name": "Orchestrator",
                "icon": "🔄",
                "description": "Recursive improvement engine",
                "shortcut": "Ctrl+5",
                "command": "python3 omni_system_orchestrator.py"
            }
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the main interface"""
        yield Header()
        
        with Grid(classes="main-grid"):
            # Left column - Interface cards
            with Vertical():
                yield Static("[bold cyan]🖥️ Available Interfaces[/]", classes="section-title")
                with Vertical(classes="interface-grid"):
                    for interface in self.interfaces:
                        yield InterfaceCard(interface, id=f"card-{interface['id']}")
            
            # Middle column - System metrics
            yield SystemMetrics(id="metrics")
            
            # Right column - Quick actions and Tiger Lily
            with Vertical():
                yield QuickActions(id="quick-actions")
                yield TigerLilyPanel(id="tiger-lily")
        
        yield Footer()
    
    def launch_interface(self, interface_data: dict) -> None:
        """Launch an interface"""
        if interface_data['id'] == 'web':
            # Special handling for web interface
            self.action_web()
        else:
            self.run_command(interface_data['command'])
    
    def run_command(self, command: str) -> None:
        """Run a command and show output"""
        self.push_screen(CommandOutput(command))
    
    def action_help(self) -> None:
        """Show help screen"""
        self.push_screen(HelpScreen())
    
    def action_web(self) -> None:
        """Launch web interface"""
        try:
            # Start web server in background
            subprocess.Popen([
                "python3", "omni-web-server.py", "--port", "8080"
            ], cwd=Path(__file__).parent)
            
            # Wait a moment then open browser
            self.set_timer(2.0, lambda: webbrowser.open("http://localhost:8080"))
            
            self.notify("🌐 Web interface starting... Opening browser in 2 seconds", severity="information")
            
        except Exception as e:
            self.notify(f"❌ Error launching web interface: {e}", severity="error")
    
    def action_status(self) -> None:
        """Show system status"""
        self.run_command("./quick-start.sh status")
    
    def action_test(self) -> None:
        """Run tests"""
        self.run_command("./quick-start.sh test")
    
    def action_deploy(self) -> None:
        """Deploy system"""
        self.run_command("./quick-start.sh deploy")
    
    def action_tiger_setup(self) -> None:
        """Setup Tiger Lily enforcement"""
        self.run_command("./quick-start.sh tiger-lily")
    
    def action_compliance(self) -> None:
        """Check compliance"""
        self.run_command("./quick-start.sh compliance")
    
    def action_verify(self) -> None:
        """Verify Tiger Lily status"""
        self.run_command("./quick-start.sh enforcement")
    
    def action_launch_cli(self) -> None:
        """Launch CLI interface"""
        self.run_command("python3 omni-interactive-tui.py")
    
    def action_launch_tui(self) -> None:
        """Launch TUI interface"""
        self.run_command("python3 omni_textual_tui.py")
    
    def action_launch_web(self) -> None:
        """Launch web interface"""
        self.action_web()
    
    def action_launch_ai(self) -> None:
        """Launch AI Ultimate"""
        self.run_command("python3 omni_ultimate_system.py")
    
    def action_launch_orchestrator(self) -> None:
        """Launch System Orchestrator"""
        self.run_command("python3 omni_system_orchestrator.py")

def main():
    """Main entry point"""
    app = OmniMeshInteractiveCLI()
    app.run()

if __name__ == "__main__":
    main()
