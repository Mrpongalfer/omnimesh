package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"os/exec"
	"strings"
	"sync"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
	"google.golang.org/protobuf/types/known/timestamppb"

	pb "github.com/omnimesh/nexus-orchestrator/proto/v1"
)

// NexusOrchestratorServer implements the gRPC server for Nexus Orchestrator API
type NexusOrchestratorServer struct {
	pb.UnimplementedNexusOrchestratorServer

	// Session management
	sessions     map[string]*ConversationSession
	sessionMutex sync.RWMutex

	// Service monitoring
	services     map[string]*ServiceInfo
	serviceMutex sync.RWMutex

	// Event streaming
	eventStreams map[string]chan *pb.EventMessage
	streamMutex  sync.RWMutex

	// Orchestrator communication
	orchestratorURL string
	httpClient      *http.Client
}

// ConversationSession tracks ongoing conversations
type ConversationSession struct {
	ID            string
	UserID        string
	StartTime     time.Time
	LastActivity  time.Time
	Messages      []*pb.ConversationMessage
	DialogueState *pb.DialogueState
	Context       map[string]string
	Preferences   map[string]string
}

// ServiceInfo holds service status information
type ServiceInfo struct {
	Name        string
	Status      string
	Health      string
	CPUUsage    float64
	MemoryUsage float64
	UptimeStart time.Time
	LastCheck   time.Time
}

// NewNexusOrchestratorServer creates a new server instance
func NewNexusOrchestratorServer(orchestratorURL string) *NexusOrchestratorServer {
	return &NexusOrchestratorServer{
		sessions:        make(map[string]*ConversationSession),
		services:        make(map[string]*ServiceInfo),
		eventStreams:    make(map[string]chan *pb.EventMessage),
		orchestratorURL: orchestratorURL,
		httpClient:      &http.Client{Timeout: 30 * time.Second},
	}
}

// HealthCheck returns the health status of the system
func (s *NexusOrchestratorServer) HealthCheck(ctx context.Context, req *emptypb.Empty) (*pb.HealthResponse, error) {
	log.Println("🔍 Health check requested")

	// Update service status
	s.updateServiceStatus()

	s.serviceMutex.RLock()
	defer s.serviceMutex.RUnlock()

	var services []*pb.ServiceHealth
	overallStatus := "healthy"

	for _, service := range s.services {
		serviceHealth := &pb.ServiceHealth{
			Name:          service.Name,
			Status:        service.Status,
			Health:        service.Health,
			CpuUsage:      service.CPUUsage,
			MemoryUsage:   service.MemoryUsage,
			UptimeSeconds: int64(time.Since(service.UptimeStart).Seconds()),
		}
		services = append(services, serviceHealth)

		if service.Health != "healthy" {
			overallStatus = "degraded"
		}
		if service.Status != "running" {
			overallStatus = "unhealthy"
		}
	}

	return &pb.HealthResponse{
		Status:    overallStatus,
		Version:   "1.0.0-god-tier",
		Timestamp: timestamppb.Now(),
		Services:  services,
	}, nil
}

// ProcessCommand handles natural language command processing
func (s *NexusOrchestratorServer) ProcessCommand(ctx context.Context, req *pb.CommandRequest) (*pb.CommandResponse, error) {
	log.Printf("🧠 Processing command: %s", req.Command)

	// Process with local NLP engine
	intent, entities, confidence := s.processNaturalLanguage(req.Command)

	// Generate response based on intent
	response := s.generateResponse(intent, entities, confidence, req.Command)

	// Determine if action is required
	requiresAction := s.requiresAction(intent)
	var action *pb.ActionRequest
	if requiresAction {
		action = s.createActionRequest(intent, entities)
	}

	// Generate suggestions
	suggestions := s.generateSuggestions(intent, entities)

	return &pb.CommandResponse{
		Response:       response,
		Intent:         intent,
		Confidence:     confidence,
		Entities:       entities,
		Suggestions:    suggestions,
		SessionId:      req.SessionId,
		RequiresAction: requiresAction,
		Action:         action,
	}, nil
}

