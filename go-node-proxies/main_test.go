package main

import (
	"context"
	"testing"
	"time"

	"github.com/omnimesh/go-node-proxies/internal/fabricpb"
	"google.golang.org/grpc"
)

func TestGCNPRegistrationAndStatus(t *testing.T) {
	addr := "localhost:50051" // Assumes Nexus Prime is running locally for test
	conn, err := grpc.Dial(addr, grpc.WithInsecure(), grpc.WithBlock(), grpc.WithTimeout(2*time.Second))
	if err != nil {
		t.Skipf("Could not connect to Nexus Prime: %v", err)
	}
	defer conn.Close()

	client := fabricpb.NewFabricServiceClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	req := &fabricpb.AgentRegistrationRequest{
		AgentType:    fabricpb.AgentType_AGENT_TYPE_PC,
		IpAddress:    "127.0.0.1",
		Capabilities: "cpu:4,ram:16GB,gpu:0",
	}
	resp, err := client.RegisterAgent(ctx, req)
	if err != nil {
		t.Errorf("RegisterAgent failed: %v", err)
	}
	if resp != nil && resp.NodeId == "" {
		t.Errorf("Expected non-empty NodeId in response")
	}

	statusReq := &fabricpb.AgentStatusUpdate{
		NodeId:      resp.NodeId,
		StatusType:  fabricpb.StatusType_STATUS_TYPE_NODE,
		StatusValue: "Online",
	}
	_, err = client.UpdateAgentStatus(ctx, statusReq)
	if err != nil {
		t.Errorf("UpdateAgentStatus failed: %v", err)
	}
}
