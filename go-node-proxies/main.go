package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/omnimesh/go-node-proxies/internal/container"
	fabricpb "github.com/omnimesh/go-node-proxies/internal/fabricpb"
	"github.com/omnimesh/go-node-proxies/internal/monitor"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/emptypb"
)

// NodeProxyServer implements the NodeProxyService
type NodeProxyServer struct {
	fabricpb.UnimplementedNodeProxyServiceServer
	agentsMu      sync.RWMutex
	agents        map[string]*AgentInfo // Map of agent ID to agent info
	containerMgr  *container.Manager
	systemMonitor *monitor.Monitor
	nodeID        string
	fabricClient  fabricpb.FabricServiceClient
}

type AgentInfo struct {
	ID     string
	Name   string
	Type   string
	Status string
}

func (s *NodeProxyServer) DeployAgent(ctx context.Context, req *fabricpb.DeployAgentRequest) (*fabricpb.CommandResponse, error) {
	log.Printf("Received DeployAgent request: %+v", req)

	s.agentsMu.Lock()
	defer s.agentsMu.Unlock()

	// Create deployment configuration
	deployConfig := &container.DeploymentConfig{
		AgentID:   req.AgentId,
		AgentType: req.AgentType,
		Name:      fmt.Sprintf("omnitide-agent-%s", req.AgentId),
		Image:     getAgentImage(req.AgentType),
		Environment: map[string]string{
			"AGENT_ID":   req.AgentId,
			"AGENT_TYPE": req.AgentType,
			"AGENT_NAME": req.Name,
			"NODE_ID":    s.nodeID,
		},
		Memory:        512, // 512MB default
		CPUShares:     512, // Half CPU share
		RestartPolicy: "unless-stopped",
		NetworkMode:   "bridge",
		Labels: map[string]string{
			"omnitide.component": "ai-agent",
			"omnitide.version":   "1.0",
		},
	}

	// Add parameters from request
	for key, value := range req.Parameters {
		deployConfig.Environment[key] = value
	}

	// Deploy the container
	containerInfo, err := s.containerMgr.DeployAgent(ctx, deployConfig)
	if err != nil {
		log.Printf("Failed to deploy agent %s: %v", req.AgentId, err)
		return &fabricpb.CommandResponse{
			Status:  "ERROR",
			Message: fmt.Sprintf("Failed to deploy agent: %v", err),
		}, nil
	}

	// Update local tracking
	agent := &AgentInfo{
		ID:     req.AgentId,
		Name:   req.Name,
		Type:   req.AgentType,
		Status: "Running",
	}
	s.agents[req.AgentId] = agent

	log.Printf("Successfully deployed agent %s (%s) in container %s", req.AgentId, req.Name, containerInfo.ID)

	return &fabricpb.CommandResponse{
		Status:  "SUCCESS",
		Message: fmt.Sprintf("Agent deployed successfully in container %s", containerInfo.ID),
	}, nil
}

func (s *NodeProxyServer) StopAgent(ctx context.Context, req *fabricpb.StopAgentRequest) (*fabricpb.CommandResponse, error) {
	log.Printf("Received StopAgent request: %+v", req)

	s.agentsMu.Lock()
	defer s.agentsMu.Unlock()

	agent, exists := s.agents[req.AgentId]
	if !exists {
		return &fabricpb.CommandResponse{
			Status:  "ERROR",
			Message: fmt.Sprintf("Agent %s not found", req.AgentId),
		}, nil
	}

	// Stop the container
	if err := s.containerMgr.StopAgent(ctx, req.AgentId); err != nil {
		log.Printf("Failed to stop agent %s: %v", req.AgentId, err)
		return &fabricpb.CommandResponse{
			Status:  "ERROR",
			Message: fmt.Sprintf("Failed to stop agent: %v", err),
		}, nil
	}

	// Update status
	agent.Status = "Stopped"
	log.Printf("Successfully stopped agent %s", req.AgentId)

	return &fabricpb.CommandResponse{
		Status:  "SUCCESS",
		Message: fmt.Sprintf("Agent %s stopped successfully", req.AgentId),
	}, nil
}

// getAgentImage returns the Docker image for a given agent type
func getAgentImage(agentType string) string {
	switch agentType {
	case "synthesizer":
		return "omnitide/ai-agent-synthesizer:latest"
	case "protector":
		return "omnitide/ai-agent-protector:latest"
	case "analyzer":
		return "omnitide/ai-agent-analyzer:latest"
	default:
		return "omnitide/ai-agent-base:latest"
	}
}

