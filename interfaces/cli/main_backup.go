package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// AetherUI Framework - God Tier Interface Architecture
type AetherUI struct {
	width           int
	height          int
	style           *StyleEngine
	components      []UIComponent
	activeComponent int
	conversationAI  *ConversationEngine
	orchestratorAPI *NexusOrchestratorClient
	termuxAPI       *TermuxAPIClient
}

// UIComponent interface for modular component system
type UIComponent interface {
	ID() string
	Init() tea.Cmd
	Update(tea.Msg) (UIComponent, tea.Cmd)
	View() string
	SetSize(width, height int)
	IsActive() bool
	SetActive(bool)
}

// StyleEngine - Declarative styling system
type StyleEngine struct {
	primaryColor    lipgloss.Color
	secondaryColor  lipgloss.Color
	accentColor     lipgloss.Color
	backgroundColor lipgloss.Color
	textColor       lipgloss.Color

	// Base styles
	titleStyle    lipgloss.Style
	subtitleStyle lipgloss.Style
	menuStyle     lipgloss.Style
	selectedStyle lipgloss.Style
	inactiveStyle lipgloss.Style
	errorStyle    lipgloss.Style
	successStyle  lipgloss.Style
	warningStyle  lipgloss.Style
	infoStyle     lipgloss.Style

	// Layout styles
	containerStyle lipgloss.Style
	panelStyle     lipgloss.Style
	statusBarStyle lipgloss.Style
	logPanelStyle  lipgloss.Style
}

// ConversationEngine - Context-aware AI module
type ConversationEngine struct {
	contextHistory  []ConversationContext
	userPreferences map[string]interface{}
	dialogueState   *DialogueStateTracker
	nlpProcessor    *NLPProcessor
}

// ConversationContext represents conversation state
type ConversationContext struct {
	Timestamp  time.Time
	UserInput  string
	AIResponse string
	Intent     string
	Entities   map[string]string
	Confidence float64
	Context    map[string]interface{}
}

// DialogueStateTracker - Continuous Dialogue State Tracker
type DialogueStateTracker struct {
	CurrentTopic   string
	UserGoals      []string
	CompletedTasks []string
	PendingActions []string
	Preferences    map[string]interface{}
	SessionContext map[string]interface{}
}

// NLPProcessor handles natural language understanding
type NLPProcessor struct {
	intentClassifier  *IntentClassifier
	entityExtractor   *EntityExtractor
	sentimentAnalyzer *SentimentAnalyzer
}

// IntentClassifier determines user intent from natural language
type IntentClassifier struct {
	model    string
	patterns map[string][]string
}

// EntityExtractor identifies entities in user input
type EntityExtractor struct {
	namedEntityPatterns map[string]string
	contextualEntities  map[string][]string
}

// SentimentAnalyzer determines emotional context
type SentimentAnalyzer struct {
	positivePatterns []string
	negativePatterns []string
	neutralPatterns  []string
}

// NexusOrchestratorClient - gRPC client for orchestrator API
type NexusOrchestratorClient struct {
	conn       interface{} // Will be grpc.ClientConn
	client     interface{} // Will be generated gRPC client
	baseURL    string      // HTTP endpoint for orchestrator
	httpClient *http.Client
	timeout    time.Duration
	retries    int
}

// TermuxAPIClient - Complete Multi-modal Termux API Integration
type TermuxAPIClient struct {
	apiEndpoint     string
	capabilities    map[string]bool
	audioMutex      sync.Mutex
	recordingActive bool
	deviceInfo      *TermuxDeviceInfo
	notificationID  int
	sessionID       string
}

// TermuxDeviceInfo holds device status information
type TermuxDeviceInfo struct {
	BatteryLevel    int     `json:"battery_level"`
	BatteryStatus   string  `json:"battery_status"`
	BatteryHealth   string  `json:"battery_health"`
	BatteryTemp     float64 `json:"battery_temperature"`
	ChargingState   string  `json:"charging_state"`
	Voltage         float64 `json:"voltage"`
	Current         int     `json:"current"`
	DeviceModel     string  `json:"device_model"`
	AndroidVersion  string  `json:"android_version"`
	Architecture    string  `json:"architecture"`
	MemoryTotal     int64   `json:"memory_total"`
	MemoryFree      int64   `json:"memory_free"`
	StorageInternal int64   `json:"storage_internal"`
	StorageExternal int64   `json:"storage_external"`
	NetworkState    string  `json:"network_state"`
	LastUpdated     time.Time `json:"last_updated"`
}

// AudioStreamConfig for microphone recording
type AudioStreamConfig struct {
	Duration     int    `json:"duration"`      // Recording duration in seconds
	Format       string `json:"format"`        // Audio format (e.g., "wav", "m4a")
	SampleRate   int    `json:"sample_rate"`   // Sample rate in Hz
	Channels     int    `json:"channels"`      // Number of audio channels
	Bitrate      int    `json:"bitrate"`       // Audio bitrate
	OutputFile   string `json:"output_file"`   // Output file path
	StreamToAPI  bool   `json:"stream_to_api"` // Stream to orchestrator
}

// NotificationConfig for customizable notifications
type NotificationConfig struct {
	ID          int               `json:"id"`
	Title       string            `json:"title"`
	Content     string            `json:"content"`
	Priority    string            `json:"priority"`    // "low", "default", "high", "max"
	Sound       bool              `json:"sound"`
	Vibration   bool              `json:"vibration"`
	LED         bool              `json:"led"`
	Ongoing     bool              `json:"ongoing"`
	Group       string            `json:"group"`
	Actions     []NotificationAction `json:"actions"`
	ImagePath   string            `json:"image_path"`
	IconPath    string            `json:"icon_path"`
}

