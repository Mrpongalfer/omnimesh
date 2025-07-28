package main

import (
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// MenuOption represents a menu item
type MenuOption struct {
	Label  string
	Action string
}

// MainMenuComponent - Primary navigation interface
type MainMenuComponent struct {
	id       string
	active   bool
	selected int
	options  []MenuOption
	style    *StyleEngine
	width    int
	height   int
}

func (m *MainMenuComponent) ID() string { return m.id }

func (m *MainMenuComponent) Init() tea.Cmd { return nil }

func (m *MainMenuComponent) Update(msg tea.Msg) (UIComponent, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.selected > 0 {
				m.selected--
			}
		case "down", "j":
			if m.selected < len(m.options)-1 {
				m.selected++
			}
		case "enter", " ":
			// Execute selected action
			action := m.options[m.selected].Action
			if action == "exit" {
				return m, tea.Quit
			}
			// Handle other actions
			return m, tea.Cmd(func() tea.Msg {
				return ActionMsg{Action: action}
			})
		}
	}
	return m, nil
}

func (m *MainMenuComponent) View() string {
	var view strings.Builder

	view.WriteString(m.style.subtitleStyle.Render("🎮 MAIN COMMAND CENTER") + "\n\n")

	for i, option := range m.options {
		if i == m.selected && m.active {
			view.WriteString(m.style.selectedStyle.Render(option.Label) + "\n")
		} else {
			style := m.style.menuStyle
			if !m.active {
				style = m.style.inactiveStyle
			}
			view.WriteString(style.Render(option.Label) + "\n")
		}
	}

	view.WriteString("\n")
	view.WriteString(m.style.infoStyle.Render("Use ↑/↓ to navigate, Enter to select, Tab to switch panels, Ctrl+C to exit"))

	return m.style.containerStyle.Render(view.String())
}

func (m *MainMenuComponent) SetSize(width, height int) {
	m.width = width
	m.height = height
}

func (m *MainMenuComponent) IsActive() bool { return m.active }

func (m *MainMenuComponent) SetActive(active bool) { m.active = active }

// ConversationMessage represents a chat message
type ConversationMessage struct {
	Timestamp  time.Time
	Speaker    string // "user" or "ai"
	Content    string
	Intent     string
	Confidence float64
}

// ConversationComponent - AI chat interface
type ConversationComponent struct {
	id           string
	active       bool
	messages     []ConversationMessage
	input        string
	inputMode    bool
	ai           *ConversationEngine
	orchestrator *NexusOrchestratorClient
	style        *StyleEngine
	width        int
	height       int
}

func (c *ConversationComponent) ID() string { return c.id }

func (c *ConversationComponent) Init() tea.Cmd { return nil }

func (c *ConversationComponent) Update(msg tea.Msg) (UIComponent, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		if c.inputMode {
			switch msg.String() {
			case "enter":
				if strings.TrimSpace(c.input) != "" {
					// Process user input
					userMsg := ConversationMessage{
						Timestamp: time.Now(),
						Speaker:   "user",
						Content:   c.input,
					}
					c.messages = append(c.messages, userMsg)

					// Process with AI
					intent, entities, confidence := c.ai.processNaturalLanguage(c.input)

					// Generate AI response
					aiResponse := c.generateAIResponse(c.input, intent, entities, confidence)
					aiMsg := ConversationMessage{
						Timestamp:  time.Now(),
						Speaker:    "ai",
						Content:    aiResponse,
						Intent:     intent,
						Confidence: confidence,
					}
					c.messages = append(c.messages, aiMsg)

					c.input = ""
				}
			case "esc":
				c.inputMode = false
			case "backspace":
				if len(c.input) > 0 {
					c.input = c.input[:len(c.input)-1]
				}
			default:
				if len(msg.String()) == 1 {
					c.input += msg.String()
				}
			}
		} else {
			switch msg.String() {
			case "i":
				c.inputMode = true
			case "c":
				c.messages = []ConversationMessage{}
			}
		}
	}
	return c, nil
}