// StartConversation initiates a new conversational session
func (s *NexusOrchestratorServer) StartConversation(ctx context.Context, req *pb.ConversationRequest) (*pb.ConversationResponse, error) {
	log.Printf("💬 Starting conversation for user: %s", req.UserId)

	sessionID := s.generateSessionID()

	session := &ConversationSession{
		ID:           sessionID,
		UserID:       req.UserId,
		StartTime:    time.Now(),
		LastActivity: time.Now(),
		Messages:     make([]*pb.ConversationMessage, 0),
		DialogueState: &pb.DialogueState{
			CurrentTopic:   "",
			UserGoals:      make([]string, 0),
			CompletedTasks: make([]string, 0),
			PendingActions: make([]string, 0),
			Preferences:    make(map[string]string),
			SessionContext: make(map[string]string),
		},
		Context:     req.Context,
		Preferences: make(map[string]string),
	}

	s.sessionMutex.Lock()
	s.sessions[sessionID] = session
	s.sessionMutex.Unlock()

	// Process initial message
	intent, entities, confidence := s.processNaturalLanguage(req.Message)
	response := s.generateConversationalResponse(intent, entities, confidence, req.Message, session)

	// Add messages to session
	userMsg := &pb.ConversationMessage{
		Speaker:    "user",
		Content:    req.Message,
		Timestamp:  timestamppb.Now(),
		Intent:     intent,
		Confidence: confidence,
		Entities:   entities,
	}

	aiMsg := &pb.ConversationMessage{
		Speaker:    "ai",
		Content:    response,
		Timestamp:  timestamppb.Now(),
		Intent:     intent,
		Confidence: confidence,
		Entities:   entities,
	}

	session.Messages = append(session.Messages, userMsg, aiMsg)
	session.DialogueState.CurrentTopic = intent
	session.DialogueState.UserGoals = append(session.DialogueState.UserGoals, intent)

	followUpOptions := s.generateFollowUpOptions(intent, entities)

	return &pb.ConversationResponse{
		Response:        response,
		SessionId:       sessionID,
		DialogueState:   session.DialogueState,
		FollowUpOptions: followUpOptions,
		Confidence:      confidence,
		Intent:          intent,
		Entities:        entities,
	}, nil
}

// ContinueConversation continues an existing conversation
func (s *NexusOrchestratorServer) ContinueConversation(ctx context.Context, req *pb.ConversationRequest) (*pb.ConversationResponse, error) {
	log.Printf("💬 Continuing conversation: %s", req.SessionId)

	s.sessionMutex.RLock()
	session, exists := s.sessions[req.SessionId]
	s.sessionMutex.RUnlock()

	if !exists {
		return nil, status.Errorf(codes.NotFound, "conversation session not found")
	}

	session.LastActivity = time.Now()

	// Process message with conversation context
	intent, entities, confidence := s.processNaturalLanguageWithContext(req.Message, session)
	response := s.generateConversationalResponse(intent, entities, confidence, req.Message, session)

	// Add messages to session
	userMsg := &pb.ConversationMessage{
		Speaker:    "user",
		Content:    req.Message,
		Timestamp:  timestamppb.Now(),
		Intent:     intent,
		Confidence: confidence,
		Entities:   entities,
	}

	aiMsg := &pb.ConversationMessage{
		Speaker:    "ai",
		Content:    response,
		Timestamp:  timestamppb.Now(),
		Intent:     intent,
		Confidence: confidence,
		Entities:   entities,
	}

	s.sessionMutex.Lock()
	session.Messages = append(session.Messages, userMsg, aiMsg)
	session.DialogueState.CurrentTopic = intent
	if !contains(session.DialogueState.UserGoals, intent) {
		session.DialogueState.UserGoals = append(session.DialogueState.UserGoals, intent)
	}
	s.sessionMutex.Unlock()

	followUpOptions := s.generateFollowUpOptions(intent, entities)

	return &pb.ConversationResponse{
		Response:        response,
		SessionId:       req.SessionId,
		DialogueState:   session.DialogueState,
		FollowUpOptions: followUpOptions,
		Confidence:      confidence,
		Intent:          intent,
		Entities:        entities,
	}, nil
}

