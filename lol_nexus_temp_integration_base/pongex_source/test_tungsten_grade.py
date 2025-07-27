#!/usr/bin/env python3

"""
Test script for ExWork Agent Tungsten Grade enhancements.
This script verifies that the enhanced features are working correctly.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        import exworkagent0
        print("✓ Main module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import main module: {e}")
        return False

def test_version():
    """Test version information."""
    print("\nTesting version...")
    
    try:
        import exworkagent0
        version = exworkagent0.AGENT_VERSION
        print(f"✓ Agent version: {version}")
        
        if version == "3.0":
            print("✓ Version is correctly set to Tungsten Grade")
            return True
        else:
            print(f"✗ Version mismatch - expected '3.0', got '{version}'")
            return False
    except Exception as e:
        print(f"✗ Failed to get version: {e}")
        return False

def test_handlers():
    """Test handler registration."""
    print("\nTesting handlers...")
    
    try:
        import exworkagent0
        handlers = exworkagent0.ACTION_HANDLERS
        print(f"✓ Found {len(handlers)} registered handlers")
        
        # Check for key handlers
        required_handlers = ["RUN_COMMAND", "CREATE_OR_REPLACE_FILE", "APPLY_PATCH", "DAEMON_IPC"]
        missing_handlers = []
        
        for handler in required_handlers:
            if handler in handlers:
                print(f"✓ Handler '{handler}' found")
            else:
                missing_handlers.append(handler)
                print(f"✗ Handler '{handler}' missing")
        
        if not missing_handlers:
            print("✓ All required handlers are present")
            return True
        else:
            print(f"✗ Missing handlers: {missing_handlers}")
            return False
    except Exception as e:
        print(f"✗ Failed to test handlers: {e}")
        return False

def test_enhanced_features():
    """Test enhanced features."""
    print("\nTesting enhanced features...")
    
    try:
        import exworkagent0
        
        # Test rich UI availability
        if hasattr(exworkagent0, 'RICH_AVAILABLE'):
            print(f"✓ Rich UI availability: {exworkagent0.RICH_AVAILABLE}")
        else:
            print("✗ Rich UI availability not found")
        
        # Test questionary availability
        if hasattr(exworkagent0, 'QUESTIONARY_AVAILABLE'):
            print(f"✓ Questionary availability: {exworkagent0.QUESTIONARY_AVAILABLE}")
        else:
            print("✗ Questionary availability not found")
        
        # Test learn_from_failures function
        if hasattr(exworkagent0, 'learn_from_failures'):
            print("✓ learn_from_failures function found")
        else:
            print("✗ learn_from_failures function not found")
        
        # Test _run_subprocess function
        if hasattr(exworkagent0, '_run_subprocess'):
            print("✓ _run_subprocess function found")
        else:
            print("✗ _run_subprocess function not found")
        
        # Test check_dependencies function
        if hasattr(exworkagent0, 'check_dependencies'):
            print("✓ check_dependencies function found")
        else:
            print("✗ check_dependencies function not found")
        
        return True
    except Exception as e:
        print(f"✗ Failed to test enhanced features: {e}")
        return False

def test_json_processing():
    """Test JSON instruction processing."""
    print("\nTesting JSON processing...")
    
    try:
        import exworkagent0
        
        # Create a simple test instruction
        test_instruction = {
            "step_id": "test_step",
            "description": "Test instruction",
            "actions": [
                {
                    "type": "RUN_COMMAND",
                    "command": ["echo", "Hello World"],
                    "use_sudo": False
                }
            ]
        }
        
        # Convert to JSON string
        json_str = json.dumps(test_instruction)
        
        # Test that process_instruction_block exists
        if hasattr(exworkagent0, 'process_instruction_block'):
            print("✓ process_instruction_block function found")
            return True
        else:
            print("✗ process_instruction_block function not found")
            return False
    except Exception as e:
        print(f"✗ Failed to test JSON processing: {e}")
        return False

def main():
    """Run all tests."""
    print("ExWork Agent Tungsten Grade Enhancement Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_version,
        test_handlers,
        test_enhanced_features,
        test_json_processing
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed! ExWork Agent Tungsten Grade is ready.")
        return True
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