func (c *ConversationComponent) View() string {
	var view strings.Builder

	view.WriteString(c.style.subtitleStyle.Render("🧠 CONVERSATIONAL AI INTERFACE") + "\n\n")

	// Messages area
	messagesHeight := c.height - 8
	if messagesHeight < 5 {
		messagesHeight = 5
	}

	messageArea := strings.Builder{}
	for _, msg := range c.messages {
		timestamp := msg.Timestamp.Format("15:04:05")
		if msg.Speaker == "user" {
			messageArea.WriteString(fmt.Sprintf("[%s] 👤 You: %s\n", timestamp, msg.Content))
		} else {
			confidence := ""
			if msg.Confidence > 0 {
				confidence = fmt.Sprintf(" (%.0f%% confidence)", msg.Confidence*100)
			}
			messageArea.WriteString(fmt.Sprintf("[%s] 🤖 LoL Nexus%s: %s\n", timestamp, confidence, msg.Content))
		}
		messageArea.WriteString("\n")
	}

	messagesBox := lipgloss.NewStyle().
		Border(lipgloss.NormalBorder()).
		BorderForeground(lipgloss.Color("#666666")).
		Height(messagesHeight).
		Width(c.width - 4).
		Padding(1).
		Render(messageArea.String())

	view.WriteString(messagesBox + "\n")

	// Input area
	inputPrompt := "💬 "
	if c.inputMode {
		inputPrompt += c.input + "█"
	} else {
		inputPrompt += "Press 'i' to start conversation, 'c' to clear, Tab to switch panels"
	}

	inputBox := lipgloss.NewStyle().
		Border(lipgloss.NormalBorder()).
		BorderForeground(lipgloss.Color("#00FFFF")).
		Width(c.width-4).
		Padding(0, 1).
		Render(inputPrompt)

	view.WriteString(inputBox)

	return view.String()
}

func (c *ConversationComponent) generateAIResponse(input, intent string, entities map[string]string, confidence float64) string {
	// Generate contextual AI response
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
		// Simple response selection (would use more sophisticated AI in production)
		responseIndex := len(c.messages) % len(responseList)
		return responseList[responseIndex]
	}

	// Default response for unknown intents
	if confidence < 0.6 {
		return fmt.Sprintf("I'm not entirely sure what you mean by '%s'. Could you rephrase that? I can help with deployments, system status, configuration, and more.", input)
	}

	return fmt.Sprintf("I understand you want to '%s'. Let me process that for you.", intent)
}

func (c *ConversationComponent) SetSize(width, height int) {
	c.width = width
	c.height = height
}

func (c *ConversationComponent) IsActive() bool { return c.active }

func (c *ConversationComponent) SetActive(active bool) { c.active = active }

// ServiceStatus represents the status of a service
type ServiceStatus struct {
	Name      string
	Status    string // "running", "stopped", "error", "unknown"
	Health    string // "healthy", "degraded", "unhealthy"
	Uptime    time.Duration
	CPU       float64
	Memory    float64
	LastCheck time.Time
}

// StatusComponent - System health monitoring
type StatusComponent struct {
	id       string
	active   bool
	services map[string]ServiceStatus
	metrics  map[string]interface{}
	style    *StyleEngine
	width    int
	height   int
}

func (s *StatusComponent) ID() string { return s.id }

func (s *StatusComponent) Init() tea.Cmd {
	// Initialize with mock data (would connect to real services)
	s.services = map[string]ServiceStatus{
		"nexus-orchestrator": {
			Name:      "Nexus Orchestrator",
			Status:    "running",
			Health:    "healthy",
			Uptime:    2 * time.Hour,
			CPU:       15.3,
			Memory:    245.7,
			LastCheck: time.Now(),
		},
		"rust-engine": {
			Name:      "Rust Core Engine",
			Status:    "running",
			Health:    "healthy",
			Uptime:    2 * time.Hour,
			CPU:       8.7,
			Memory:    512.1,
			LastCheck: time.Now(),
		},
		"go-proxies": {
			Name:      "Go Fabric Proxies",
			Status:    "running",
			Health:    "healthy",
			Uptime:    1*time.Hour + 45*time.Minute,
			CPU:       12.4,
			Memory:    128.3,
			LastCheck: time.Now(),
		},
		"web-frontend": {
			Name:      "Web Frontend",
			Status:    "running",
			Health:    "healthy",
			Uptime:    1*time.Hour + 30*time.Minute,
			CPU:       5.2,
			Memory:    89.6,
			LastCheck: time.Now(),
		},
	}
	return nil
}