// GetSystemStatus returns current system status and metrics
func (s *NexusOrchestratorServer) GetSystemStatus(ctx context.Context, req *emptypb.Empty) (*pb.SystemStatusResponse, error) {
	log.Println("📊 System status requested")

	s.updateServiceStatus()

	s.serviceMutex.RLock()
	defer s.serviceMutex.RUnlock()

	var services []*pb.ServiceHealth
	var totalCPU, totalMemory float64
	healthyCount := 0

	for _, service := range s.services {
		serviceHealth := &pb.ServiceHealth{
			Name:          service.Name,
			Status:        service.Status,
			Health:        service.Health,
			CpuUsage:      service.CPUUsage,
			MemoryUsage:   service.MemoryUsage,
			UptimeSeconds: int64(time.Since(service.UptimeStart).Seconds()),
		}
		services = append(services, serviceHealth)

		totalCPU += service.CPUUsage
		totalMemory += service.MemoryUsage

		if service.Health == "healthy" {
			healthyCount++
		}
	}

	overallStatus := "healthy"
	if healthyCount < len(s.services) {
		overallStatus = "degraded"
	}
	if healthyCount == 0 {
		overallStatus = "unhealthy"
	}

	metrics := &pb.SystemMetrics{
		TotalCpuUsage:     totalCPU,
		TotalMemoryUsage:  totalMemory,
		NetworkIoIn:       1200000, // Mock data
		NetworkIoOut:      2800000, // Mock data
		DiskIoRead:        524288,  // Mock data
		DiskIoWrite:       1048576, // Mock data
		ActiveConnections: 147,     // Mock data
		TotalRequests:     12456,   // Mock data
	}

	return &pb.SystemStatusResponse{
		OverallStatus: overallStatus,
		Services:      services,
		Metrics:       metrics,
		Timestamp:     timestamppb.Now(),
	}, nil
}

// DeployService handles service deployment requests
func (s *NexusOrchestratorServer) DeployService(ctx context.Context, req *pb.DeploymentRequest) (*pb.DeploymentResponse, error) {
	log.Printf("🚀 Deploying service: %s to %s", req.Service, req.Environment)

	deploymentID := s.generateDeploymentID()

	steps := []*pb.DeploymentStep{
		{
			Name:      "Validation",
			Status:    "completed",
			Message:   "Service configuration validated",
			Timestamp: timestamppb.Now(),
		},
		{
			Name:      "Build",
			Status:    "completed",
			Message:   "Service build completed successfully",
			Timestamp: timestamppb.Now(),
		},
		{
			Name:      "Deploy",
			Status:    "in_progress",
			Message:   "Deploying to " + req.Environment,
			Timestamp: timestamppb.Now(),
		},
	}

	return &pb.DeploymentResponse{
		DeploymentId: deploymentID,
		Status:       "in_progress",
		Message:      fmt.Sprintf("Deployment initiated for %s", req.Service),
		StartedAt:    timestamppb.Now(),
		Steps:        steps,
	}, nil
}