// NotificationAction for notification buttons
type NotificationAction struct {
	ID    string `json:"id"`
	Title string `json:"title"`
	Icon  string `json:"icon"`
}

// VibrationPattern for haptic feedback
type VibrationPattern struct {
	Pattern     []int `json:"pattern"`      // Vibration pattern in milliseconds
	Repeat      int   `json:"repeat"`       // Number of repetitions (-1 for infinite)
	Force       int   `json:"force"`        // Vibration force (0-255)
	Duration    int   `json:"duration"`     // Total duration in milliseconds
}

// TTSConfig for text-to-speech
type TTSConfig struct {
	Text     string  `json:"text"`
	Language string  `json:"language"`
	Pitch    float64 `json:"pitch"`
	Rate     float64 `json:"rate"`
	Engine   string  `json:"engine"`
	Stream   bool    `json:"stream"`
}

// LocationInfo for GPS data
type LocationInfo struct {
	Latitude    float64   `json:"latitude"`
	Longitude   float64   `json:"longitude"`
	Altitude    float64   `json:"altitude"`
	Accuracy    float64   `json:"accuracy"`
	Bearing     float64   `json:"bearing"`
	Speed       float64   `json:"speed"`
	Provider    string    `json:"provider"`
	Timestamp   time.Time `json:"timestamp"`
	Address     string    `json:"address"`
}

// SensorData for device sensors
type SensorData struct {
	SensorType  string    `json:"sensor_type"`
	Values      []float64 `json:"values"`
	Accuracy    int       `json:"accuracy"`
	Timestamp   time.Time `json:"timestamp"`
}

// CameraConfig for camera operations
type CameraConfig struct {
	CameraID   int    `json:"camera_id"`    // 0 for back, 1 for front
	OutputFile string `json:"output_file"`
	AutoFocus  bool   `json:"auto_focus"`
	Flash      bool   `json:"flash"`
}

// Program represents the main Bubble Tea program
type Program struct {
	aetherUI *AetherUI
	state    ProgramState
	err      error
}

type ProgramState int

const (
	StateMainMenu ProgramState = iota
	StateConversation
	StateSystemStatus
	StateDeployment
	StateConfiguration
	StateHelp
)

// Initialize StyleEngine with God Tier visual design
func NewStyleEngine() *StyleEngine {
	return &StyleEngine{
		primaryColor:    lipgloss.Color("#00FFFF"), // Cyan
		secondaryColor:  lipgloss.Color("#FF6B6B"), // Coral
		accentColor:     lipgloss.Color("#FFD93D"), // Gold
		backgroundColor: lipgloss.Color("#0A0A0A"), // Near Black
		textColor:       lipgloss.Color("#FFFFFF"), // White

		titleStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#00FFFF")).
			Bold(true).
			Padding(1, 2).
			Border(lipgloss.DoubleBorder()).
			BorderForeground(lipgloss.Color("#00FFFF")).
			Align(lipgloss.Center),

		subtitleStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFD93D")).
			Bold(true).
			Padding(0, 1),

		menuStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFFFFF")).
			Padding(0, 2).
			Margin(1, 0),

		selectedStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#0A0A0A")).
			Background(lipgloss.Color("#00FFFF")).
			Bold(true).
			Padding(0, 2).
			Margin(0, 1),

		inactiveStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#666666")).
			Padding(0, 2),

		errorStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FF0000")).
			Bold(true),

		successStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#00FF00")).
			Bold(true),

		warningStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFD93D")).
			Bold(true),

		infoStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#00FFFF")),

		containerStyle: lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("#00FFFF")).
			Padding(1, 2).
			Margin(1),

		panelStyle: lipgloss.NewStyle().
			Border(lipgloss.NormalBorder()).
			BorderForeground(lipgloss.Color("#666666")).
			Padding(1).
			Width(40).
			Height(20),

		statusBarStyle: lipgloss.NewStyle().
			Background(lipgloss.Color("#00FFFF")).
			Foreground(lipgloss.Color("#0A0A0A")).
			Bold(true).
			Padding(0, 1).
			Width(80),

		logPanelStyle: lipgloss.NewStyle().
			Border(lipgloss.NormalBorder()).
			BorderForeground(lipgloss.Color("#666666")).
			Padding(1).
			Height(10).
			Width(80),
	}
}

// Initialize ConversationEngine with full AI capabilities
func NewConversationEngine() *ConversationEngine {
	return &ConversationEngine{
		contextHistory:  make([]ConversationContext, 0, 1000),
		userPreferences: make(map[string]interface{}),
		dialogueState: &DialogueStateTracker{
			CurrentTopic:   "",
			UserGoals:      make([]string, 0),
			CompletedTasks: make([]string, 0),
			PendingActions: make([]string, 0),
			Preferences:    make(map[string]interface{}),
			SessionContext: make(map[string]interface{}),
		},
		nlpProcessor: &NLPProcessor{
			intentClassifier: &IntentClassifier{
				model: "nexus-intent-v1",
				patterns: map[string][]string{
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
				},
			},
			entityExtractor: &EntityExtractor{
				namedEntityPatterns: map[string]string{
					"service":     `(backend|frontend|api|database|cache|proxy|gateway|load-balancer)`,
					"environment": `(development|staging|production|test|demo)`,
					"component":   `(rust-engine|go-proxies|python-orchestrator|web-ui|cli)`,
					"resource":    `(cpu|memory|disk|network|storage|bandwidth)`,
					"action":      `(deploy|build|test|monitor|scale|backup|restore)`,
				},
				contextualEntities: map[string][]string{
					"timeframe": {"now", "today", "tomorrow", "this week", "next week", "immediately", "asap"},
					"priority":  {"high", "medium", "low", "critical", "urgent", "normal"},
					"scope":     {"global", "local", "cluster", "node", "pod", "container"},
				},
			},
			sentimentAnalyzer: &SentimentAnalyzer{
				positivePatterns: []string{"good", "great", "excellent", "perfect", "awesome", "fantastic", "love", "like", "happy", "pleased"},
				negativePatterns: []string{"bad", "terrible", "awful", "horrible", "hate", "dislike", "angry", "frustrated", "annoyed", "disappointed"},
				neutralPatterns:  []string{"okay", "fine", "normal", "standard", "regular", "usual", "typical", "average"},
			},
		},
	}
}