func (s *StatusComponent) Update(msg tea.Msg) (UIComponent, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "r":
			// Refresh status
			return s, s.Init()
		}
	}
	return s, nil
}

func (s *StatusComponent) View() string {
	var view strings.Builder

	view.WriteString(s.style.subtitleStyle.Render("🔍 SYSTEM HEALTH DASHBOARD") + "\n\n")

	// Services status table
	table := strings.Builder{}
	table.WriteString("┌─────────────────────┬─────────┬──────────┬─────────┬──────────┬──────────┐\n")
	table.WriteString("│ Service             │ Status  │ Health   │ CPU %   │ Memory   │ Uptime   │\n")
	table.WriteString("├─────────────────────┼─────────┼──────────┼─────────┼──────────┼──────────┤\n")

	for _, service := range s.services {
		status := service.Status
		health := service.Health

		// Color code status
		statusStyle := lipgloss.NewStyle()
		switch service.Status {
		case "running":
			statusStyle = statusStyle.Foreground(lipgloss.Color("#00FF00"))
		case "stopped":
			statusStyle = statusStyle.Foreground(lipgloss.Color("#FF0000"))
		case "error":
			statusStyle = statusStyle.Foreground(lipgloss.Color("#FF0000")).Bold(true)
		default:
			statusStyle = statusStyle.Foreground(lipgloss.Color("#FFFF00"))
		}

		healthStyle := lipgloss.NewStyle()
		switch service.Health {
		case "healthy":
			healthStyle = healthStyle.Foreground(lipgloss.Color("#00FF00"))
		case "degraded":
			healthStyle = healthStyle.Foreground(lipgloss.Color("#FFFF00"))
		case "unhealthy":
			healthStyle = healthStyle.Foreground(lipgloss.Color("#FF0000"))
		}

		uptime := formatDuration(service.Uptime)

		table.WriteString(fmt.Sprintf("│ %-19s │ %s │ %s │ %6.1f  │ %7.1fM │ %8s │\n",
			service.Name,
			statusStyle.Render(fmt.Sprintf("%-7s", status)),
			healthStyle.Render(fmt.Sprintf("%-8s", health)),
			service.CPU,
			service.Memory,
			uptime,
		))
	}

	table.WriteString("└─────────────────────┴─────────┴──────────┴─────────┴──────────┴──────────┘\n")

	view.WriteString(table.String())
	view.WriteString("\n")

	// System metrics
	view.WriteString(s.style.subtitleStyle.Render("📊 SYSTEM METRICS") + "\n")
	view.WriteString("• Total CPU Usage: 12.4%\n")
	view.WriteString("• Total Memory Usage: 975.7MB\n")
	view.WriteString("• Network I/O: ↑ 1.2MB/s ↓ 2.8MB/s\n")
	view.WriteString("• Disk I/O: ↑ 512KB/s ↓ 1.1MB/s\n")
	view.WriteString("• Active Connections: 147\n")
	view.WriteString("\n")
	view.WriteString(s.style.infoStyle.Render("Press 'r' to refresh, Tab to switch panels"))

	return s.style.containerStyle.Render(view.String())
}

func (s *StatusComponent) SetSize(width, height int) {
	s.width = width
	s.height = height
}

func (s *StatusComponent) IsActive() bool { return s.active }

func (s *StatusComponent) SetActive(active bool) { s.active = active }

// LogEntry represents a log message
type LogEntry struct {
	Timestamp time.Time
	Level     string
	Component string
	Message   string
}

// LogPanelComponent - System log viewer
type LogPanelComponent struct {
	id     string
	active bool
	logs   []LogEntry
	filter string
	offset int
	style  *StyleEngine
	width  int
	height int
}

func (l *LogPanelComponent) ID() string { return l.id }

func (l *LogPanelComponent) Init() tea.Cmd {
	// Initialize with mock logs
	l.logs = []LogEntry{
		{time.Now().Add(-5 * time.Minute), "INFO", "orchestrator", "Trinity convergence initialization complete"},
		{time.Now().Add(-4 * time.Minute), "INFO", "rust-engine", "Nexus core engine started successfully"},
		{time.Now().Add(-3 * time.Minute), "INFO", "go-proxies", "Fabric proxy mesh established"},
		{time.Now().Add(-2 * time.Minute), "WARN", "web-frontend", "High memory usage detected: 89.6MB"},
		{time.Now().Add(-1 * time.Minute), "INFO", "orchestrator", "Health check completed - all systems operational"},
		{time.Now(), "INFO", "aether-ui", "God Tier Interface initialized"},
	}
	return nil
}