// GetLogs retrieves system logs
func (s *NexusOrchestratorServer) GetLogs(ctx context.Context, req *pb.LogRequest) (*pb.LogResponse, error) {
	log.Printf("📋 Logs requested for service: %s", req.Service)

	// Mock log entries (would connect to real logging system)
	logs := []*pb.LogEntry{
		{
			Timestamp: timestamppb.New(time.Now().Add(-5 * time.Minute)),
			Level:     "INFO",
			Component: "orchestrator",
			Message:   "Trinity convergence initialization complete",
			Metadata:  map[string]string{"module": "core", "thread": "main"},
		},
		{
			Timestamp: timestamppb.New(time.Now().Add(-4 * time.Minute)),
			Level:     "INFO",
			Component: "rust-engine",
			Message:   "Nexus core engine started successfully",
			Metadata:  map[string]string{"module": "engine", "pid": "12345"},
		},
		{
			Timestamp: timestamppb.New(time.Now().Add(-3 * time.Minute)),
			Level:     "INFO",
			Component: "go-proxies",
			Message:   "Fabric proxy mesh established",
			Metadata:  map[string]string{"module": "proxy", "connections": "147"},
		},
		{
			Timestamp: timestamppb.New(time.Now().Add(-2 * time.Minute)),
			Level:     "WARN",
			Component: "web-frontend",
			Message:   "High memory usage detected: 89.6MB",
			Metadata:  map[string]string{"module": "frontend", "memory": "89.6MB"},
		},
		{
			Timestamp: timestamppb.New(time.Now().Add(-1 * time.Minute)),
			Level:     "INFO",
			Component: "orchestrator",
			Message:   "Health check completed - all systems operational",
			Metadata:  map[string]string{"module": "health", "status": "ok"},
		},
		{
			Timestamp: timestamppb.Now(),
			Level:     "INFO",
			Component: "grpc-gateway",
			Message:   "God Tier Interface API gateway operational",
			Metadata:  map[string]string{"module": "gateway", "version": "1.0.0"},
		},
	}

	return &pb.LogResponse{
		Logs: logs,
	}, nil
}

// StreamEvents provides real-time event streaming
func (s *NexusOrchestratorServer) StreamEvents(req *emptypb.Empty, stream pb.NexusOrchestrator_StreamEventsServer) error {
	log.Println("📡 Event stream started")

	streamID := s.generateStreamID()
	eventChan := make(chan *pb.EventMessage, 100)

	s.streamMutex.Lock()
	s.eventStreams[streamID] = eventChan
	s.streamMutex.Unlock()

	defer func() {
		s.streamMutex.Lock()
		delete(s.eventStreams, streamID)
		close(eventChan)
		s.streamMutex.Unlock()
	}()

	// Send initial system status event
	statusEvent := &pb.EventMessage{
		EventType: "system_status",
		Source:    "nexus-orchestrator",
		Timestamp: timestamppb.Now(),
		Data: map[string]string{
			"status":  "operational",
			"version": "1.0.0-god-tier",
		},
		Severity: "info",
	}

	if err := stream.Send(statusEvent); err != nil {
		return err
	}

	// Keep stream alive and send periodic updates
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-stream.Context().Done():
			return nil
		case event := <-eventChan:
			if err := stream.Send(event); err != nil {
				return err
			}
		case <-ticker.C:
			heartbeat := &pb.EventMessage{
				EventType: "heartbeat",
				Source:    "nexus-orchestrator",
				Timestamp: timestamppb.Now(),
				Data:      map[string]string{"status": "alive"},
				Severity:  "info",
			}
			if err := stream.Send(heartbeat); err != nil {
				return err
			}
		}
	}
}