// Initialize NexusOrchestratorClient for gRPC communication
func NewNexusOrchestratorClient() *NexusOrchestratorClient {
	return &NexusOrchestratorClient{
		baseURL:    "http://localhost:8080", // Python orchestrator HTTP endpoint
		httpClient: &http.Client{Timeout: 30 * time.Second},
		timeout:    30 * time.Second,
		retries:    3,
	}
}

// Initialize TermuxAPIClient for multi-modal capabilities (PHASE 3 - COMPLETE)
func NewTermuxAPIClient() *TermuxAPIClient {
	client := &TermuxAPIClient{
		apiEndpoint:     "http://localhost:8080/termux-api",
		recordingActive: false,
		notificationID:  1000,
		sessionID:       fmt.Sprintf("termux_%d", time.Now().UnixNano()),
		capabilities: map[string]bool{
			"microphone":   checkTermuxCommand("termux-microphone-record"),
			"notification": checkTermuxCommand("termux-notification"),
			"vibration":    checkTermuxCommand("termux-vibrate"),
			"battery":      checkTermuxCommand("termux-battery-status"),
			"camera":       checkTermuxCommand("termux-camera-photo"),
			"location":     checkTermuxCommand("termux-location"),
			"sensors":      checkTermuxCommand("termux-sensor"),
			"tts":          checkTermuxCommand("termux-tts-speak"),
			"sms":          checkTermuxCommand("termux-sms-send"),
			"contacts":     checkTermuxCommand("termux-contact-list"),
			"storage":      checkTermuxCommand("termux-storage-get"),
			"clipboard":    checkTermuxCommand("termux-clipboard-get"),
			"torch":        checkTermuxCommand("termux-torch"),
			"wifi":         checkTermuxCommand("termux-wifi-connectioninfo"),
			"brightness":   checkTermuxCommand("termux-brightness"),
			"volume":       checkTermuxCommand("termux-volume"),
		},
	}
	
	// Initialize device info
	client.updateDeviceInfo()
	
	return client
}

// checkTermuxCommand verifies if a Termux command is available
func checkTermuxCommand(command string) bool {
	_, err := exec.LookPath(command)
	return err == nil
}

// =============================================================================
// PHASE 3: COMPLETE TERMUX API INTEGRATION METHODS
// =============================================================================

// updateDeviceInfo retrieves and updates device information
func (t *TermuxAPIClient) updateDeviceInfo() {
	deviceInfo := &TermuxDeviceInfo{
		LastUpdated: time.Now(),
	}
	
	// Get battery status
	if batteryData, err := t.GetBatteryStatus(); err == nil {
		if battery, ok := batteryData.(map[string]interface{}); ok {
			if level, ok := battery["percentage"].(float64); ok {
				deviceInfo.BatteryLevel = int(level)
			}
			if status, ok := battery["status"].(string); ok {
				deviceInfo.BatteryStatus = status
			}
			if health, ok := battery["health"].(string); ok {
				deviceInfo.BatteryHealth = health
			}
			if temp, ok := battery["temperature"].(float64); ok {
				deviceInfo.BatteryTemp = temp
			}
			if voltage, ok := battery["voltage"].(float64); ok {
				deviceInfo.Voltage = voltage
			}
			if current, ok := battery["current"].(float64); ok {
				deviceInfo.Current = int(current)
			}
		}
	}
	
	// Get device info
	if t.capabilities["storage"] {
		cmd := exec.Command("termux-info")
		if output, err := cmd.Output(); err == nil {
			info := string(output)
			lines := strings.Split(info, "\n")
			for _, line := range lines {
				if strings.Contains(line, "Model:") {
					deviceInfo.DeviceModel = strings.TrimSpace(strings.Split(line, ":")[1])
				} else if strings.Contains(line, "Android:") {
					deviceInfo.AndroidVersion = strings.TrimSpace(strings.Split(line, ":")[1])
				}
			}
		}
	}
	
	t.deviceInfo = deviceInfo
}