func (l *LogPanelComponent) Update(msg tea.Msg) (UIComponent, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up":
			if l.offset > 0 {
				l.offset--
			}
		case "down":
			maxOffset := len(l.logs) - (l.height - 6)
			if maxOffset < 0 {
				maxOffset = 0
			}
			if l.offset < maxOffset {
				l.offset++
			}
		case "home":
			l.offset = 0
		case "end":
			maxOffset := len(l.logs) - (l.height - 6)
			if maxOffset < 0 {
				maxOffset = 0
			}
			l.offset = maxOffset
		}
	}
	return l, nil
}

func (l *LogPanelComponent) View() string {
	var view strings.Builder

	view.WriteString(l.style.subtitleStyle.Render("📋 SYSTEM LOGS") + "\n\n")

	visibleHeight := l.height - 6
	if visibleHeight < 5 {
		visibleHeight = 5
	}

	start := l.offset
	end := start + visibleHeight
	if end > len(l.logs) {
		end = len(l.logs)
	}

	for i := start; i < end; i++ {
		log := l.logs[i]
		timestamp := log.Timestamp.Format("15:04:05")

		levelStyle := lipgloss.NewStyle()
		switch log.Level {
		case "ERROR":
			levelStyle = levelStyle.Foreground(lipgloss.Color("#FF0000")).Bold(true)
		case "WARN":
			levelStyle = levelStyle.Foreground(lipgloss.Color("#FFFF00"))
		case "INFO":
			levelStyle = levelStyle.Foreground(lipgloss.Color("#00FFFF"))
		case "DEBUG":
			levelStyle = levelStyle.Foreground(lipgloss.Color("#666666"))
		}

		view.WriteString(fmt.Sprintf("[%s] %s %s: %s\n",
			timestamp,
			levelStyle.Render(fmt.Sprintf("%-5s", log.Level)),
			log.Component,
			log.Message,
		))
	}

	// Show scroll indicator
	if len(l.logs) > visibleHeight {
		view.WriteString(fmt.Sprintf("\n📜 Showing %d-%d of %d entries", start+1, end, len(l.logs)))
	}

	view.WriteString("\n")
	view.WriteString(l.style.infoStyle.Render("Use ↑/↓ to scroll, Home/End to jump, Tab to switch panels"))

	return l.style.logPanelStyle.Render(view.String())
}

func (l *LogPanelComponent) SetSize(width, height int) {
	l.width = width
	l.height = height
}

func (l *LogPanelComponent) IsActive() bool { return l.active }

func (l *LogPanelComponent) SetActive(active bool) { l.active = active }

// StatusBarComponent - Bottom status bar
type StatusBarComponent struct {
	id     string
	active bool
	status string
	time   time.Time
	style  *StyleEngine
	width  int
	height int
}

func (s *StatusBarComponent) ID() string { return s.id }

func (s *StatusBarComponent) Init() tea.Cmd { return nil }

func (s *StatusBarComponent) Update(msg tea.Msg) (UIComponent, tea.Cmd) {
	s.time = time.Now()
	return s, nil
}

func (s *StatusBarComponent) View() string {
	timestamp := s.time.Format("2006-01-02 15:04:05")
	statusText := fmt.Sprintf(" %s │ %s │ Trinity Convergence Active │ AetherUI Framework v1.0 ",
		s.status, timestamp)

	return s.style.statusBarStyle.Render(statusText)
}

func (s *StatusBarComponent) SetSize(width, height int) {
	s.width = width
	s.height = height
	s.style.statusBarStyle = s.style.statusBarStyle.Width(width)
}

func (s *StatusBarComponent) IsActive() bool { return s.active }

func (s *StatusBarComponent) SetActive(active bool) { s.active = active }

// ActionMsg represents an action message
type ActionMsg struct {
	Action string
}

// Helper function to format duration
func formatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%ds", int(d.Seconds()))
	}
	if d < time.Hour {
		return fmt.Sprintf("%dm", int(d.Minutes()))
	}
	return fmt.Sprintf("%dh%dm", int(d.Hours()), int(d.Minutes())%60)
}