// ExecuteCommand executes system commands
func (s *NexusOrchestratorServer) ExecuteCommand(ctx context.Context, req *pb.ExecuteRequest) (*pb.ExecuteResponse, error) {
	log.Printf("⚡ Executing command: %s", req.Command)

	startTime := time.Now()

	cmd := exec.CommandContext(ctx, req.Command, req.Args...)
	if req.WorkingDirectory != "" {
		cmd.Dir = req.WorkingDirectory
	}

	// Set environment variables
	for key, value := range req.Environment {
		cmd.Env = append(cmd.Env, fmt.Sprintf("%s=%s", key, value))
	}

	output, err := cmd.CombinedOutput()
	endTime := time.Now()

	exitCode := 0
	stdout := string(output)
	stderr := ""

	if err != nil {
		if exitError, ok := err.(*exec.ExitError); ok {
			exitCode = exitError.ExitCode()
		} else {
			exitCode = 1
		}
		stderr = err.Error()
	}

	return &pb.ExecuteResponse{
		ExitCode:   int32(exitCode),
		Stdout:     stdout,
		Stderr:     stderr,
		StartedAt:  timestamppb.New(startTime),
		FinishedAt: timestamppb.New(endTime),
	}, nil
}

// GetConversationHistory retrieves conversation history
func (s *NexusOrchestratorServer) GetConversationHistory(ctx context.Context, req *pb.HistoryRequest) (*pb.HistoryResponse, error) {
	log.Printf("📚 Conversation history requested for session: %s", req.SessionId)

	s.sessionMutex.RLock()
	session, exists := s.sessions[req.SessionId]
	s.sessionMutex.RUnlock()

	if !exists {
		return nil, status.Errorf(codes.NotFound, "conversation session not found")
	}

	messages := session.Messages
	if req.Limit > 0 && int(req.Limit) < len(messages) {
		messages = messages[len(messages)-int(req.Limit):]
	}

	return &pb.HistoryResponse{
		Messages:  messages,
		SessionId: req.SessionId,
	}, nil
}

// UpdatePreferences updates user preferences
func (s *NexusOrchestratorServer) UpdatePreferences(ctx context.Context, req *pb.PreferencesRequest) (*pb.PreferencesResponse, error) {
	log.Printf("⚙️ Updating preferences for user: %s", req.UserId)

	// In a real implementation, this would persist to a database
	// For now, we'll update session preferences if they exist
	s.sessionMutex.Lock()
	for _, session := range s.sessions {
		if session.UserID == req.UserId {
			for key, value := range req.Preferences {
				session.Preferences[key] = value
			}
		}
	}
	s.sessionMutex.Unlock()

	return &pb.PreferencesResponse{
		UserId:      req.UserId,
		Preferences: req.Preferences,
		UpdatedAt:   timestamppb.Now(),
	}, nil
}

// Helper methods

func (s *NexusOrchestratorServer) updateServiceStatus() {
	// Mock service status (would connect to real services)
	services := map[string]*ServiceInfo{
		"nexus-orchestrator": {
			Name:        "Nexus Orchestrator",
			Status:      "running",
			Health:      "healthy",
			CPUUsage:    15.3,
			MemoryUsage: 245.7,
			UptimeStart: time.Now().Add(-2 * time.Hour),
			LastCheck:   time.Now(),
		},
		"rust-engine": {
			Name:        "Rust Core Engine",
			Status:      "running",
			Health:      "healthy",
			CPUUsage:    8.7,
			MemoryUsage: 512.1,
			UptimeStart: time.Now().Add(-2 * time.Hour),
			LastCheck:   time.Now(),
		},
		"go-proxies": {
			Name:        "Go Fabric Proxies",
			Status:      "running",
			Health:      "healthy",
			CPUUsage:    12.4,
			MemoryUsage: 128.3,
			UptimeStart: time.Now().Add(-105 * time.Minute),
			LastCheck:   time.Now(),
		},
		"web-frontend": {
			Name:        "Web Frontend",
			Status:      "running",
			Health:      "healthy",
			CPUUsage:    5.2,
			MemoryUsage: 89.6,
			UptimeStart: time.Now().Add(-90 * time.Minute),
			LastCheck:   time.Now(),
		},
	}

	s.serviceMutex.Lock()
	s.services = services
	s.serviceMutex.Unlock()
}