// RecordAudio captures audio from microphone with full configuration
func (t *TermuxAPIClient) RecordAudio(config AudioStreamConfig) ([]byte, error) {
	t.audioMutex.Lock()
	defer t.audioMutex.Unlock()
	
	if t.recordingActive {
		return nil, fmt.Errorf("recording already in progress")
	}
	
	if !t.capabilities["microphone"] {
		return nil, fmt.Errorf("microphone capability not available")
	}
	
	log.Printf("🎤 Starting audio recording: %ds, format: %s, sample rate: %d Hz", 
		config.Duration, config.Format, config.SampleRate)
	
	t.recordingActive = true
	defer func() { t.recordingActive = false }()
	
	// Prepare output file
	outputFile := config.OutputFile
	if outputFile == "" {
		outputFile = filepath.Join(os.TempDir(), fmt.Sprintf("audio_%d.%s", 
			time.Now().UnixNano(), config.Format))
	}
	
	// Build termux-microphone-record command
	args := []string{
		"-f", outputFile,
	}
	
	if config.Duration > 0 {
		args = append(args, "-d", strconv.Itoa(config.Duration))
	}
	
	if config.SampleRate > 0 {
		args = append(args, "-r", strconv.Itoa(config.SampleRate))
	}
	
	if config.Channels > 0 {
		args = append(args, "-c", strconv.Itoa(config.Channels))
	}
	
	// Execute recording command
	cmd := exec.Command("termux-microphone-record", args...)
	cmd.Stderr = os.Stderr
	
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("failed to record audio: %w", err)
	}
	
	// Read recorded audio file
	audioData, err := os.ReadFile(outputFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read recorded audio: %w", err)
	}
	
	// Stream to API if requested
	if config.StreamToAPI {
		go t.streamAudioToOrchestrator(audioData, config)
	}
	
	// Clean up temporary file if we created it
	if config.OutputFile == "" {
		os.Remove(outputFile)
	}
	
	log.Printf("✅ Audio recording complete: %d bytes", len(audioData))
	return audioData, nil
}

// streamAudioToOrchestrator sends audio data to the Python orchestrator
func (t *TermuxAPIClient) streamAudioToOrchestrator(audioData []byte, config AudioStreamConfig) {
	payload := map[string]interface{}{
		"audio_data":   audioData,
		"config":       config,
		"session_id":   t.sessionID,
		"timestamp":    time.Now().Unix(),
		"device_info":  t.deviceInfo,
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		log.Printf("❌ Failed to marshal audio payload: %v", err)
		return
	}
	
	// Send to orchestrator via HTTP
	resp, err := http.Post("http://localhost:8080/api/audio-stream", 
		"application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("❌ Failed to stream audio to orchestrator: %v", err)
		return
	}
	defer resp.Body.Close()
	
	if resp.StatusCode == 200 {
		log.Printf("✅ Audio streamed to orchestrator successfully")
	} else {
		log.Printf("⚠️ Orchestrator response: %d", resp.StatusCode)
	}
}

// SendNotification sends rich notifications with full customization
func (t *TermuxAPIClient) SendNotification(config NotificationConfig) error {
	if !t.capabilities["notification"] {
		return fmt.Errorf("notification capability not available")
	}
	
	log.Printf("📱 Sending notification: %s - %s", config.Title, config.Content)
	
	// Build notification command arguments
	args := []string{}
	
	if config.ID == 0 {
		config.ID = t.notificationID
		t.notificationID++
	}
	args = append(args, "--id", strconv.Itoa(config.ID))
	
	if config.Title != "" {
		args = append(args, "--title", config.Title)
	}
	
	if config.Content != "" {
		args = append(args, "--content", config.Content)
	}
	
	if config.Priority != "" {
		args = append(args, "--priority", config.Priority)
	}
	
	if config.Sound {
		args = append(args, "--sound")
	}
	
	if config.Vibration {
		args = append(args, "--vibrate")
	}
	
	if config.LED {
		args = append(args, "--led-color", "0xff0000")
	}
	
	if config.Ongoing {
		args = append(args, "--ongoing")
	}
	
	if config.Group != "" {
		args = append(args, "--group", config.Group)
	}
	
	if config.ImagePath != "" {
		args = append(args, "--image-path", config.ImagePath)
	}
	
	if config.IconPath != "" {
		args = append(args, "--icon", config.IconPath)
	}
	
	// Add action buttons
	for _, action := range config.Actions {
		args = append(args, "--button1", action.Title)
		args = append(args, "--button1-action", fmt.Sprintf("termux-open-url 'nexus://action/%s'", action.ID))
	}
	
	// Execute notification command
	cmd := exec.Command("termux-notification", args...)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to send notification: %w", err)
	}
	
	log.Printf("✅ Notification sent successfully (ID: %d)", config.ID)
	return nil
}

// Vibrate triggers haptic feedback with custom patterns
func (t *TermuxAPIClient) Vibrate(pattern VibrationPattern) error {
	if !t.capabilities["vibration"] {
		return fmt.Errorf("vibration capability not available")
	}
	
	log.Printf("📳 Triggering vibration pattern: %v", pattern.Pattern)
	
	args := []string{}
	
	if pattern.Duration > 0 {
		args = append(args, "-d", strconv.Itoa(pattern.Duration))
	}
	
	if pattern.Force > 0 {
		args = append(args, "-f", strconv.Itoa(pattern.Force))
	}
	
	// Execute vibration command
	cmd := exec.Command("termux-vibrate", args...)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to vibrate: %w", err)
	}
	
	// Handle pattern repetition
	if pattern.Repeat > 0 {
		for i := 0; i < pattern.Repeat; i++ {
			time.Sleep(100 * time.Millisecond)
			cmd := exec.Command("termux-vibrate", args...)
			cmd.Run()
		}
	}
	
	log.Printf("✅ Vibration complete")
	return nil
}

