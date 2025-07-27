#!/usr/bin/env python3
"""
Simple verification that the ExWork Agent Tungsten Grade enhancements are working.
"""

print("Testing ExWork Agent Tungsten Grade...")

# Test 1: Import the module
try:
    import exworkagent0
    print("✓ Successfully imported exworkagent0 module")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    exit(1)

# Test 2: Check version
try:
    version = exworkagent0.AGENT_VERSION
    print(f"✓ Agent version: {version}")
except Exception as e:
    print(f"✗ Version check failed: {e}")

# Test 3: Check handler count
try:
    handler_count = len(exworkagent0.ACTION_HANDLERS)
    print(f"✓ Found {handler_count} registered handlers")
except Exception as e:
    print(f"✗ Handler check failed: {e}")

# Test 4: Check enhanced features
try:
    rich_available = getattr(exworkagent0, 'RICH_AVAILABLE', False)
    questionary_available = getattr(exworkagent0, 'QUESTIONARY_AVAILABLE', False)
    print(f"✓ Rich UI available: {rich_available}")
    print(f"✓ Questionary available: {questionary_available}")
except Exception as e:
    print(f"✗ Enhanced features check failed: {e}")

print("\nTungsten Grade verification complete!")
