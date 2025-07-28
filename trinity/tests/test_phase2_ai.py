#!/usr/bin/env python3
"""
Phase 2 Test: Conversational AI Integration Test
Simple test script to validate the conversational AI functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_conversational_ai():
    """Test the conversational AI components"""
    try:
        print("🧪 Testing Phase 2: Conversational AI Integration")
        
        # Test basic imports
        print("📦 Importing conversational AI components...")
        from core.nexus_orchestrator import ConversationalAI, AdvancedNLPProcessor
        print("✅ Import successful")
        
        # Test NLP processor
        print("🧠 Testing NLP processor...")
        nlp = AdvancedNLPProcessor()
        
        test_commands = [
            "check system health",
            "deploy backend service",
            "show me the status",
            "help with configuration",
            "build the application"
        ]
        
        for command in test_commands:
            result = nlp.process_natural_language(command)
            print(f"   Command: '{command}'")
            print(f"   → Intent: {result.intent} (confidence: {result.confidence:.2f})")
            print(f"   → Entities: {result.entities}")
            print(f"   → Sentiment: {result.sentiment}")
            print()
        
        # Test conversational AI
        print("💬 Testing Conversational AI...")
        ai = ConversationalAI()
        
        session = ai.start_conversation("test_user")
        print(f"✅ Session created: {session.session_id}")
        
        # Test conversation flow
        test_messages = [
            "Hello, can you check the system status?",
            "What about the backend services?",
            "Deploy the application to production",
            "Show me the deployment logs"
        ]
        
        for message in test_messages:
            response = ai.process_message(session.session_id, message)
            print(f"   User: {message}")
            print(f"   AI: {response['response']}")
            print(f"   (Intent: {response['intent']}, Confidence: {response['confidence']:.2f})")
            if response.get('requires_action'):
                print(f"   ⚡ Action required: {response['intent']}")
            print()
        
        print("🎯 Phase 2 Conversational AI Test: SUCCESS!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversational_ai()
    sys.exit(0 if success else 1)
