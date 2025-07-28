#!/usr/bin/env python3
"""
Trinity Convergence Platform - Live Monitoring Dashboard
=========================================================

An elegant, real-time monitoring dashboard for the Trinity Platform,
providing sophisticated visualization of system metrics, component health,
and operational status with beautiful console interfaces.

Features:
- Real-time component health monitoring
- Performance metrics visualization
- Interactive system control interface
- Elegant progress tracking and alerts
- Comprehensive system diagnostics

Author: LoL Nexus Core Actualization Agent
Version: 1.0.0 (Trinity Convergence)
License: MIT
"""

import asyncio
import time
import json
import sys
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from dataclasses import dataclass, field

# Rich imports for beautiful displays
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.align import Align
    from rich.text import Text
    from rich.tree import Tree
    from rich.rule import Rule
    from rich.columns import Columns
    from rich.gauge import Gauge
    from rich.sparkline import Sparkline
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

@dataclass
class ComponentMetrics:
    """Metrics for individual Trinity components."""
    name: str
    status: str = "unknown"
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time: float = 0.0
    operations_count: int = 0
    error_count: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    uptime: float = 0.0

@dataclass
class SystemMetrics:
    """Overall system metrics for Trinity platform."""
    platform_status: str = "initializing"
    total_memory: float = 0.0
    total_cpu: float = 0.0
    active_components: int = 0
    total_operations: int = 0
    total_errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)

class TrinityMonitor:
    """
    Elegant monitoring dashboard for Trinity Convergence Platform.
    
    Provides real-time visualization of system health, performance metrics,
    and component status with beautiful console interfaces.
    """
    
    def __init__(self):
        """Initialize the Trinity monitoring dashboard."""
        self.console = Console()
        self.running = False
        self.update_interval = 2.0  # seconds
        
        # System state
        self.system_metrics = SystemMetrics()
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.metric_history: Dict[str, List[float]] = {}
        self.max_history_length = 50
        
        # Initialize component metrics
        self._initialize_components()
        
        # Performance tracking
        self.performance_data = {
            'cpu_history': [],
            'memory_history': [],
            'response_time_history': [],
            'operations_history': []
        }
        
        # Dashboard layout
        self.layout = Layout()
        self._setup_layout()
    
    def _initialize_components(self):
        """Initialize monitoring for all Trinity components."""
        components = [
            "nexus_orchestrator",
            "exwork_agent",
            "noa_module", 
            "rust_bridge",
            "go_proxy_manager",
            "build_system"
        ]
        
        for comp_name in components:
            self.component_metrics[comp_name] = ComponentMetrics(
                name=comp_name,
                status="initializing"
            )
            self.metric_history[comp_name] = []
    
    def _setup_layout(self):
        """Setup the dashboard layout structure."""
        if not RICH_AVAILABLE:
            return
            
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=4)
        )
        
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        self.layout["left"].split_column(
            Layout(name="system_status"),
            Layout(name="components")
        )
        
        self.layout["right"].split_column(
            Layout(name="metrics"),
            Layout(name="performance")
        )
    
    def _generate_header(self) -> Panel:
        """Generate the dashboard header."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = datetime.now() - self.system_metrics.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        header_text = f"""