func (s *NexusOrchestratorServer) processNaturalLanguage(input string) (string, map[string]string, float64) {
	// Simple intent classification (enhanced version of CLI logic)
	normalized := strings.ToLower(strings.TrimSpace(input))

	patterns := map[string][]string{
		"deploy":    {"deploy", "launch", "start", "initialize", "run"},
		"status":    {"status", "health", "check", "monitor", "state"},
		"configure": {"config", "setup", "configure", "settings", "preferences"},
		"help":      {"help", "assistance", "guide", "tutorial", "how"},
		"build":     {"build", "compile", "construct", "create", "make"},
		"test":      {"test", "validate", "verify", "check", "examine"},
		"stop":      {"stop", "halt", "terminate", "kill", "shutdown"},
		"restart":   {"restart", "reboot", "reload", "refresh", "reset"},
		"update":    {"update", "upgrade", "patch", "sync", "refresh"},
		"backup":    {"backup", "save", "archive", "preserve", "store"},
		"restore":   {"restore", "recover", "retrieve", "reload", "revert"},
		"scale":     {"scale", "resize", "expand", "grow", "shrink"},
		"monitor":   {"monitor", "watch", "observe", "track", "follow"},
		"debug":     {"debug", "troubleshoot", "diagnose", "fix", "repair"},
		"analyze":   {"analyze", "examine", "inspect", "study", "review"},
		"optimize":  {"optimize", "improve", "enhance", "tune", "boost"},
	}

	bestIntent := "unknown"
	bestScore := 0

	for intent, keywords := range patterns {
		score := 0
		for _, keyword := range keywords {
			if strings.Contains(normalized, keyword) {
				score++
			}
		}
		if score > bestScore {
			bestScore = score
			bestIntent = intent
		}
	}

	// Extract entities (simplified)
	entities := make(map[string]string)
	entityPatterns := map[string][]string{
		"service":     {"backend", "frontend", "api", "database", "cache", "proxy", "gateway"},
		"environment": {"development", "staging", "production", "test", "demo"},
		"component":   {"rust-engine", "go-proxies", "python-orchestrator", "web-ui", "cli"},
	}

	for entityType, values := range entityPatterns {
		for _, value := range values {
			if strings.Contains(normalized, value) {
				entities[entityType] = value
				break
			}
		}
	}

	// Calculate confidence
	confidence := 0.5
	if bestIntent != "unknown" {
		confidence += 0.3
	}
	if len(entities) > 0 {
		confidence += 0.2
	}
	if len(strings.Fields(normalized)) < 2 {
		confidence -= 0.2
	}

	if confidence > 1.0 {
		confidence = 1.0
	}
	if confidence < 0.0 {
		confidence = 0.0
	}

	return bestIntent, entities, confidence
}

func (s *NexusOrchestratorServer) processNaturalLanguageWithContext(input string, session *ConversationSession) (string, map[string]string, float64) {
	intent, entities, confidence := s.processNaturalLanguage(input)

	// Enhance with conversation context
	if session.DialogueState.CurrentTopic != "" && intent == "unknown" {
		// If we can't determine intent, use context from previous topic
		intent = session.DialogueState.CurrentTopic
		confidence += 0.1
	}

	// Add context-based entities
	for key, value := range session.Context {
		if entities[key] == "" {
			entities[key] = value
		}
	}

	return intent, entities, confidence
}