func main() {
	fmt.Println("Go Compute Node Proxy (GCNP) starting...")

	// Initialize container manager
	containerMgr, err := container.NewManager()
	if err != nil {
		log.Fatalf("Failed to initialize container manager: %v", err)
	}
	defer containerMgr.Close()

	// Initialize system monitor
	systemMonitor := monitor.NewMonitor(30 * time.Second)

	// Initialize the node proxy server
	proxyServer := &NodeProxyServer{
		agents:        make(map[string]*AgentInfo),
		containerMgr:  containerMgr,
		systemMonitor: systemMonitor,
	}

	// Start gRPC server for NodeProxyService
	proxyListenAddr := "0.0.0.0:50052"
	lis, err := net.Listen("tcp", proxyListenAddr)
	if err != nil {
		log.Fatalf("Failed to listen on %s: %v", proxyListenAddr, err)
	}

	grpcServer := grpc.NewServer()
	fabricpb.RegisterNodeProxyServiceServer(grpcServer, proxyServer)

	go func() {
		log.Printf("NodeProxy gRPC server listening on %s", proxyListenAddr)
		if err := grpcServer.Serve(lis); err != nil {
			log.Fatalf("Failed to serve gRPC: %v", err)
		}
	}()

	// Connect to Nexus Prime as a client
	addr := "[::1]:50053"
	conn, err := grpc.Dial(addr, grpc.WithInsecure(), grpc.WithBlock(), grpc.WithTimeout(5*time.Second))
	if err != nil {
		log.Fatalf("Failed to connect to Nexus Prime: %v", err)
	}
	defer conn.Close()
	fmt.Println("Connected to Nexus Prime at", addr)

	client := fabricpb.NewFabricServiceClient(conn)
	proxyServer.fabricClient = client

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Register with Nexus Prime
	req := &fabricpb.AgentRegistrationRequest{
		AgentType:          fabricpb.AgentType_AGENT_TYPE_PC,
		IpAddress:          "127.0.0.1",
		Capabilities:       "cpu:4,ram:16GB,gpu:0,docker:enabled",
		ProxyListenAddress: proxyListenAddr,
	}
	resp, err := client.RegisterAgent(ctx, req)
	if err != nil {
		log.Fatalf("RegisterAgent failed: %v", err)
	}
	proxyServer.nodeID = resp.NodeId
	fmt.Printf("Registered with Nexus Prime. Node ID: %s, Status: %s\n", resp.NodeId, resp.Status)

	// Start system monitoring
	monitorCtx, monitorCancel := context.WithCancel(context.Background())
	defer monitorCancel()

	go func() {
		if err := systemMonitor.Start(monitorCtx); err != nil {
			log.Printf("System monitor error: %v", err)
		}
	}()

	// Start periodic status updates with telemetry
	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-monitorCtx.Done():
				return
			case <-ticker.C:
				metrics := systemMonitor.GetLatestMetrics()
				if metrics != nil {
					telemetry := &fabricpb.TelemetryData{
						CpuUtilization:    float32(metrics.CPUPercent / 100.0),
						MemoryUtilization: float32(metrics.MemoryPercent / 100.0),
						NetworkInKbps:     float32(metrics.NetworkBytesRecv / 1024),
						NetworkOutKbps:    float32(metrics.NetworkBytesSent / 1024),
					}

					statusReq := &fabricpb.AgentStatusUpdate{
						NodeId:        proxyServer.nodeID,
						StatusType:    fabricpb.StatusType_STATUS_TYPE_NODE,
						StatusValue:   "Online",
						TelemetryData: telemetry,
					}

					_, err := client.UpdateAgentStatus(context.Background(), statusReq)
					if err != nil {
						log.Printf("Failed to send status update: %v", err)
					}
				}
			}
		}
	}()

	// Subscribe to event stream
	go func() {
		eventStream, err := client.StreamFabricEvents(context.Background(), &emptypb.Empty{})
		if err != nil {
			log.Printf("StreamFabricEvents error: %v", err)
			return
		}
		for {
			event, err := eventStream.Recv()
			if err != nil {
				log.Printf("Event stream closed: %v", err)
				return
			}
			fmt.Printf("Received event: %s - %s\n", event.EventType, event.Message)
		}
	}()

	// Start enhanced health and metrics HTTP server
	go startHealthServer(systemMonitor, containerMgr, proxyServer)

	// Set up graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	fmt.Println("Go Compute Node Proxy is running. Press Ctrl+C to stop.")
	<-sigChan

	fmt.Println("Shutting down gracefully...")
	grpcServer.GracefulStop()
	monitorCancel()
}

// startHealthServer starts an enhanced HTTP server for health, metrics, and management endpoints
func startHealthServer(systemMonitor *monitor.Monitor, containerMgr *container.Manager, nodeServer *NodeProxyServer) {
	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	http.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		metrics := systemMonitor.GetLatestMetrics()
		if metrics != nil {
			if data, err := json.Marshal(metrics); err == nil {
				w.Write(data)
			} else {
				http.Error(w, "Failed to marshal metrics", http.StatusInternalServerError)
			}
		} else {
			w.Write([]byte("{}"))
		}
	})

	http.HandleFunc("/agents", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		agents := containerMgr.ListAgents()
		if data, err := json.Marshal(agents); err == nil {
			w.Write(data)
		} else {
			http.Error(w, "Failed to marshal agents", http.StatusInternalServerError)
		}
	})

	http.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		status := map[string]interface{}{
			"node_id":     nodeServer.nodeID,
			"timestamp":   time.Now(),
			"status":      "online",
			"agent_count": len(nodeServer.agents),
		}
		if data, err := json.Marshal(status); err == nil {
			w.Write(data)
		} else {
			http.Error(w, "Failed to marshal status", http.StatusInternalServerError)
		}
	})

	log.Printf("Health and metrics server starting on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Printf("Health server error: %v", err)
	}
}