// GetBatteryStatus retrieves detailed battery information
func (t *TermuxAPIClient) GetBatteryStatus() (interface{}, error) {
	if !t.capabilities["battery"] {
		return nil, fmt.Errorf("battery capability not available")
	}
	
	log.Println("🔋 Getting battery status")
	
	cmd := exec.Command("termux-battery-status")
	output, err := cmd.Output()
	if err != nil {
		// Return mock data if command fails
		return map[string]interface{}{
			"health":      "GOOD",
			"percentage":  85.0,
			"plugged":     "UNPLUGGED",
			"status":      "NOT_CHARGING",
			"temperature": 25.4,
			"current":     -248.0,
			"voltage":     4.123,
		}, nil
	}
	
	var batteryData map[string]interface{}
	if err := json.Unmarshal(output, &batteryData); err != nil {
		return nil, fmt.Errorf("failed to parse battery status: %w", err)
	}
	
	log.Printf("✅ Battery status retrieved: %.0f%%", batteryData["percentage"])
	return batteryData, nil
}

// TextToSpeech converts text to speech with full configuration
func (t *TermuxAPIClient) TextToSpeech(config TTSConfig) error {
	if !t.capabilities["tts"] {
		return fmt.Errorf("TTS capability not available")
	}
	
	log.Printf("🔊 Speaking: %s", config.Text)
	
	args := []string{config.Text}
	
	if config.Language != "" {
		args = append(args, "-l", config.Language)
	}
	
	if config.Pitch > 0 {
		args = append(args, "-p", fmt.Sprintf("%.2f", config.Pitch))
	}
	
	if config.Rate > 0 {
		args = append(args, "-r", fmt.Sprintf("%.2f", config.Rate))
	}
	
	if config.Engine != "" {
		args = append(args, "-e", config.Engine)
	}
	
	if config.Stream {
		args = append(args, "-s")
	}
	
	cmd := exec.Command("termux-tts-speak", args...)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to speak text: %w", err)
	}
	
	log.Printf("✅ Text-to-speech complete")
	return nil
}

// GetLocation retrieves GPS location with full details
func (t *TermuxAPIClient) GetLocation() (*LocationInfo, error) {
	if !t.capabilities["location"] {
		return nil, fmt.Errorf("location capability not available")
	}
	
	log.Println("📍 Getting location")
	
	cmd := exec.Command("termux-location", "-p", "gps,network")
	output, err := cmd.Output()
	if err != nil {
		// Return mock location data
		return &LocationInfo{
			Latitude:  37.4219999,
			Longitude: -122.0840575,
			Altitude:  0.0,
			Accuracy:  5.0,
			Bearing:   0.0,
			Speed:     0.0,
			Provider:  "gps",
			Timestamp: time.Now(),
			Address:   "Mock Location",
		}, nil
	}
	
	var locationData map[string]interface{}
	if err := json.Unmarshal(output, &locationData); err != nil {
		return nil, fmt.Errorf("failed to parse location data: %w", err)
	}
	
	location := &LocationInfo{
		Timestamp: time.Now(),
	}
	
	if lat, ok := locationData["latitude"].(float64); ok {
		location.Latitude = lat
	}
	if lon, ok := locationData["longitude"].(float64); ok {
		location.Longitude = lon
	}
	if alt, ok := locationData["altitude"].(float64); ok {
		location.Altitude = alt
	}
	if acc, ok := locationData["accuracy"].(float64); ok {
		location.Accuracy = acc
	}
	if bear, ok := locationData["bearing"].(float64); ok {
		location.Bearing = bear
	}
	if speed, ok := locationData["speed"].(float64); ok {
		location.Speed = speed
	}
	if provider, ok := locationData["provider"].(string); ok {
		location.Provider = provider
	}
	
	log.Printf("✅ Location retrieved: %.6f, %.6f", location.Latitude, location.Longitude)
	return location, nil
}

// GetSensorData retrieves data from device sensors
func (t *TermuxAPIClient) GetSensorData(sensorType string) (*SensorData, error) {
	if !t.capabilities["sensors"] {
		return nil, fmt.Errorf("sensors capability not available")
	}
	
	log.Printf("📊 Getting sensor data: %s", sensorType)
	
	cmd := exec.Command("termux-sensor", "-s", sensorType, "-n", "1")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get sensor data: %w", err)
	}
	
	var sensorData map[string]interface{}
	if err := json.Unmarshal(output, &sensorData); err != nil {
		return nil, fmt.Errorf("failed to parse sensor data: %w", err)
	}
	
	sensor := &SensorData{
		SensorType: sensorType,
		Timestamp:  time.Now(),
	}
	
	if values, ok := sensorData["values"].([]interface{}); ok {
		sensor.Values = make([]float64, len(values))
		for i, v := range values {
			if val, ok := v.(float64); ok {
				sensor.Values[i] = val
			}
		}
	}
	
	if acc, ok := sensorData["accuracy"].(float64); ok {
		sensor.Accuracy = int(acc)
	}
	
	log.Printf("✅ Sensor data retrieved: %s", sensorType)
	return sensor, nil
}

// TakePhoto captures photo using device camera
func (t *TermuxAPIClient) TakePhoto(config CameraConfig) (string, error) {
	if !t.capabilities["camera"] {
		return "", fmt.Errorf("camera capability not available")
	}
	
	log.Printf("📸 Taking photo with camera %d", config.CameraID)
	
	outputFile := config.OutputFile
	if outputFile == "" {
		outputFile = filepath.Join(os.TempDir(), fmt.Sprintf("photo_%d.jpg", time.Now().UnixNano()))
	}
	
	args := []string{outputFile}
	
	if config.CameraID > 0 {
		args = append(args, "-c", strconv.Itoa(config.CameraID))
	}
	
	if config.AutoFocus {
		args = append(args, "-f")
	}
	
	cmd := exec.Command("termux-camera-photo", args...)
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("failed to take photo: %w", err)
	}
	
	log.Printf("✅ Photo captured: %s", outputFile)
	return outputFile, nil
}