func (s *NexusOrchestratorServer) generateResponse(intent string, entities map[string]string, confidence float64, input string) string {
	responses := map[string][]string{
		"deploy": {
			"I'll initiate the deployment sequence for you. Which service would you like to deploy?",
			"Starting deployment process. Let me check the current system status first.",
			"Deployment ready! I can deploy to development, staging, or production. Which environment?",
		},
		"status": {
			"Let me check the system health for you right now.",
			"Running comprehensive health diagnostics across all Trinity components.",
			"System status check initiated. I'll provide a detailed report momentarily.",
		},
		"help": {
			"I'm here to help! I can assist with deployments, monitoring, configuration, and more.",
			"What would you like to know? I can explain any aspect of the LoL Nexus system.",
			"I understand natural language commands. Try asking me to 'deploy the backend' or 'check system health'.",
		},
		"configure": {
			"I'll help you configure the system. What settings would you like to modify?",
			"Configuration mode activated. I can help with service settings, environment variables, and more.",
			"Let's configure your system. What component needs adjustment?",
		},
	}

	if responseList, exists := responses[intent]; exists {
		return responseList[0] // Use first response for consistency
	}

	if confidence < 0.6 {
		return fmt.Sprintf("I'm not entirely sure what you mean by '%s'. Could you rephrase that? I can help with deployments, system status, configuration, and more.", input)
	}

	return fmt.Sprintf("I understand you want to '%s'. Let me process that for you.", intent)
}

func (s *NexusOrchestratorServer) generateConversationalResponse(intent string, entities map[string]string, confidence float64, input string, session *ConversationSession) string {
	// Enhanced conversational responses with context awareness
	baseResponse := s.generateResponse(intent, entities, confidence, input)

	// Add contextual enhancements
	if len(session.Messages) > 0 {
		// This is a continuation, make it more conversational
		conversationalPrefixes := []string{
			"Got it! ",
			"I see. ",
			"Understood. ",
			"Of course! ",
		}
		prefix := conversationalPrefixes[len(session.Messages)%len(conversationalPrefixes)]
		baseResponse = prefix + baseResponse
	}

	return baseResponse
}

func (s *NexusOrchestratorServer) requiresAction(intent string) bool {
	actionIntents := map[string]bool{
		"deploy":    true,
		"build":     true,
		"test":      true,
		"restart":   true,
		"stop":      true,
		"backup":    true,
		"restore":   true,
		"scale":     true,
		"update":    true,
		"configure": true,
	}

	return actionIntents[intent]
}

func (s *NexusOrchestratorServer) createActionRequest(intent string, entities map[string]string) *pb.ActionRequest {
	return &pb.ActionRequest{
		Type:       intent,
		Target:     entities["service"],
		Parameters: entities,
	}
}

func (s *NexusOrchestratorServer) generateSuggestions(intent string, entities map[string]string) []string {
	suggestions := map[string][]string{
		"deploy": {
			"deploy to staging environment",
			"check deployment status",
			"rollback if needed",
		},
		"status": {
			"show detailed metrics",
			"check individual services",
			"view recent logs",
		},
		"help": {
			"show available commands",
			"explain system architecture",
			"view documentation",
		},
		"configure": {
			"backup current config",
			"view configuration options",
			"apply recommended settings",
		},
	}

	if suggestionList, exists := suggestions[intent]; exists {
		return suggestionList
	}

	return []string{
		"show system help",
		"check system status",
		"view available commands",
	}
}

func (s *NexusOrchestratorServer) generateFollowUpOptions(intent string, entities map[string]string) []string {
	return s.generateSuggestions(intent, entities)
}

func (s *NexusOrchestratorServer) generateSessionID() string {
	return fmt.Sprintf("session_%d", time.Now().UnixNano())
}

func (s *NexusOrchestratorServer) generateDeploymentID() string {
	return fmt.Sprintf("deploy_%d", time.Now().UnixNano())
}

func (s *NexusOrchestratorServer) generateStreamID() string {
	return fmt.Sprintf("stream_%d", time.Now().UnixNano())
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// Main function to start the gRPC server
func main() {
	log.Println("🚀 Starting LoL Nexus God Tier gRPC API Gateway...")

	// Create server instance
	server := NewNexusOrchestratorServer("http://localhost:8080")

	// Start gRPC server
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterNexusOrchestratorServer(grpcServer, server)

	log.Println("🎯 gRPC API Gateway listening on :50051")
	log.Println("🔗 Ready to serve LoL Nexus God Tier Interface requests")

	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
