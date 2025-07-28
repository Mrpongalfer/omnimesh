#!/usr/bin/env python3
"""
Phase 4 Trinity Convergence Validation Script
Complete health check and integration testing
"""

import asyncio
import sys
import os
import sqlite3
import subprocess
from pathlib import Path

# Add the core directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

class Phase4Validator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.passed = 0
        self.failed = 0
        
    def print_header(self):
        print("╔═══════════════════════════════════════════════════════════════════════════════╗")
        print("║                     PHASE 4 TRINITY CONVERGENCE VALIDATION                   ║")
        print("║                         True Intent Resonance & Proactive Orchestration      ║")
        print("╚═══════════════════════════════════════════════════════════════════════════════╝")
        print()
        
    def check_component(self, name: str, check_func, *args) -> bool:
        """Run a validation check and report result"""
        try:
            result = check_func(*args)
            if result:
                print(f"✅ {name}: PASSED")
                self.passed += 1
                return True
            else:
                print(f"❌ {name}: FAILED")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            self.failed += 1
            return False
            
    def check_file_exists(self, filepath: str) -> bool:
        """Check if a file exists"""
        return (self.project_root / filepath).exists()
        
    def check_database_schema(self, db_path: str, expected_tables: list) -> bool:
        """Check if database exists and has expected tables"""
        db_file = self.project_root / db_path
        if not db_file.exists():
            return False
            
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return all(table in tables for table in expected_tables)
        except:
            return False
            
    def check_python_imports(self, module_path: str) -> bool:
        """Check if Python module can be imported"""
        try:
            # Use subprocess to test import without affecting current process
            result = subprocess.run([
                sys.executable, '-c', 
                f'import sys; sys.path.insert(0, "{self.project_root}"); import {module_path}'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
            
    def validate_phase4_components(self):
        """Validate all Phase 4 components"""
        print("🔍 Validating Phase 4 Core Components...")
        print("-" * 50)
        
        # 1. PIG Engine Validation
        self.check_component(
            "PIG Engine Module", 
            self.check_file_exists, 
            "core/agents/pig_engine.py"
        )
        
        self.check_component(
            "PIG Knowledge Database",
            self.check_database_schema,
            "pig_knowledge.db",
            ["behavioral_patterns", "intent_predictions", "predictive_insights", "neural_pathways"]
        )
        
        # 2. DRAP Engine Validation  
        self.check_component(
            "DRAP Engine Module",
            self.check_file_exists,
            "platform/rust_engine/drap_module.py"
        )
        
        self.check_component(
            "DRAP Knowledge Database",
            self.check_database_schema,
            "drap_knowledge.db",
            ["resource_allocations", "prediction_models", "performance_metrics", "ml_models"]
        )
        
        # 3. Proactive Trigger System
        self.check_component(
            "Proactive Trigger Module",
            self.check_file_exists,
            "core/agents/proactive_trigger.py"
        )
        
        # 4. Orchestration Proxy
        self.check_component(
            "DRAP Orchestration Proxy",
            self.check_file_exists,
            "core/fabric_proxies/drap_orchestration_proxy.py"
        )
        
        # 5. Configuration Files
        self.check_component(
            "Nexus Configuration",
            self.check_file_exists,
            "config/nexus_config.toml"
        )
        
        print()
        
    def validate_integration_readiness(self):
        """Validate integration readiness"""
        print("🔗 Validating Integration Readiness...")
        print("-" * 50)
        
        # Check Python module imports
        self.check_component(
            "PIG Engine Import",
            self.check_python_imports,
            "core.agents.pig_engine"
        )
        
        self.check_component(
            "DRAP Module Import", 
            self.check_python_imports,
            "platform.rust_engine.drap_module"
        )
        
        self.check_component(
            "Proactive Trigger Import",
            self.check_python_imports,
            "core.agents.proactive_trigger"
        )
        
        self.check_component(
            "Orchestration Proxy Import",
            self.check_python_imports,
            "core.fabric_proxies.drap_orchestration_proxy"
        )
        
        print()
        
    def validate_dependencies(self):
        """Validate required dependencies"""
        print("📦 Validating Dependencies...")
        print("-" * 50)
        
        required_packages = [
            'numpy', 'scipy', 'sklearn', 'networkx', 
            'asyncio', 'sqlite3', 'websockets', 'cryptography'
        ]
        
        for package in required_packages:
            self.check_component(
                f"Package: {package}",
                self.check_python_package,
                package
            )
            
        print()
        
    def check_python_package(self, package_name: str) -> bool:
        """Check if Python package is available"""
        try:
            result = subprocess.run([
                sys.executable, '-c', f'import {package_name}'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
            
    def generate_summary(self):
        """Generate validation summary"""
        print("=" * 80)
        print("🎯 PHASE 4 VALIDATION SUMMARY")
        print("=" * 80)
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print()
        
        if self.failed == 0:
            print("🎉 PHASE 4 FULLY VALIDATED - TRINITY CONVERGENCE READY!")
            print("🚀 All systems operational for True Intent Resonance & Proactive Orchestration")
            return True
        else:
            print("⚠️  PHASE 4 VALIDATION INCOMPLETE")
            print("🔧 Please address failed components before deployment")
            return False
            
    async def run_validation(self):
        """Run complete Phase 4 validation"""
        self.print_header()
        
        self.validate_phase4_components()
        self.validate_integration_readiness() 
        self.validate_dependencies()
        
        success = self.generate_summary()
        
        return success

def main():
    """Main validation entry point"""
    validator = Phase4Validator()
    
    try:
        success = asyncio.run(validator.run_validation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