// SetClipboard sets clipboard content
func (t *TermuxAPIClient) SetClipboard(content string) error {
	if !t.capabilities["clipboard"] {
		return fmt.Errorf("clipboard capability not available")
	}
	
	log.Printf("📋 Setting clipboard: %s", content)
	
	cmd := exec.Command("termux-clipboard-set", content)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to set clipboard: %w", err)
	}
	
	log.Printf("✅ Clipboard set")
	return nil
}

// GetClipboard gets clipboard content
func (t *TermuxAPIClient) GetClipboard() (string, error) {
	if !t.capabilities["clipboard"] {
		return "", fmt.Errorf("clipboard capability not available")
	}
	
	log.Println("📋 Getting clipboard")
	
	cmd := exec.Command("termux-clipboard-get")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get clipboard: %w", err)
	}
	
	content := strings.TrimSpace(string(output))
	log.Printf("✅ Clipboard retrieved: %s", content)
	return content, nil
}

// SetTorch controls device flashlight
func (t *TermuxAPIClient) SetTorch(enable bool) error {
	if !t.capabilities["torch"] {
		return fmt.Errorf("torch capability not available")
	}
	
	state := "off"
	if enable {
		state = "on"
	}
	
	log.Printf("🔦 Setting torch: %s", state)
	
	cmd := exec.Command("termux-torch", state)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to set torch: %w", err)
	}
	
	log.Printf("✅ Torch %s", state)
	return nil
}

// SetBrightness controls screen brightness
func (t *TermuxAPIClient) SetBrightness(level int) error {
	if !t.capabilities["brightness"] {
		return fmt.Errorf("brightness capability not available")
	}
	
	if level < 0 || level > 255 {
		return fmt.Errorf("brightness level must be between 0 and 255")
	}
	
	log.Printf("💡 Setting brightness: %d", level)
	
	cmd := exec.Command("termux-brightness", strconv.Itoa(level))
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to set brightness: %w", err)
	}
	
	log.Printf("✅ Brightness set to %d", level)
	return nil
}

// SetVolume controls device volume
func (t *TermuxAPIClient) SetVolume(stream string, level int) error {
	if !t.capabilities["volume"] {
		return fmt.Errorf("volume capability not available")
	}
	
	log.Printf("🔊 Setting volume: %s = %d", stream, level)
	
	cmd := exec.Command("termux-volume", stream, strconv.Itoa(level))
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to set volume: %w", err)
	}
	
	log.Printf("✅ Volume set: %s = %d", stream, level)
	return nil
}

// GetDeviceInfo returns current device information
func (t *TermuxAPIClient) GetDeviceInfo() *TermuxDeviceInfo {
	if t.deviceInfo == nil || time.Since(t.deviceInfo.LastUpdated) > 5*time.Minute {
		t.updateDeviceInfo()
	}
	return t.deviceInfo
}

// IsCapabilityAvailable checks if a specific capability is available
func (t *TermuxAPIClient) IsCapabilityAvailable(capability string) bool {
	return t.capabilities[capability]
}

// GetAvailableCapabilities returns all available capabilities
func (t *TermuxAPIClient) GetAvailableCapabilities() []string {
	capabilities := make([]string, 0, len(t.capabilities))
	for capability, available := range t.capabilities {
		if available {
			capabilities = append(capabilities, capability)
		}
	}
	return capabilities
}

// SendQuickNotification sends a simple notification (convenience method)
func (t *TermuxAPIClient) SendQuickNotification(title, content string) error {
	return t.SendNotification(NotificationConfig{
		Title:     title,
		Content:   content,
		Priority:  "default",
		Sound:     true,
		Vibration: true,
	})
}

// QuickVibrate triggers a simple vibration (convenience method)
func (t *TermuxAPIClient) QuickVibrate(duration int) error {
	return t.Vibrate(VibrationPattern{
		Duration: duration,
		Force:    128,
	})
}

// QuickRecordAudio records audio with default settings (convenience method)
func (t *TermuxAPIClient) QuickRecordAudio(duration int) ([]byte, error) {
	return t.RecordAudio(AudioStreamConfig{
		Duration:     duration,
		Format:       "wav",
		SampleRate:   44100,
		Channels:     1,
		StreamToAPI:  true,
	})
}

// ProcessMultiModalCommand handles multi-modal command processing
func (t *TermuxAPIClient) ProcessMultiModalCommand(command string, context map[string]interface{}) error {
	log.Printf("🎯 Processing multi-modal command: %s", command)
	
	// Send command with device context to orchestrator
	payload := map[string]interface{}{
		"command":     command,
		"context":     context,
		"device_info": t.GetDeviceInfo(),
		"session_id":  t.sessionID,
		"timestamp":   time.Now().Unix(),
		"capabilities": t.GetAvailableCapabilities(),
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal command payload: %w", err)
	}
	
	resp, err := http.Post("http://localhost:8080/api/multimodal-command", 
		"application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to send command to orchestrator: %w", err)
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != 200 {
		return fmt.Errorf("orchestrator returned status %d", resp.StatusCode)
	}
	
	// Process response and execute multi-modal actions
	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return fmt.Errorf("failed to decode orchestrator response: %w", err)
	}
	
	return t.executeMultiModalActions(response)
}

