#!/usr/bin/env python3
"""
🧪 OmniMesh TUI Test Suite
Comprehensive testing for the OmniMesh Control Center implementations.
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing module imports...")
    
    required_modules = [
        "yaml",
        "rich",
        "questionary", 
        "textual",
        "pydantic",
        "typer"
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            spec = importlib.util.find_spec(module)
            if spec is None:
                failed_imports.append(module)
                print(f"❌ {module} - Not installed")
            else:
                print(f"✅ {module} - Available")
        except Exception as e:
            failed_imports.append(module)
            print(f"❌ {module} - Error: {e}")
    
    if failed_imports:
        print(f"\n❌ Missing modules: {', '.join(failed_imports)}")
        print("📦 Install with: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required modules are available")
        return True

def test_config_files():
    """Test that configuration files exist and are valid"""
    print("\n🔍 Testing configuration files...")
    
    config_files = [
        "omni-config.yaml",
        "requirements.txt",
        "omni_launcher.py",
        "omni-interactive-tui.py",
        "omni_textual_tui.py",
        "omni_tui.css",
        "omni_textual_tui.css"
    ]
    
    missing_files = []
    
    for file in config_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"✅ {file} - Found")
        else:
            missing_files.append(file)
            print(f"❌ {file} - Missing")
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ All configuration files are present")
        return True

def test_yaml_config():
    """Test that YAML configuration is valid"""
    print("\n🔍 Testing YAML configuration...")
    
    try:
        import yaml
        with open("omni-config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        required_sections = ["environment", "services", "ai", "monitoring", "security"]
        
        for section in required_sections:
            if section in config:
                print(f"✅ {section} - Present")
            else:
                print(f"❌ {section} - Missing")
                return False
        
        print("\n✅ YAML configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ YAML configuration error: {e}")
        return False

def test_cli_launch():
    """Test that CLI launcher works"""
    print("\n🔍 Testing CLI launcher...")
    
    try:
        # Test help output
        result = subprocess.run(
            [sys.executable, "omni_launcher.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ CLI launcher help works")
            return True
        else:
            print(f"❌ CLI launcher help failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ CLI launcher test error: {e}")
        return False

def test_textual_import():
    """Test that Textual TUI can be imported"""
    print("\n🔍 Testing Textual TUI import...")
    
    try:
        # Try to import the Textual TUI module
        sys.path.insert(0, ".")
        from omni_textual_tui import OmniMeshTextualTUI
        
        # Check if the main class exists
        print("✅ Textual TUI class found")
        return True
            
    except Exception as e:
        print(f"❌ Textual TUI import error: {e}")
        return False

def test_ultimate_system_import():
    """Test that the ultimate system can be imported"""
    try:
        from omni_ultimate_system import OmniMeshUltimateSystem
        print("✅ Ultimate system import successful")
        return True
    except ImportError as e:
        print(f"❌ Ultimate system import failed: {e}")
        return False

def test_orchestrator_import():
    """Test that the system orchestrator can be imported"""
    try:
        from omni_system_orchestrator import OrchestratorTUI
        print("✅ System orchestrator import successful")
        return True
    except ImportError as e:
        print(f"❌ System orchestrator import failed: {e}")
        return False

def test_launcher_functionality():
    """Test the enhanced launcher functionality"""
    try:
        # Test import
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import the launcher module directly
        spec = importlib.util.spec_from_file_location("omni_launcher", "omni-launcher.py")
        if spec is None or spec.loader is None:
            print("❌ Could not load launcher module")
            return False
            
        launcher_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher_module)
        
        # Test launcher creation
        launcher = launcher_module.OmniMeshLauncher()
        
        # Test interfaces
        expected_interfaces = ["cli", "tui", "ultimate", "orchestrator"]
        for interface in expected_interfaces:
            if interface not in launcher.interfaces:
                print(f"❌ Interface {interface} not found in launcher")
                return False
        
        print("✅ Enhanced launcher functionality test passed")
        return True
    except Exception as e:
        print(f"❌ Launcher functionality test failed: {e}")
        return False

def test_recursive_improvement_features():
    """Test recursive improvement capabilities"""
    try:
        from omni_system_orchestrator import SystemOrchestrator, AIOrchestrator, SystemState
        
        # Test system state
        state = SystemState()
        print("✅ SystemState created successfully")
        
        # Test AI orchestrator
        ai_orch = AIOrchestrator(enabled=False)  # Test without API key
        print("✅ AIOrchestrator created successfully")
        
        # Test system orchestrator
        sys_orch = SystemOrchestrator()
        print("✅ SystemOrchestrator created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Recursive improvement features test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 OmniMesh TUI Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration Files", test_config_files),
        ("YAML Configuration", test_yaml_config),
        ("CLI Launcher", test_cli_launch),
        ("Textual TUI Import", test_textual_import),
        ("Ultimate System Import", test_ultimate_system_import),
        ("Orchestrator Import", test_orchestrator_import),
        ("Launcher Functionality", test_launcher_functionality),
        ("Recursive Improvement Features", test_recursive_improvement_features)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! OmniMesh TUI is ready to use.")
        print("\n🚀 Quick Start:")
        print("   python omni-launcher.py        # CLI mode")
        print("   python omni-launcher.py --tui  # Full TUI mode")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
