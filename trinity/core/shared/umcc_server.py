#!/usr/bin/env python3
"""
UMCC Server - Trinity Enhanced v5.0
Universal Multi-Component Communication Server
"""

import json
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor

class UMCCServer:
    """UMCC Protocol Server"""
    
    def __init__(self, host="localhost", port=50051):
        self.host = host
        self.port = port
        self.running = False
        self.components = {}
        self.message_queue = []
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("UMCC-Server")
    
    def start(self):
        """Start UMCC server"""
        self.running = True
        self.logger.info(f"Starting UMCC server on {self.host}:{self.port}")
        
        # Start server threads
        threading.Thread(target=self._message_processor, daemon=True).start()
        threading.Thread(target=self._health_monitor, daemon=True).start()
        
        self.logger.info("UMCC server started successfully")
    
    def stop(self):
        """Stop UMCC server"""
        self.running = False
        self.logger.info("UMCC server stopped")
    
    def _message_processor(self):
        """Process incoming messages"""
        while self.running:
            if self.message_queue:
                message = self.message_queue.pop(0)
                self._handle_message(message)
            time.sleep(0.1)
    
    def _health_monitor(self):
        """Monitor component health"""
        while self.running:
            current_time = time.time()
            for comp_id, comp_info in self.components.items():
                if current_time - comp_info.get("last_seen", 0) > 60:
                    self.logger.warning(f"Component {comp_id} appears offline")
            time.sleep(30)
    
    def _handle_message(self, message):
        """Handle incoming message"""
        sender = message.get("sender_id")
        target = message.get("target_id")
        msg_type = message.get("message_type")
        
        self.logger.info(f"Processing message: {sender} -> {target} [{msg_type}]")
        
        if target in self.components:
            # Route message to target
            return {"success": True, "routed": True}
        else:
            return {"success": False, "error": "Target not found"}
    
    def register_component(self, component_id, component_type, endpoint, capabilities=None):
        """Register a component"""
        if capabilities is None:
            capabilities = {}
        
        self.components[component_id] = {
            "type": component_type,
            "endpoint": endpoint,
            "capabilities": capabilities,
            "registered_at": time.time(),
            "last_seen": time.time()
        }
        
        self.logger.info(f"Registered component: {component_id} ({component_type})")
        return {"success": True, "registration_id": f"reg_{component_id}"}
    
    def get_component_status(self, component_id):
        """Get status of a component"""
        if component_id in self.components:
            comp = self.components[component_id]
            return {
                "component_id": component_id,
                "status": "online",
                "type": comp["type"],
                "registered_at": comp["registered_at"],
                "last_seen": comp["last_seen"]
            }
        else:
            return {"error": "Component not found"}
    
    def broadcast_event(self, event_type, source_id, event_data):
        """Broadcast event to all components"""
        event = {
            "event_type": event_type,
            "source_id": source_id,
            "event_data": event_data,
            "timestamp": time.time()
        }
        
        recipients = len(self.components)
        self.logger.info(f"Broadcasting event {event_type} to {recipients} components")
        
        return {"success": True, "recipients": recipients}
    
    def get_server_status(self):
        """Get server status"""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "components": len(self.components),
            "messages_processed": len(self.message_queue),
            "uptime": time.time()
        }

if __name__ == "__main__":
    # Demo usage
    server = UMCCServer()
    server.start()
    
    # Register some demo components
    server.register_component("agent-1", "agent", "localhost:5001")
    server.register_component("web-ui", "interface", "localhost:3000")
    
    print(f"Server status: {server.get_server_status()}")
    
    time.sleep(2)
    server.stop()