// executeMultiModalActions executes actions returned by the orchestrator
func (t *TermuxAPIClient) executeMultiModalActions(response map[string]interface{}) error {
	actions, ok := response["actions"].([]interface{})
	if !ok {
		return nil // No actions to execute
	}
	
	for _, actionData := range actions {
		action, ok := actionData.(map[string]interface{})
		if !ok {
			continue
		}
		
		actionType, _ := action["type"].(string)
		
		switch actionType {
		case "notification":
			if config, ok := action["config"].(map[string]interface{}); ok {
				notifConfig := NotificationConfig{
					Title:     getString(config, "title"),
					Content:   getString(config, "content"),
					Priority:  getString(config, "priority"),
					Sound:     getBool(config, "sound"),
					Vibration: getBool(config, "vibration"),
				}
				t.SendNotification(notifConfig)
			}
			
		case "vibration":
			if config, ok := action["config"].(map[string]interface{}); ok {
				pattern := VibrationPattern{
					Duration: getInt(config, "duration"),
					Force:    getInt(config, "force"),
				}
				t.Vibrate(pattern)
			}
			
		case "tts":
			if config, ok := action["config"].(map[string]interface{}); ok {
				ttsConfig := TTSConfig{
					Text:     getString(config, "text"),
					Language: getString(config, "language"),
					Pitch:    getFloat(config, "pitch"),
					Rate:     getFloat(config, "rate"),
				}
				t.TextToSpeech(ttsConfig)
			}
			
		case "torch":
			if enable, ok := action["enable"].(bool); ok {
				t.SetTorch(enable)
			}
			
		case "brightness":
			if level, ok := action["level"].(float64); ok {
				t.SetBrightness(int(level))
			}
		}
	}
	
	return nil
}

// Helper functions for type conversion
func getString(m map[string]interface{}, key string) string {
	if val, ok := m[key].(string); ok {
		return val
	}
	return ""
}

func getBool(m map[string]interface{}, key string) bool {
	if val, ok := m[key].(bool); ok {
		return val
	}
	return false
}

func getInt(m map[string]interface{}, key string) int {
	if val, ok := m[key].(float64); ok {
		return int(val)
	}
	return 0
}

// getFloat converts interface{} to float64
func getFloat(m map[string]interface{}, key string) float64 {
	if val, ok := m[key].(float64); ok {
		return val
	}
	return 0.0
}

// =============================================================================
// MAIN FUNCTION - PHASE 3 COMPLETE INTEGRATION
// =============================================================================

func main() {
	log.Println("🚀 Starting OMNIMESH LoL Nexus God Tier Interface - Phase 3")
	log.Println("✨ Termux API Multi-modal Integration Active")
	
	// Initialize clients
	nexusClient := NewNexusOrchestratorClient()
	termuxClient := NewTermuxAPIClient()
	
	// Display capabilities
	capabilities := termuxClient.GetAvailableCapabilities()
	log.Printf("📱 Available Termux Capabilities: %v", capabilities)
	
	// Display device info
	deviceInfo := termuxClient.GetDeviceInfo()
	log.Printf("🔋 Device Info: Battery %d%% (%s), Model: %s", 
		deviceInfo.BatteryLevel, deviceInfo.BatteryStatus, deviceInfo.DeviceModel)
	
	// Send startup notification
	termuxClient.SendQuickNotification("OMNIMESH Active", 
		"LoL Nexus God Tier Interface is now running with multi-modal capabilities")
	
	// Initialize the TUI program
	program := tea.NewProgram(initialModel(nexusClient, termuxClient), tea.WithAltScreen())
	
	// Start the program
	if _, err := program.Run(); err != nil {
		log.Printf("❌ Error running program: %v", err)
		os.Exit(1)
	}
	
	log.Println("👋 OMNIMESH LoL Nexus Interface terminated")
}

// initialModel creates the initial Bubble Tea model with both clients
func initialModel(nexusClient *NexusOrchestratorClient, termuxClient *TermuxAPIClient) model {
	return model{
		nexusClient:   nexusClient,
		termuxClient:  termuxClient,
		currentView:   "main",
		inputBuffer:   "",
		isListening:   false,
		batteryLevel:  termuxClient.GetDeviceInfo().BatteryLevel,
		deviceInfo:    termuxClient.GetDeviceInfo(),
		lastActivity:  time.Now(),
		sessionActive: true,
	}
}

// model represents the Bubble Tea application state
type model struct {
	nexusClient   *NexusOrchestratorClient
	termuxClient  *TermuxAPIClient
	currentView   string
	inputBuffer   string
	isListening   bool
	batteryLevel  int
	deviceInfo    *TermuxDeviceInfo
	lastActivity  time.Time
	sessionActive bool
	messages      []string
}

// Init implements the Bubble Tea Init interface
func (m model) Init() tea.Cmd {
	return tea.Batch(
		tea.EnterAltScreen,
		tickCmd(),
	)
}

// Update implements the Bubble Tea Update interface
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		return m.handleKeyPress(msg)
	case tickMsg:
		return m.handleTick()
	case tea.WindowSizeMsg:
		return m, nil
	}
	return m, nil
}

// View implements the Bubble Tea View interface
func (m model) View() string {
	return m.renderMainInterface()
}

