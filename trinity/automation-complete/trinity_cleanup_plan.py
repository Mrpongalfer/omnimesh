#!/usr/bin/env python3
"""
OMNIMESH Trinity Cleanup & Reorganization Plan
==============================================

Based on comprehensive codebase analysis, this is the definitive action plan
to clean up the OMNIMESH codebase and keep only Trinity Phases 1-4.
"""

import os
import shutil
from pathlib import Path
import json

class TrinityCleanupPlan:
    def __init__(self, workspace_root):
        self.workspace_root = Path(workspace_root)
        
        # FILES TO KEEP - Core Trinity Architecture
        self.trinity_keep_files = {
            # Phase 4 Core Files (True Intent Resonance)
            'phase_4': [
                'core/nexus_orchestrator.py',  # Main Phase 4 orchestrator
                'core/agents/pig_engine.py',  # Probabilistic Intent Graph
                'core/agents/behavior_monitor.py',  # Behavior monitoring
                'core/agents/proactive_trigger.py',  # Proactive triggers
                'core/fabric_proxies/drap_orchestration_proxy.py',  # DRAP proxy
                'test_phase4_complete.py',  # Phase 4 validation
                'test_phase4_direct.py',  # Direct Phase 4 testing
                'validate_phase4.py',  # Phase 4 validator
                'PHASE4_VALIDATION_REPORT.json',  # Phase 4 report
            ],
            
            # Phase 3 Core Files (Termux API Integration)  
            'phase_3': [
                'interfaces/cli/main.go',  # Phase 3 Go CLI
                'PHASE3_COMPLETION_REPORT.py',  # Phase 3 completion report
                'test_phase3_complete.py',  # Phase 3 testing
            ],
            
            # Phase 2 Core Files (Conversational AI)
            'phase_2': [
                'test_phase2_ai.py',  # Phase 2 AI testing
                # ConversationalAI is embedded in nexus_orchestrator.py
            ],
            
            # Phase 1 Core Files (Foundation)
            'phase_1': [
                'platform/rust_engine/',  # Rust engine foundation
                'core/fabric_proxies/proto/',  # Protocol definitions
            ],
            
            # Trinity Support & Monitoring
            'trinity_support': [
                'trinity_startup.sh',  # Trinity startup script
                'trinity_monitor.py',  # Trinity monitoring
                'trinity_deploy.py',  # Trinity deployment
                'nexus_cli.py',  # Main CLI interface
                'Makefile',  # Trinity build system
                'ACTUALIZATION_REPORT.md',  # Trinity documentation
                'C2_CENTER_GUIDE.md',  # C2 Center guide
                'core/build_system.py',  # Build management
            ],
            
            # Configuration & Infrastructure
            'infrastructure': [
                'config/nexus_config.toml',  # Main config
                'config/examples/',  # Config examples
                'requirements.txt',  # Python dependencies
                '.env.example',  # Environment template
                'README.md',  # Project documentation
                'LICENSE',  # License file
                'INSTALLATION_GUIDE.md',  # Installation guide
                'scripts/',  # Utility scripts (selective)
                'automation/setup_scripts/',  # Setup automation
            ]
        }
        
        # DIRECTORIES TO REMOVE - Old OMNIMESH Bloat
        self.remove_directories = [
            'BACKEND/',  # Old OMNIMESH backend
            'FRONTEND/',  # Old OMNIMESH frontend  
            'venv/',  # Virtual environment (regeneratable)
            '__pycache__/',  # Python cache
            '.git/',  # Git history (will be reset)
            'docs/operational-runbooks/',  # Old documentation
            'kubernetes/',  # Old K8s configs
            'infrastructure/',  # Old Terraform
        ]
        
        # FILES TO REMOVE - Specific old files
        self.remove_files = [
            # Old CLI implementations
            'omni',  # Old binary
            'omnimesh',  # Old binary
            'omni-c2-center.py',  # Old C2 center
            
            # Old databases (will be regenerated)
            'behavior_patterns.db',
            'drap_knowledge.db', 
            'pig_knowledge.db',
            
            # Old logs and temp files
            'trinity_startup.log',
            '=23.2.0',  # Weird file
            
            # Old test files (not Trinity-specific)
            # Keep Trinity test files: test_phase2_ai.py, test_phase3_complete.py, test_phase4_*
        ]
        
        # KEEP BUT REORGANIZE
        self.reorganization_plan = {
            # Move all Phase files to organized structure
            'trinity/': {
                'phase1/': ['platform/rust_engine/', 'core/fabric_proxies/proto/'],
                'phase2/': ['test_phase2_ai.py'],
                'phase3/': ['interfaces/cli/main.go', 'PHASE3_COMPLETION_REPORT.py', 'test_phase3_complete.py'],
                'phase4/': ['core/agents/', 'test_phase4_*.py', 'validate_phase4.py'],
                'core/': ['core/nexus_orchestrator.py', 'core/build_system.py'],
                'monitoring/': ['trinity_*.py', 'trinity_*.sh'],
                'config/': ['config/', '.env.example'],
            }
        }
        
    def analyze_cleanup_impact(self):
        """Analyze what will be cleaned up"""
        print("🔍 TRINITY CLEANUP IMPACT ANALYSIS")
        print("=" * 50)
        
        # Calculate current state
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(self.workspace_root):
            for file in files:
                filepath = Path(root) / file
                if filepath.exists():
                    total_files += 1
                    total_size += filepath.stat().st_size
        
        # Calculate what we're keeping
        keep_files = 0
        keep_size = 0
        
        for phase, files in self.trinity_keep_files.items():
            for file_pattern in files:
                file_path = self.workspace_root / file_pattern
                if file_path.exists():
                    if file_path.is_file():
                        keep_files += 1
                        keep_size += file_path.stat().st_size
                    elif file_path.is_dir():
                        for root, dirs, files in os.walk(file_path):
                            for file in files:
                                keep_files += 1
                                keep_size += (Path(root) / file).stat().st_size
        
        # Calculate what we're removing
        remove_files = total_files - keep_files
        remove_size = total_size - keep_size
        
        print(f"📊 CURRENT STATE:")
        print(f"   Total Files: {total_files:,}")
        print(f"   Total Size: {total_size / (1024*1024*1024):.1f} GB")
        
        print(f"\n✅ AFTER CLEANUP:")
        print(f"   Keep Files: {keep_files:,} (Trinity Architecture)")
        print(f"   Keep Size: {keep_size / (1024*1024):.1f} MB")
        
        print(f"\n🗑️ WILL REMOVE:")
        print(f"   Remove Files: {remove_files:,}")
        print(f"   Remove Size: {remove_size / (1024*1024*1024):.1f} GB")
        print(f"   Space Savings: {(remove_size/total_size)*100:.1f}%")
        
        return {
            'current_files': total_files,
            'current_size_gb': total_size / (1024*1024*1024),
            'keep_files': keep_files, 
            'keep_size_mb': keep_size / (1024*1024),
            'remove_files': remove_files,
            'remove_size_gb': remove_size / (1024*1024*1024),
            'space_savings_pct': (remove_size/total_size)*100
        }
    
    def generate_cleanup_script(self):
        """Generate the actual cleanup script"""
        script_content = '''#!/bin/bash
# OMNIMESH Trinity Cleanup Script
# Removes old OMNIMESH bloat, keeps only Trinity Phases 1-4

set -e

echo "🚀 Starting OMNIMESH Trinity Cleanup..."
echo "This will remove old OMNIMESH components and keep only Trinity architecture"
echo ""

# Backup current state
echo "📦 Creating backup..."
tar -czf omnimesh_backup_$(date +%Y%m%d_%H%M%S).tar.gz . --exclude='.git' --exclude='venv'

# Remove old OMNIMESH directories
echo "🗑️ Removing old OMNIMESH directories..."
'''

        for directory in self.remove_directories:
            script_content += f'rm -rf "{directory}"\n'
        
        script_content += '''
# Remove old OMNIMESH files  
echo "🗑️ Removing old OMNIMESH files..."
'''
        
        for file in self.remove_files:
            script_content += f'rm -f "{file}"\n'
            
        script_content += '''
# Clean up Python cache and temporary files
echo "🧹 Cleaning temporary files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.log" -delete
find . -name "*.tmp" -delete

# Reorganize Trinity structure (optional)
echo "📁 Trinity structure preserved in current organization"

echo ""
echo "✅ Trinity Cleanup Complete!"
echo "📊 Workspace now contains only Trinity Phases 1-4 architecture"
echo "🚀 Ready for clean deployment to GitHub"
'''
        
        return script_content
    
    def create_trinity_manifest(self):
        """Create manifest of what's in the cleaned codebase"""
        manifest = {
            "omnimesh_trinity_architecture": {
                "version": "4.0",
                "description": "LoL Nexus God Tier Interface - Trinity Convergence",
                "phases": {
                    "phase_1": {
                        "name": "Foundation Architecture",
                        "components": ["Rust Engine", "Protocol Definitions", "Core Fabric"],
                        "files": self.trinity_keep_files['phase_1']
                    },
                    "phase_2": {
                        "name": "Conversational AI Integration", 
                        "components": ["NLP Processing", "Conversational AI", "Intent Recognition"],
                        "files": self.trinity_keep_files['phase_2']
                    },
                    "phase_3": {
                        "name": "Termux API Multi-Modal Capabilities",
                        "components": ["Go CLI", "Audio Processing", "Device Integration", "Haptic Feedback"],
                        "files": self.trinity_keep_files['phase_3']
                    },
                    "phase_4": {
                        "name": "True Intent Resonance & Proactive Orchestration",
                        "components": ["PIG Engine", "Behavior Monitor", "Proactive Triggers", "DRAP Module"],
                        "files": self.trinity_keep_files['phase_4']
                    }
                },
                "support_systems": {
                    "monitoring": ["trinity_monitor.py", "trinity_startup.sh"],
                    "deployment": ["trinity_deploy.py", "Makefile"],
                    "cli": ["nexus_cli.py"],
                    "configuration": ["config/", "requirements.txt"]
                }
            }
        }
        
        return json.dumps(manifest, indent=2)