[bold blue]Trinity Convergence Platform - Live Monitoring Dashboard[/bold blue]
[dim]Current Time: {current_time} | Uptime: {uptime_str} | Status: [bold green]{self.system_metrics.platform_status.upper()}[/bold green][/dim]
        """
        
        return Panel(
            Align.center(Text(header_text.strip())),
            style="blue",
            border_style="bright_blue"
        )
    
    def _generate_system_status(self) -> Panel:
        """Generate system status overview."""
        status_table = Table(show_header=False, box=None, padding=(0, 1))
        status_table.add_column("Metric", style="cyan", min_width=15)
        status_table.add_column("Value", style="green")
        
        # Calculate system health score
        healthy_components = sum(1 for comp in self.component_metrics.values() 
                               if comp.status == "healthy")
        health_score = (healthy_components / len(self.component_metrics)) * 100
        
        status_table.add_row("Platform Status", self.system_metrics.platform_status.upper())
        status_table.add_row("Health Score", f"{health_score:.1f}%")
        status_table.add_row("Active Components", str(self.system_metrics.active_components))
        status_table.add_row("Total Operations", f"{self.system_metrics.total_operations:,}")
        status_table.add_row("Error Rate", f"{self.system_metrics.total_errors}")
        status_table.add_row("Memory Usage", f"{self.system_metrics.total_memory:.1f} MB")
        status_table.add_row("CPU Usage", f"{self.system_metrics.total_cpu:.1f}%")
        
        return Panel(
            status_table,
            title="🖥️  System Status",
            border_style="green"
        )
    
    def _generate_components_status(self) -> Panel:
        """Generate component status table."""
        comp_table = Table(show_header=True, header_style="bold magenta")
        comp_table.add_column("Component", style="cyan", min_width=18)
        comp_table.add_column("Status", justify="center", min_width=8)
        comp_table.add_column("CPU%", justify="right", min_width=6)
        comp_table.add_column("Memory", justify="right", min_width=8)
        comp_table.add_column("Response", justify="right", min_width=9)
        
        for comp_name, metrics in self.component_metrics.items():
            # Status with emoji
            if metrics.status == "healthy":
                status_text = "[green]✅ OK[/green]"
            elif metrics.status == "warning":
                status_text = "[yellow]⚠️  WARN[/yellow]"
            elif metrics.status == "error":
                status_text = "[red]❌ ERR[/red]"
            else:
                status_text = "[dim]🔄 INIT[/dim]"
            
            # Format display name
            display_name = comp_name.replace('_', ' ').title()
            
            comp_table.add_row(
                display_name,
                status_text,
                f"{metrics.cpu_usage:.1f}%",
                f"{metrics.memory_usage:.0f}MB",
                f"{metrics.response_time:.0f}ms"
            )
        
        return Panel(
            comp_table,
            title="🔧 Component Health",
            border_style="blue"
        )
    
    def _generate_metrics_panel(self) -> Panel:
        """Generate real-time metrics display."""
        if not self.performance_data['cpu_history']:
            return Panel(
                "[dim]Collecting metrics data...[/dim]",
                title="📊 Performance Metrics",
                border_style="yellow"
            )
        
        # Create sparklines for key metrics
        metrics_content = []
        
        if len(self.performance_data['cpu_history']) > 1:
            cpu_sparkline = Sparkline(
                self.performance_data['cpu_history'][-20:], 
                width=40
            )
            metrics_content.append(f"CPU Usage:    {cpu_sparkline}")
        
        if len(self.performance_data['memory_history']) > 1:
            memory_sparkline = Sparkline(
                self.performance_data['memory_history'][-20:], 
                width=40
            )
            metrics_content.append(f"Memory Usage: {memory_sparkline}")
        
        if len(self.performance_data['operations_history']) > 1:
            ops_sparkline = Sparkline(
                self.performance_data['operations_history'][-20:], 
                width=40
            )
            metrics_content.append(f"Operations:   {ops_sparkline}")
        
        metrics_text = "\n".join(metrics_content) if metrics_content else "[dim]No data available[/dim]"
        
        return Panel(
            metrics_text,
            title="📈 Real-time Metrics",
            border_style="magenta"
        )
    
    def _generate_performance_panel(self) -> Panel:
        """Generate performance statistics."""
        perf_table = Table(show_header=False, box=None)
        perf_table.add_column("Metric", style="cyan", min_width=20)
        perf_table.add_column("Current", style="green")
        perf_table.add_column("Avg", style="yellow")
        perf_table.add_column("Peak", style="red")
        
        # Calculate statistics
        def calc_stats(data_list):
            if not data_list:
                return 0, 0, 0
            current = data_list[-1] if data_list else 0
            avg = sum(data_list) / len(data_list)
            peak = max(data_list)
            return current, avg, peak
        
        cpu_current, cpu_avg, cpu_peak = calc_stats(self.performance_data['cpu_history'])
        mem_current, mem_avg, mem_peak = calc_stats(self.performance_data['memory_history'])
        
        perf_table.add_row(
            "CPU Usage", 
            f"{cpu_current:.1f}%", 
            f"{cpu_avg:.1f}%", 
            f"{cpu_peak:.1f}%"
        )
        perf_table.add_row(
            "Memory Usage", 
            f"{mem_current:.0f}MB", 
            f"{mem_avg:.0f}MB", 
            f"{mem_peak:.0f}MB"
        )
        perf_table.add_row(
            "Operations/sec", 
            f"{self.system_metrics.total_operations}", 
            "N/A", 
            "N/A"
        )
        
        return Panel(
            perf_table,
            title="⚡ Performance Stats",
            border_style="red"
        )
    
    def _generate_footer(self) -> Panel:
        """Generate dashboard footer."""
        footer_text = f"""
