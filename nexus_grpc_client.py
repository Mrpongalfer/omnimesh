# gRPC client for Omnitide_Sub_Core_Agent to communicate with Nexus Prime Rust Core
import os
import time
import grpc
import threading
from pathlib import Path
import fabric_pb2
import fabric_pb2_grpc

NEXUS_GRPC_HOST = os.environ.get("NEXUS_GRPC_HOST", "localhost")
NEXUS_GRPC_PORT = int(os.environ.get("NEXUS_GRPC_PORT", "50051"))
AGENT_ID = os.environ.get("OMNITIDE_AGENT_ID", os.uname().nodename)

class NexusPrimeClient:
    def __init__(self, host=NEXUS_GRPC_HOST, port=NEXUS_GRPC_PORT, agent_id=AGENT_ID):
        self.target = f"{host}:{port}"
        self.agent_id = agent_id
        self.channel = grpc.insecure_channel(self.target)
        self.stub = fabric_pb2_grpc.FabricServiceStub(self.channel)
        self.registered = False

    def register_agent(self):
        req = fabric_pb2.RegisterAgentRequest(
            agent_id=self.agent_id,
            agent_type="python",
            hostname=os.uname().nodename,
            metadata={"cwd": str(Path.cwd())}
        )
        try:
            resp = self.stub.RegisterAgent(req)
            self.registered = True
            return resp
        except Exception as e:
            print(f"[gRPC] RegisterAgent failed: {e}")
            self.registered = False
            return None

    def update_status(self, status_msg="OK", telemetry=None):
        req = fabric_pb2.UpdateAgentStatusRequest(
            agent_id=self.agent_id,
            status=status_msg,
            telemetry=telemetry or {}
        )
        try:
            resp = self.stub.UpdateAgentStatus(req)
            return resp
        except Exception as e:
            print(f"[gRPC] UpdateAgentStatus failed: {e}")
            return None

    def run_status_loop(self, interval=30):
        def loop():
            while True:
                if not self.registered:
                    self.register_agent()
                self.update_status()
                time.sleep(interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

# Usage example (to be called from agent main):
# nexus_client = NexusPrimeClient()
# nexus_client.register_agent()
# nexus_client.run_status_loop()