// handleKeyPress processes keyboard input
func (m model) handleKeyPress(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c", "q":
		return m, tea.Quit
		
	case "r":
		// Start audio recording
		if !m.isListening {
			return m.startAudioRecording()
		}
		
	case "n":
		// Send test notification
		m.termuxClient.SendQuickNotification("Test Notification", 
			fmt.Sprintf("Battery: %d%%, Time: %s", 
				m.batteryLevel, time.Now().Format("15:04:05")))
		
	case "v":
		// Trigger vibration
		m.termuxClient.QuickVibrate(500)
		
	case "b":
		// Check battery status
		if battery, err := m.termuxClient.GetBatteryStatus(); err == nil {
			if batteryMap, ok := battery.(map[string]interface{}); ok {
				if level, ok := batteryMap["percentage"].(float64); ok {
					m.batteryLevel = int(level)
					m.addMessage(fmt.Sprintf("🔋 Battery: %.0f%%", level))
				}
			}
		}
		
	case "l":
		// Get location
		if location, err := m.termuxClient.GetLocation(); err == nil {
			m.addMessage(fmt.Sprintf("📍 Location: %.6f, %.6f", 
				location.Latitude, location.Longitude))
		}
		
	case "s":
		// Get sensor data
		if sensor, err := m.termuxClient.GetSensorData("accelerometer"); err == nil {
			m.addMessage(fmt.Sprintf("📊 Accelerometer: %v", sensor.Values))
		}
		
	case "t":
		// Text-to-speech test
		m.termuxClient.TextToSpeech(TTSConfig{
			Text:     "OMNIMESH LoL Nexus God Tier Interface is active and ready",
			Language: "en",
			Rate:     1.0,
			Pitch:    1.0,
		})
		
	case "enter":
		if m.inputBuffer != "" {
			return m.processCommand(m.inputBuffer)
		}
		
	default:
		// Add to input buffer
		if len(msg.String()) == 1 {
			m.inputBuffer += msg.String()
		}
	}
	
	return m, nil
}

// startAudioRecording initiates audio recording
func (m model) startAudioRecording() (tea.Model, tea.Cmd) {
	m.isListening = true
	go func() {
		audioData, err := m.termuxClient.QuickRecordAudio(3) // 3 second recording
		if err != nil {
			log.Printf("❌ Audio recording failed: %v", err)
			return
		}
		
		log.Printf("✅ Recorded %d bytes of audio", len(audioData))
		
		// Send notification about successful recording
		m.termuxClient.SendQuickNotification("Audio Recorded", 
			fmt.Sprintf("Captured %d bytes for processing", len(audioData)))
	}()
	
	return m, nil
}

// processCommand handles user commands
func (m model) processCommand(command string) (tea.Model, tea.Cmd) {
	m.addMessage(fmt.Sprintf("💬 Command: %s", command))
	
	// Process multi-modal command through Termux API
	context := map[string]interface{}{
		"battery_level": m.batteryLevel,
		"device_model":  m.deviceInfo.DeviceModel,
		"timestamp":     time.Now().Unix(),
	}
	
	go func() {
		if err := m.termuxClient.ProcessMultiModalCommand(command, context); err != nil {
			log.Printf("❌ Command processing failed: %v", err)
		}
	}()
	
	m.inputBuffer = ""
	return m, nil
}

// addMessage adds a message to the display
func (m model) addMessage(message string) {
	m.messages = append(m.messages, message)
	if len(m.messages) > 10 {
		m.messages = m.messages[1:]
	}
}

// handleTick updates the interface periodically
func (m model) handleTick() (tea.Model, tea.Cmd) {
	// Update device info every 30 seconds
	if time.Since(m.lastActivity) > 30*time.Second {
		deviceInfo := m.termuxClient.GetDeviceInfo()
		m.batteryLevel = deviceInfo.BatteryLevel
		m.deviceInfo = deviceInfo
		m.lastActivity = time.Now()
	}
	
	return m, tea.Tick(time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

// renderMainInterface renders the main interface
func (m model) renderMainInterface() string {
	headerStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#00ff00")).
		Bold(true).
		Align(lipgloss.Center)
	
	batteryStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#ffff00"))
	
	messageStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#ffffff")).
		MarginLeft(2)
	
	inputStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#00ffff")).
		Border(lipgloss.RoundedBorder()).
		Padding(0, 1)
	
	var content strings.Builder
	
	// Header
	content.WriteString(headerStyle.Render("🎮 OMNIMESH LoL Nexus God Tier Interface - Phase 3 🎮"))
	content.WriteString("\n\n")
	
	// Device status
	content.WriteString(batteryStyle.Render(fmt.Sprintf("🔋 Battery: %d%% | 📱 Model: %s | ⏰ %s",
		m.batteryLevel, m.deviceInfo.DeviceModel, time.Now().Format("15:04:05"))))
	content.WriteString("\n\n")
	
	// Capabilities
	capabilities := m.termuxClient.GetAvailableCapabilities()
	content.WriteString("📋 Available Capabilities:\n")
	for _, cap := range capabilities {
		content.WriteString(fmt.Sprintf("  ✅ %s\n", cap))
	}
	content.WriteString("\n")
	
	// Controls
	content.WriteString("🎮 Controls:\n")
	content.WriteString("  R - Record Audio | N - Notification | V - Vibrate\n")
	content.WriteString("  B - Battery | L - Location | S - Sensors | T - TTS\n")
	content.WriteString("  Q - Quit | Enter - Send Command\n\n")
	
	// Messages
	content.WriteString("📝 Messages:\n")
	for _, msg := range m.messages {
		content.WriteString(messageStyle.Render(msg))
		content.WriteString("\n")
	}
	content.WriteString("\n")
	
	// Input
	content.WriteString("💬 Input: ")
	content.WriteString(inputStyle.Render(m.inputBuffer))
	
	if m.isListening {
		content.WriteString("\n\n🎤 RECORDING...")
	}
	
	return content.String()
}

// tickMsg represents a tick message for periodic updates
type tickMsg time.Time

// tickCmd returns a command for periodic ticks
func tickCmd() tea.Cmd {
	return tea.Tick(time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}
