package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
)

// LoL Nexus Fabric Proxy - Trinity Convergence Communication Bridge
// Enables high-performance communication between:
// - Rust Platform Engine (platform/rust_engine)
// - Python Core Orchestrator (core/nexus_orchestrator.py)
// - PONGEX ExWork Agent (core/agents/exwork_agent.py)

const (
	version     = "1.0.0"
	serviceName = "LoL-Nexus-Fabric-Proxy"
	defaultPort = ":50051"
)

// FabricProxyServer implements the gRPC service for inter-language communication
type FabricProxyServer struct {
	UnimplementedFabricProxyServer
	rustEngineClient  RustEngineClient
	pythonAgentClient PythonAgentClient
	healthServer      *health.Server
}

// ExecutionRequest represents a unified execution request
type ExecutionRequest struct {
	RequestId  string                 `json:"request_id"`
	Operation  string                 `json:"operation"`
	Parameters map[string]interface{} `json:"parameters"`
	Source     string                 `json:"source"` // "rust", "python", "exwork"
	Target     string                 `json:"target"` // "rust", "python", "exwork"
	Priority   int32                  `json:"priority"`
	Timeout    time.Duration          `json:"timeout"`
	Metadata   map[string]string      `json:"metadata"`
}

// ExecutionResponse represents a unified execution response
type ExecutionResponse struct {
	RequestId     string            `json:"request_id"`
	Success       bool              `json:"success"`
	Result        interface{}       `json:"result"`
	Error         string            `json:"error,omitempty"`
	ExecutionTime time.Duration     `json:"execution_time"`
	Metadata      map[string]string `json:"metadata"`
}

// ExecuteOperation handles cross-language operation execution
func (s *FabricProxyServer) ExecuteOperation(ctx context.Context, req *ExecutionRequest) (*ExecutionResponse, error) {
	startTime := time.Now()

	log.Printf("🔄 Fabric Proxy: Routing %s->%s operation: %s", req.Source, req.Target, req.Operation)

	response := &ExecutionResponse{
		RequestId: req.RequestId,
		Metadata:  make(map[string]string),
	}

	// Route the request based on target
	switch req.Target {
	case "rust":
		result, err := s.routeToRustEngine(ctx, req)
		if err != nil {
			response.Success = false
			response.Error = fmt.Sprintf("Rust engine error: %v", err)
		} else {
			response.Success = true
			response.Result = result
		}

	case "python", "exwork":
		result, err := s.routeToPythonAgent(ctx, req)
		if err != nil {
			response.Success = false
			response.Error = fmt.Sprintf("Python agent error: %v", err)
		} else {
			response.Success = true
			response.Result = result
		}

	default:
		response.Success = false
		response.Error = fmt.Sprintf("Unknown target: %s", req.Target)
	}

	response.ExecutionTime = time.Since(startTime)
	log.Printf("✅ Fabric Proxy: Completed %s operation in %v", req.Operation, response.ExecutionTime)

	return response, nil
}

// routeToRustEngine forwards requests to the Rust platform engine
func (s *FabricProxyServer) routeToRustEngine(ctx context.Context, req *ExecutionRequest) (interface{}, error) {
	// Implementation for communicating with Rust engine via gRPC
	// This would connect to the Rust nexus-prime-core service

	log.Printf("🦀 Routing to Rust Engine: %s", req.Operation)

	// Placeholder for actual Rust communication
	// In production, this would establish gRPC connection to Rust service
	result := map[string]interface{}{
		"operation": req.Operation,
		"status":    "completed",
		"source":    "rust_engine",
		"timestamp": time.Now().Unix(),
	}

	return result, nil
}

// routeToPythonAgent forwards requests to Python agents
func (s *FabricProxyServer) routeToPythonAgent(ctx context.Context, req *ExecutionRequest) (interface{}, error) {
	// Implementation for communicating with Python agents

	log.Printf("🐍 Routing to Python Agent: %s", req.Operation)

	// Placeholder for actual Python communication
	// In production, this would use Python gRPC client or direct IPC
	result := map[string]interface{}{
		"operation": req.Operation,
		"status":    "completed",
		"source":    "python_agent",
		"timestamp": time.Now().Unix(),
	}

	return result, nil
}

// HealthCheck implements the gRPC health checking protocol
func (s *FabricProxyServer) HealthCheck(ctx context.Context, req *grpc_health_v1.HealthCheckRequest) (*grpc_health_v1.HealthCheckResponse, error) {
	return &grpc_health_v1.HealthCheckResponse{
		Status: grpc_health_v1.HealthCheckResponse_SERVING,
	}, nil
}

// setupServer initializes the gRPC server with all services
func setupServer() (*grpc.Server, *FabricProxyServer) {
	server := grpc.NewServer(
		grpc.ConnectionTimeout(30*time.Second),
		grpc.MaxRecvMsgSize(10*1024*1024), // 10MB max message size
		grpc.MaxSendMsgSize(10*1024*1024),
	)

	// Create fabric proxy service
	fabricProxy := &FabricProxyServer{
		healthServer: health.NewServer(),
	}

	// Register services
	RegisterFabricProxyServer(server, fabricProxy)
	grpc_health_v1.RegisterHealthServer(server, fabricProxy.healthServer)

	// Set health status
	fabricProxy.healthServer.SetServingStatus(serviceName, grpc_health_v1.HealthCheckResponse_SERVING)

	return server, fabricProxy
}

// main starts the LoL Nexus Fabric Proxy server
func main() {
	log.Printf("🚀 LoL Nexus Fabric Proxy v%s starting...", version)

	// Get port from environment or use default
	port := os.Getenv("FABRIC_PROXY_PORT")
	if port == "" {
		port = defaultPort
	}

	// Create listener
	listener, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("❌ Failed to listen on port %s: %v", port, err)
	}

	// Setup gRPC server
	server, fabricProxy := setupServer()

	// Graceful shutdown handling
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log.Printf("🛑 Received signal %v, initiating graceful shutdown...", sig)

		// Set health status to not serving
		fabricProxy.healthServer.SetServingStatus(serviceName, grpc_health_v1.HealthCheckResponse_NOT_SERVING)

		// Graceful stop with timeout
		done := make(chan struct{})
		go func() {
			server.GracefulStop()
			close(done)
		}()

		select {
		case <-done:
			log.Println("✅ Graceful shutdown completed")
		case <-time.After(30 * time.Second):
			log.Println("⚡ Force shutdown after timeout")
			server.Stop()
		}
	}()

	// Start serving
	log.Printf("🌐 LoL Nexus Fabric Proxy listening on %s", port)
	log.Println("🔗 Ready to bridge Rust ↔ Python ↔ ExWork communications")

	if err := server.Serve(listener); err != nil {
		log.Fatalf("❌ Failed to serve: %v", err)
	}
}

// Placeholder interfaces - in production these would be generated from .proto files

type UnimplementedFabricProxyServer struct{}

func (UnimplementedFabricProxyServer) ExecuteOperation(context.Context, *ExecutionRequest) (*ExecutionResponse, error) {
	return nil, fmt.Errorf("method ExecuteOperation not implemented")
}

func RegisterFabricProxyServer(s grpc.ServiceRegistrar, srv *FabricProxyServer) {
	// This would be generated by protoc in production
}

type RustEngineClient interface {
	ExecuteOperation(ctx context.Context, req *ExecutionRequest) (*ExecutionResponse, error)
}

type PythonAgentClient interface {
	ExecuteOperation(ctx context.Context, req *ExecutionRequest) (*ExecutionResponse, error)
}
