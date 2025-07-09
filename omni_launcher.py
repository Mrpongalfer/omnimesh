#!/usr/bin/env python3
"""
🌊 OmniMesh Unified Launcher
Launch CLI, TUI, or Ultimate System interfaces with exponential improvements.
"""

import argparse
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text

console = Console()

class OmniMeshLauncher:
    """Advanced launcher with recursive improvement capabilities"""
    
    def __init__(self):
        self.version = "v2.0.0-ultimate"
        self.interfaces = {
            "cli": {
                "name": "Interactive CLI",
                "description": "Rich command-line interface with questionary prompts",
                "module": "omni-interactive-tui.py",
                "features": ["Quick commands", "Interactive prompts", "Basic status"]
            },
            "tui": {
                "name": "Textual TUI",
                "description": "Full-screen terminal user interface",
                "module": "omni_textual_tui.py",
                "features": ["Full-screen interface", "Real-time updates", "Navigation"]
            },
            "ultimate": {
                "name": "Ultimate System",
                "description": "Enterprise-grade AI-powered control center",
                "module": "omni_ultimate_system.py",
                "features": ["AI assistance", "Real-time monitoring", "Emergency controls", "Production-ready"]
            }
        }
    
    def show_interface_selection(self):
        """Display interactive interface selection"""
        console.print(Panel.fit(
            f"🌊 [bold cyan]OmniMesh Control Center {self.version}[/bold cyan]\n"
            "[dim]Sovereign system with institutional rigor[/dim]",
            title="Welcome",
            border_style="cyan"
        ))
        
        table = Table(title="Available Interfaces", show_header=True)
        table.add_column("Interface", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Features", style="green")
        
        for key, info in self.interfaces.items():
            features = ", ".join(info["features"])
            table.add_row(f"[bold]{key}[/bold]", info["description"], features)
        
        console.print(table)
        console.print()
        
        # Interactive selection
        choices = list(self.interfaces.keys())
        choice = Prompt.ask(
            "Select interface",
            choices=choices,
            default="ultimate"
        )
        
        return choice
    
    def launch_interface(self, interface: str):
        """Launch the selected interface"""
        if interface not in self.interfaces:
            console.print(f"❌ Unknown interface: {interface}")
            return False
        
        info = self.interfaces[interface]
        module = info["module"]
        
        console.print(f"🚀 Launching {info['name']}...")
        
        try:
            if interface == "cli":
                import subprocess
                subprocess.run([sys.executable, module], check=True)
            elif interface == "tui":
                from omni_textual_tui import OmniMeshTextualTUI
                app = OmniMeshTextualTUI()
                app.run()
            elif interface == "ultimate":
                from omni_ultimate_system import OmniMeshUltimateSystem
                app = OmniMeshUltimateSystem()
                app.run()
            
            return True
            
        except ImportError as e:
            console.print(f"❌ Import error: {e}")
            console.print("   Please install required dependencies: pip install -r requirements.txt")
            return False
        except Exception as e:
            console.print(f"❌ Error launching {interface}: {e}")
            return False

def main():
    """Main entry point for the unified launcher"""
    parser = argparse.ArgumentParser(
        description="🌊 OmniMesh Control Center - Unified Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python omni_launcher.py                    # Interactive interface selection
  python omni_launcher.py --cli              # Launch CLI interface
  python omni_launcher.py --tui              # Launch TUI interface
  python omni_launcher.py --ultimate         # Launch Ultimate System
  python omni_launcher.py --setup            # Run setup wizard
  python omni_launcher.py --status           # Show system status
        """
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch the CLI interface"
    )
    
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch the full Textual TUI interface"
    )
    
    parser.add_argument(
        "--ultimate",
        action="store_true",
        help="Launch the Ultimate System (AI-powered)"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the setup wizard"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="OmniMesh Control Center v2.0.0-ultimate"
    )
    
    args = parser.parse_args()
    launcher = OmniMeshLauncher()
    
    # Handle specific interface launches
    if args.cli:
        return launcher.launch_interface("cli")
    elif args.tui:
        return launcher.launch_interface("tui")
    elif args.ultimate:
        return launcher.launch_interface("ultimate")
    elif args.setup:
        console.print("🏗️ Running OmniMesh Setup Wizard...")
        return launcher.launch_interface("cli")
    elif args.status:
        console.print("📊 OmniMesh System Status...")
        return launcher.launch_interface("ultimate")
    else:
        # Interactive selection
        try:
            choice = launcher.show_interface_selection()
            return launcher.launch_interface(choice)
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!")
            return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