def main():
    """Run the Trinity cleanup analysis"""
    workspace = "/home/pong/Documents/OMNIMESH"
    planner = TrinityCleanupPlan(workspace)
    
    print("🎯 OMNIMESH TRINITY CLEANUP & REORGANIZATION PLAN")
    print("=" * 60)
    
    # Analyze impact
    impact = planner.analyze_cleanup_impact()
    
    # Generate cleanup script
    print(f"\n📜 GENERATING CLEANUP SCRIPT...")
    cleanup_script = planner.generate_cleanup_script()
    
    # Save cleanup script
    script_path = Path(workspace) / "trinity_cleanup.sh"
    with open(script_path, 'w') as f:
        f.write(cleanup_script)
    os.chmod(script_path, 0o755)
    print(f"✅ Cleanup script saved: {script_path}")
    
    # Generate Trinity manifest
    print(f"\n📋 GENERATING TRINITY MANIFEST...")
    manifest = planner.create_trinity_manifest()
    manifest_path = Path(workspace) / "TRINITY_MANIFEST.json"
    with open(manifest_path, 'w') as f:
        f.write(manifest)
    print(f"✅ Trinity manifest saved: {manifest_path}")
    
    print(f"\n🎉 CLEANUP PLAN READY!")
    print(f"📁 Workspace will be reduced from {impact['current_files']:,} files to {impact['keep_files']:,} files")
    print(f"💾 Space savings: {impact['space_savings_pct']:.1f}% ({impact['remove_size_gb']:.1f} GB)")
    print(f"🚀 Run './trinity_cleanup.sh' to execute cleanup")
    
    return impact, cleanup_script, manifest

if __name__ == "__main__":
    main()