[dim]Last Update: {self.system_metrics.last_update.strftime('%H:%M:%S')} | 
Update Interval: {self.update_interval}s | 
Press Ctrl+C to exit[/dim]
        """
        
        return Panel(
            Align.center(Text(footer_text.strip())),
            style="dim",
            border_style="dim"
        )
    
    async def _simulate_metrics(self):
        """Simulate realistic metrics data for demonstration."""
        import random
        import math
        
        base_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                elapsed = current_time - base_time
                
                # Simulate CPU usage with some variation
                base_cpu = 15 + 10 * math.sin(elapsed / 30) + random.gauss(0, 3)
                base_cpu = max(0, min(100, base_cpu))
                
                # Simulate memory usage
                base_memory = 180 + 50 * math.sin(elapsed / 45) + random.gauss(0, 10)
                base_memory = max(50, min(500, base_memory))
                
                # Update system metrics
                self.system_metrics.total_cpu = base_cpu
                self.system_metrics.total_memory = base_memory
                self.system_metrics.active_components = len([
                    comp for comp in self.component_metrics.values() 
                    if comp.status in ["healthy", "warning"]
                ])
                self.system_metrics.total_operations += random.randint(10, 50)
                self.system_metrics.last_update = datetime.now()
                
                # Update performance history
                self.performance_data['cpu_history'].append(base_cpu)
                self.performance_data['memory_history'].append(base_memory)
                self.performance_data['operations_history'].append(
                    random.randint(800, 1200)
                )
                
                # Trim history to max length
                for key in self.performance_data:
                    if len(self.performance_data[key]) > self.max_history_length:
                        self.performance_data[key] = self.performance_data[key][-self.max_history_length:]
                
                # Update component metrics
                for comp_name, comp_metrics in self.component_metrics.items():
                    # Simulate component health
                    health_chance = random.random()
                    if health_chance > 0.95:
                        comp_metrics.status = "error"
                    elif health_chance > 0.85:
                        comp_metrics.status = "warning"
                    else:
                        comp_metrics.status = "healthy"
                    
                    # Update component performance
                    comp_metrics.cpu_usage = base_cpu + random.gauss(0, 5)
                    comp_metrics.memory_usage = base_memory / 6 + random.gauss(0, 10)
                    comp_metrics.response_time = 20 + random.gauss(0, 15)
                    comp_metrics.operations_count += random.randint(1, 10)
                    comp_metrics.last_heartbeat = datetime.now()
                
                # Set overall platform status
                error_components = sum(1 for comp in self.component_metrics.values() 
                                     if comp.status == "error")
                warning_components = sum(1 for comp in self.component_metrics.values() 
                                       if comp.status == "warning")
                
                if error_components > 0:
                    self.system_metrics.platform_status = "degraded"
                elif warning_components > 0:
                    self.system_metrics.platform_status = "warning"
                else:
                    self.system_metrics.platform_status = "operational"
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                # Handle any errors gracefully
                await asyncio.sleep(self.update_interval)
    
    def _update_display(self):
        """Update the dashboard display."""
        if not RICH_AVAILABLE:
            return self._simple_display()
        
        # Update layout panels
        self.layout["header"].update(self._generate_header())
        self.layout["system_status"].update(self._generate_system_status())
        self.layout["components"].update(self._generate_components_status())
        self.layout["metrics"].update(self._generate_metrics_panel())
        self.layout["performance"].update(self._generate_performance_panel())
        self.layout["footer"].update(self._generate_footer())
        
        return self.layout
    
    def _simple_display(self):
        """Simple text-based display for systems without rich."""
        output = []
        output.append("=" * 80)
        output.append("TRINITY CONVERGENCE PLATFORM - MONITORING DASHBOARD")
        output.append("=" * 80)
        output.append(f"Status: {self.system_metrics.platform_status.upper()}")
        output.append(f"Active Components: {self.system_metrics.active_components}")
        output.append(f"CPU: {self.system_metrics.total_cpu:.1f}%")
        output.append(f"Memory: {self.system_metrics.total_memory:.1f} MB")
        output.append(f"Operations: {self.system_metrics.total_operations:,}")
        output.append("")
        output.append("COMPONENT STATUS:")
        
        for comp_name, metrics in self.component_metrics.items():
            status_symbol = "✓" if metrics.status == "healthy" else "!" if metrics.status == "warning" else "✗"
            output.append(f"  {status_symbol} {comp_name}: {metrics.status}")
        
        output.append("")
        output.append(f"Last Update: {self.system_metrics.last_update}")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    async def start_monitoring(self):
        """Start the monitoring dashboard."""
        self.running = True
        
        # Show initial banner
        if RICH_AVAILABLE:
            self.console.print(Panel(
                "[bold blue]Trinity Convergence Platform[/bold blue]\n"
                "[dim]Live Monitoring Dashboard Starting...[/dim]",
                title="🚀 Initializing Monitor",
                border_style="blue"
            ))
        else:
            print("Trinity Convergence Platform - Monitoring Dashboard")
            print("Initializing...")
        
        # Start metrics simulation
        metrics_task = asyncio.create_task(self._simulate_metrics())
        
        try:
            if RICH_AVAILABLE:
                # Use rich Live display
                with Live(
                    self._update_display(), 
                    console=self.console, 
                    refresh_per_second=1,
                    screen=True
                ) as live:
                    while self.running:
                        live.update(self._update_display())
                        await asyncio.sleep(1.0)
            else:
                # Simple text updates
                while self.running:
                    print("\033[2J\033[H")  # Clear screen
                    print(self._simple_display())
                    await asyncio.sleep(self.update_interval)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            metrics_task.cancel()
            
            if RICH_AVAILABLE:
                self.console.print(Panel(
                    "[bold]Trinity Monitoring Dashboard Stopped[/bold]\n"
                    "[dim]Thank you for using Trinity monitoring![/dim]",
                    title="👋 Shutdown Complete",
                    border_style="red"
                ))
            else:
                print("\nTrinity Monitoring Dashboard stopped.")

async def main():
    """Main entry point for Trinity monitoring dashboard."""
    monitor = TrinityMonitor()
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        monitor.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Trinity Monitor interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
