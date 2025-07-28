package main

/*
LoL Nexus Termux Behavior Collector - Phase 4: True Intent Resonance
Termux API Data Hooks for Mobile Behavior Analysis

Comprehensive mobile behavior data collection with privacy preservation
integrating termux-location, termux-sensor, and file access APIs.
*/

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"golang.org/x/crypto/nacl/secretbox"
)

// MobileBehaviorData represents collected mobile behavior data
type MobileBehaviorData struct {
	Timestamp      time.Time      `json:"timestamp"`
	DataType       string         `json:"data_type"`
	LocationData   *LocationData  `json:"location_data,omitempty"`
	SensorData     *SensorData    `json:"sensor_data,omitempty"`
	FileActivity   *FileActivity  `json:"file_activity,omitempty"`
	AppUsage       *AppUsage      `json:"app_usage,omitempty"`
	SystemMetrics  *SystemMetrics `json:"system_metrics,omitempty"`
	AnonymizedHash string         `json:"anonymized_hash"`
	EncryptedData  string         `json:"encrypted_data"`
	Confidence     float64        `json:"confidence"`
}

// LocationData holds anonymized location information
type LocationData struct {
	GridCoordinate string  `json:"grid_coordinate"` // Anonymized grid reference
	MovementType   string  `json:"movement_type"`   // stationary, walking, driving
	Velocity       float64 `json:"velocity"`        // km/h
	Accuracy       float64 `json:"accuracy"`        // meters
	ContextZone    string  `json:"context_zone"`    // home, work, transit, unknown
}

// SensorData holds device sensor information
type SensorData struct {
	AccelerometerX  float64 `json:"accelerometer_x"`
	AccelerometerY  float64 `json:"accelerometer_y"`
	AccelerometerZ  float64 `json:"accelerometer_z"`
	GyroscopeX      float64 `json:"gyroscope_x"`
	GyroscopeY      float64 `json:"gyroscope_y"`
	GyroscopeZ      float64 `json:"gyroscope_z"`
	MagnetometerX   float64 `json:"magnetometer_x"`
	MagnetometerY   float64 `json:"magnetometer_y"`
	MagnetometerZ   float64 `json:"magnetometer_z"`
	LightLevel      float64 `json:"light_level"`
	Proximity       float64 `json:"proximity"`
	Temperature     float64 `json:"temperature"`
	Humidity        float64 `json:"humidity"`
	Pressure        float64 `json:"pressure"`
	ActivityPattern string  `json:"activity_pattern"` // derived from sensor fusion
}

// FileActivity tracks file system interactions
type FileActivity struct {
	Action       string `json:"action"`        // read, write, create, delete
	FileCategory string `json:"file_category"` // document, media, code, config
	SizeCategory string `json:"size_category"` // small, medium, large
	PathPattern  string `json:"path_pattern"`  // anonymized path structure
	AccessTime   string `json:"access_time"`   // time of day category
}

// AppUsage tracks application usage patterns
type AppUsage struct {
	AppCategory     string  `json:"app_category"`     // productivity, social, entertainment
	UsageDuration   float64 `json:"usage_duration"`   // minutes
	InteractionType string  `json:"interaction_type"` // active, background, notification
	TimeContext     string  `json:"time_context"`     // morning, afternoon, evening, night
}

// SystemMetrics holds device performance data
type SystemMetrics struct {
	BatteryLevel     int     `json:"battery_level"`
	BatteryStatus    string  `json:"battery_status"`
	CPUUsage         float64 `json:"cpu_usage"`
	MemoryUsage      float64 `json:"memory_usage"`
	StorageUsage     float64 `json:"storage_usage"`
	NetworkType      string  `json:"network_type"`
	SignalStrength   int     `json:"signal_strength"`
	ScreenBrightness int     `json:"screen_brightness"`
}

// BehaviorCollector manages mobile behavior data collection
type BehaviorCollector struct {
	encryptionKey    [32]byte
	anonymizationKey [32]byte
	dataBuffer       []MobileBehaviorData
	bufferMutex      sync.RWMutex
	collectionActive bool
	config           CollectorConfig
	httpClient       *http.Client
	termuxClient     *TermuxAPIClient
}

// CollectorConfig holds collection configuration
type CollectorConfig struct {
	CollectionInterval    time.Duration `json:"collection_interval"`
	LocationEnabled       bool          `json:"location_enabled"`
	SensorEnabled         bool          `json:"sensor_enabled"`
	FileMonitoringEnabled bool          `json:"file_monitoring_enabled"`
	PrivacyLevel          string        `json:"privacy_level"` // high, medium, low
	DataRetentionHours    int           `json:"data_retention_hours"`
	OrchestratorEndpoint  string        `json:"orchestrator_endpoint"`
	SyncInterval          time.Duration `json:"sync_interval"`
	MaxBufferSize         int           `json:"max_buffer_size"`
}

// NewBehaviorCollector initializes a new behavior collector
func NewBehaviorCollector(configPath string) (*BehaviorCollector, error) {
	bc := &BehaviorCollector{
		collectionActive: false,
		httpClient:       &http.Client{Timeout: 30 * time.Second},
	}

	// Load configuration
	config, err := bc.loadConfig(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to load config: %w", err)
	}
	bc.config = config

	// Generate encryption keys
	if err := bc.generateKeys(); err != nil {
		return nil, fmt.Errorf("failed to generate keys: %w", err)
	}

	// Initialize Termux API client
	bc.termuxClient = NewTermuxAPIClient()

	// Initialize data buffer
	bc.dataBuffer = make([]MobileBehaviorData, 0, bc.config.MaxBufferSize)

	log.Printf("BehaviorCollector initialized with privacy level: %s", bc.config.PrivacyLevel)
	return bc, nil
}

// loadConfig loads collector configuration
func (bc *BehaviorCollector) loadConfig(configPath string) (CollectorConfig, error) {
	defaultConfig := CollectorConfig{
		CollectionInterval:    5 * time.Minute,
		LocationEnabled:       true,
		SensorEnabled:         true,
		FileMonitoringEnabled: true,
		PrivacyLevel:          "high",
		DataRetentionHours:    24,
		OrchestratorEndpoint:  "http://100.64.0.1:8080/api/behavior",
		SyncInterval:          10 * time.Minute,
		MaxBufferSize:         1000,
	}

	if configPath == "" || !fileExists(configPath) {
		return defaultConfig, nil
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return defaultConfig, nil
	}

	var config CollectorConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return defaultConfig, nil
	}

	return config, nil
}

// generateKeys generates encryption and anonymization keys
func (bc *BehaviorCollector) generateKeys() error {
	keyFile := filepath.Join(os.Getenv("HOME"), ".lolnexus", "mobile_keys.key")

	// Create directory if needed
	if err := os.MkdirAll(filepath.Dir(keyFile), 0700); err != nil {
		return err
	}

	if fileExists(keyFile) {
		// Load existing keys
		data, err := os.ReadFile(keyFile)
		if err != nil {
			return err
		}

		if len(data) >= 64 {
			copy(bc.encryptionKey[:], data[:32])
			copy(bc.anonymizationKey[:], data[32:64])
			return nil
		}
	}

	// Generate new keys
	if _, err := rand.Read(bc.encryptionKey[:]); err != nil {
		return err
	}
	if _, err := rand.Read(bc.anonymizationKey[:]); err != nil {
		return err
	}

	// Save keys
	keyData := append(bc.encryptionKey[:], bc.anonymizationKey[:]...)
	return os.WriteFile(keyFile, keyData, 0600)
}

// StartCollection begins behavior data collection
func (bc *BehaviorCollector) StartCollection(ctx context.Context) error {
	if bc.collectionActive {
		return fmt.Errorf("collection already active")
	}

	bc.collectionActive = true
	log.Println("Starting mobile behavior collection...")

	// Start collection goroutines
	go bc.collectLocationData(ctx)
	go bc.collectSensorData(ctx)
	go bc.collectFileActivity(ctx)
	go bc.collectSystemMetrics(ctx)
	go bc.syncDataPeriodically(ctx)

	return nil
}

// collectLocationData collects and anonymizes location data
func (bc *BehaviorCollector) collectLocationData(ctx context.Context) {
	if !bc.config.LocationEnabled {
		return
	}

	ticker := time.NewTicker(bc.config.CollectionInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			locationData, err := bc.getLocationData()
			if err != nil {
				log.Printf("Error collecting location data: %v", err)
				continue
			}

			behaviorData := MobileBehaviorData{
				Timestamp:    time.Now(),
				DataType:     "location",
				LocationData: locationData,
				Confidence:   0.8,
			}

			bc.addBehaviorData(behaviorData)
		}
	}
}

// getLocationData retrieves and anonymizes location data
func (bc *BehaviorCollector) getLocationData() (*LocationData, error) {
	// Use termux-location API
	cmd := exec.Command("termux-location", "-p", "gps")
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	var location struct {
		Latitude  float64 `json:"latitude"`
		Longitude float64 `json:"longitude"`
		Accuracy  float64 `json:"accuracy"`
		Speed     float64 `json:"speed"`
	}

	if err := json.Unmarshal(output, &location); err != nil {
		return nil, err
	}

	// Anonymize location to grid coordinate
	gridCoord := bc.anonymizeLocation(location.Latitude, location.Longitude)

	// Determine movement type based on speed
	movementType := "stationary"
	if location.Speed > 1.0 {
		movementType = "walking"
	}
	if location.Speed > 10.0 {
		movementType = "driving"
	}

	// Determine context zone (simplified implementation)
	contextZone := bc.determineContextZone(gridCoord)

	return &LocationData{
		GridCoordinate: gridCoord,
		MovementType:   movementType,
		Velocity:       location.Speed * 3.6, // Convert m/s to km/h
		Accuracy:       location.Accuracy,
		ContextZone:    contextZone,
	}, nil
}

// anonymizeLocation converts lat/lng to anonymized grid reference
func (bc *BehaviorCollector) anonymizeLocation(lat, lng float64) string {
	// Convert to grid system (simplified geohash-like approach)
	latGrid := int(lat*100) / 100 // 0.01 degree precision (~1km)
	lngGrid := int(lng*100) / 100

	gridStr := fmt.Sprintf("%d,%d", latGrid, lngGrid)

	// Hash with anonymization key for consistent anonymization
	hasher := sha256.New()
	hasher.Write(bc.anonymizationKey[:])
	hasher.Write([]byte(gridStr))
	hash := hasher.Sum(nil)

	return base64.URLEncoding.EncodeToString(hash[:8])
}

// determineContextZone determines location context from grid coordinate
func (bc *BehaviorCollector) determineContextZone(gridCoord string) string {
	// This would be implemented with learned location patterns
	// For now, return "unknown"
	return "unknown"
}

// collectSensorData collects device sensor data
func (bc *BehaviorCollector) collectSensorData(ctx context.Context) {
	if !bc.config.SensorEnabled {
		return
	}

	ticker := time.NewTicker(bc.config.CollectionInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			sensorData, err := bc.getSensorData()
			if err != nil {
				log.Printf("Error collecting sensor data: %v", err)
				continue
			}

			behaviorData := MobileBehaviorData{
				Timestamp:  time.Now(),
				DataType:   "sensor",
				SensorData: sensorData,
				Confidence: 0.9,
			}

			bc.addBehaviorData(behaviorData)
		}
	}
}

// getSensorData retrieves device sensor information
func (bc *BehaviorCollector) getSensorData() (*SensorData, error) {
	sensors := &SensorData{}

	// Collect accelerometer data
	if accelData, err := bc.getSensorReading("accelerometer"); err == nil {
		sensors.AccelerometerX = accelData[0]
		sensors.AccelerometerY = accelData[1]
		sensors.AccelerometerZ = accelData[2]
	}

	// Collect gyroscope data
	if gyroData, err := bc.getSensorReading("gyroscope"); err == nil {
		sensors.GyroscopeX = gyroData[0]
		sensors.GyroscopeY = gyroData[1]
		sensors.GyroscopeZ = gyroData[2]
	}

	// Collect magnetometer data
	if magData, err := bc.getSensorReading("magnetometer"); err == nil {
		sensors.MagnetometerX = magData[0]
		sensors.MagnetometerY = magData[1]
		sensors.MagnetometerZ = magData[2]
	}

	// Collect environmental sensors
	if lightData, err := bc.getSensorReading("light"); err == nil && len(lightData) > 0 {
		sensors.LightLevel = lightData[0]
	}

	if proxData, err := bc.getSensorReading("proximity"); err == nil && len(proxData) > 0 {
		sensors.Proximity = proxData[0]
	}

	// Derive activity pattern from sensor fusion
	sensors.ActivityPattern = bc.deriveActivityPattern(sensors)

	return sensors, nil
}

// getSensorReading gets reading from specific sensor
func (bc *BehaviorCollector) getSensorReading(sensorType string) ([]float64, error) {
	cmd := exec.Command("termux-sensor", "-s", sensorType, "-n", "1")
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	var result struct {
		Values []float64 `json:"values"`
	}

	if err := json.Unmarshal(output, &result); err != nil {
		return nil, err
	}

	return result.Values, nil
}

// deriveActivityPattern derives activity pattern from sensor data
func (bc *BehaviorCollector) deriveActivityPattern(sensors *SensorData) string {
	// Simple activity recognition based on accelerometer
	totalAccel := sensors.AccelerometerX*sensors.AccelerometerX +
		sensors.AccelerometerY*sensors.AccelerometerY +
		sensors.AccelerometerZ*sensors.AccelerometerZ

	if totalAccel < 1.0 {
		return "stationary"
	} else if totalAccel < 4.0 {
		return "walking"
	} else if totalAccel < 16.0 {
		return "running"
	} else {
		return "vehicle"
	}
}

// collectFileActivity monitors file system activity
func (bc *BehaviorCollector) collectFileActivity(ctx context.Context) {
	if !bc.config.FileMonitoringEnabled {
		return
	}

	ticker := time.NewTicker(bc.config.CollectionInterval * 2) // Less frequent
	defer ticker.Stop()

	watchedDirs := []string{
		"/storage/emulated/0/Documents",
		"/storage/emulated/0/Download",
		"/storage/emulated/0/Pictures",
		"/data/data/com.termux/files/home",
	}

	lastModTimes := make(map[string]time.Time)

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			for _, dir := range watchedDirs {
				bc.scanDirectoryActivity(dir, lastModTimes)
			}
		}
	}
}

// scanDirectoryActivity scans directory for file activity
func (bc *BehaviorCollector) scanDirectoryActivity(dir string, lastModTimes map[string]time.Time) {
	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip inaccessible files
		}

		if info.IsDir() {
			return nil
		}

		modTime := info.ModTime()
		lastMod, exists := lastModTimes[path]

		if !exists || modTime.After(lastMod) {
			fileActivity := &FileActivity{
				Action:       bc.determineFileAction(exists, modTime),
				FileCategory: bc.categorizeFile(path),
				SizeCategory: bc.categorizeSizeCategory(info.Size()),
				PathPattern:  bc.anonymizeFilePath(path),
				AccessTime:   bc.categorizeTimeOfDay(modTime),
			}

			behaviorData := MobileBehaviorData{
				Timestamp:    modTime,
				DataType:     "file_activity",
				FileActivity: fileActivity,
				Confidence:   0.7,
			}

			bc.addBehaviorData(behaviorData)
			lastModTimes[path] = modTime
		}

		return nil
	})

	if err != nil {
		log.Printf("Error scanning directory %s: %v", dir, err)
	}
}

// determineFileAction determines the type of file action
func (bc *BehaviorCollector) determineFileAction(existed bool, modTime time.Time) string {
	if !existed {
		return "create"
	}
	return "modify"
}

// categorizeFile categorizes file by type
func (bc *BehaviorCollector) categorizeFile(path string) string {
	ext := strings.ToLower(filepath.Ext(path))

	docExts := []string{".txt", ".doc", ".docx", ".pdf", ".odt"}
	mediaExts := []string{".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3", ".wav"}
	codeExts := []string{".py", ".go", ".js", ".html", ".css", ".java", ".cpp"}

	for _, docExt := range docExts {
		if ext == docExt {
			return "document"
		}
	}

	for _, mediaExt := range mediaExts {
		if ext == mediaExt {
			return "media"
		}
	}

	for _, codeExt := range codeExts {
		if ext == codeExt {
			return "code"
		}
	}

	return "other"
}

// categorizeSizeCategory categorizes file size
func (bc *BehaviorCollector) categorizeSizeCategory(size int64) string {
	if size < 1024*1024 { // < 1MB
		return "small"
	} else if size < 10*1024*1024 { // < 10MB
		return "medium"
	} else {
		return "large"
	}
}

// anonymizeFilePath anonymizes file path while preserving structure
func (bc *BehaviorCollector) anonymizeFilePath(path string) string {
	parts := strings.Split(path, "/")
	anonymizedParts := make([]string, len(parts))

	for i, part := range parts {
		if i < 3 || part == "" { // Keep root parts
			anonymizedParts[i] = part
		} else {
			// Hash with anonymization key
			hasher := sha256.New()
			hasher.Write(bc.anonymizationKey[:])
			hasher.Write([]byte(part))
			hash := hasher.Sum(nil)
			anonymizedParts[i] = base64.URLEncoding.EncodeToString(hash[:4])
		}
	}

	return strings.Join(anonymizedParts, "/")
}

// categorizeTimeOfDay categorizes time of day
func (bc *BehaviorCollector) categorizeTimeOfDay(t time.Time) string {
	hour := t.Hour()
	if hour < 6 {
		return "night"
	} else if hour < 12 {
		return "morning"
	} else if hour < 18 {
		return "afternoon"
	} else {
		return "evening"
	}
}

// collectSystemMetrics collects device system metrics
func (bc *BehaviorCollector) collectSystemMetrics(ctx context.Context) {
	ticker := time.NewTicker(bc.config.CollectionInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			systemMetrics, err := bc.getSystemMetrics()
			if err != nil {
				log.Printf("Error collecting system metrics: %v", err)
				continue
			}

			behaviorData := MobileBehaviorData{
				Timestamp:     time.Now(),
				DataType:      "system_metrics",
				SystemMetrics: systemMetrics,
				Confidence:    1.0,
			}

			bc.addBehaviorData(behaviorData)
		}
	}
}

// getSystemMetrics retrieves device system metrics
func (bc *BehaviorCollector) getSystemMetrics() (*SystemMetrics, error) {
	metrics := &SystemMetrics{}

	// Get battery info
	if batteryInfo, err := bc.getBatteryInfo(); err == nil {
		metrics.BatteryLevel = batteryInfo.Level
		metrics.BatteryStatus = batteryInfo.Status
	}

	// Get network info
	if networkInfo, err := bc.getNetworkInfo(); err == nil {
		metrics.NetworkType = networkInfo.Type
		metrics.SignalStrength = networkInfo.SignalStrength
	}

	// Get device info
	if deviceInfo, err := bc.getDeviceInfo(); err == nil {
		metrics.ScreenBrightness = deviceInfo.Brightness
	}

	return metrics, nil
}

// getBatteryInfo gets battery information
func (bc *BehaviorCollector) getBatteryInfo() (*struct {
	Level  int    `json:"level"`
	Status string `json:"status"`
}, error) {
	cmd := exec.Command("termux-battery-status")
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	var batteryInfo struct {
		Level  int    `json:"percentage"`
		Status string `json:"status"`
	}

	if err := json.Unmarshal(output, &batteryInfo); err != nil {
		return nil, err
	}

	return &struct {
		Level  int    `json:"level"`
		Status string `json:"status"`
	}{
		Level:  batteryInfo.Level,
		Status: batteryInfo.Status,
	}, nil
}

// getNetworkInfo gets network information
func (bc *BehaviorCollector) getNetworkInfo() (*struct {
	Type           string `json:"type"`
	SignalStrength int    `json:"signal_strength"`
}, error) {
	// Simplified network info
	return &struct {
		Type           string `json:"type"`
		SignalStrength int    `json:"signal_strength"`
	}{
		Type:           "wifi", // Would be determined from actual network state
		SignalStrength: 80,     // Would be actual signal strength
	}, nil
}

// getDeviceInfo gets device information
func (bc *BehaviorCollector) getDeviceInfo() (*struct {
	Brightness int `json:"brightness"`
}, error) {
	// Simplified device info
	return &struct {
		Brightness int `json:"brightness"`
	}{
		Brightness: 50, // Would be actual screen brightness
	}, nil
}

// addBehaviorData adds behavior data to buffer
func (bc *BehaviorCollector) addBehaviorData(data MobileBehaviorData) {
	bc.bufferMutex.Lock()
	defer bc.bufferMutex.Unlock()

	// Encrypt and anonymize data
	data.AnonymizedHash = bc.anonymizeData(data)
	data.EncryptedData = bc.encryptData(data)

	// Add to buffer
	bc.dataBuffer = append(bc.dataBuffer, data)

	// Trim buffer if needed
	if len(bc.dataBuffer) > bc.config.MaxBufferSize {
		bc.dataBuffer = bc.dataBuffer[len(bc.dataBuffer)-bc.config.MaxBufferSize:]
	}
}

// anonymizeData creates anonymized hash of behavior data
func (bc *BehaviorCollector) anonymizeData(data MobileBehaviorData) string {
	hasher := sha256.New()
	hasher.Write(bc.anonymizationKey[:])

	// Add key data elements to hash
	hasher.Write([]byte(data.DataType))
	hasher.Write([]byte(data.Timestamp.Format("2006-01-02-15"))) // Hour precision

	if data.LocationData != nil {
		hasher.Write([]byte(data.LocationData.GridCoordinate))
	}

	hash := hasher.Sum(nil)
	return base64.URLEncoding.EncodeToString(hash[:8])
}

// encryptData encrypts behavior data
func (bc *BehaviorCollector) encryptData(data MobileBehaviorData) string {
	// Serialize data
	jsonData, err := json.Marshal(data)
	if err != nil {
		return ""
	}

	// Encrypt with NaCl secretbox
	var nonce [24]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return ""
	}

	encrypted := secretbox.Seal(nonce[:], jsonData, &nonce, &bc.encryptionKey)
	return base64.StdEncoding.EncodeToString(encrypted)
}

// syncDataPeriodically syncs collected data to orchestrator
func (bc *BehaviorCollector) syncDataPeriodically(ctx context.Context) {
	ticker := time.NewTicker(bc.config.SyncInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := bc.syncData(); err != nil {
				log.Printf("Error syncing data: %v", err)
			}
		}
	}
}

// syncData syncs behavior data to orchestrator
func (bc *BehaviorCollector) syncData() error {
	bc.bufferMutex.RLock()
	data := make([]MobileBehaviorData, len(bc.dataBuffer))
	copy(data, bc.dataBuffer)
	bc.bufferMutex.RUnlock()

	if len(data) == 0 {
		return nil
	}

	// Prepare sync payload
	payload := map[string]interface{}{
		"source":        "mobile_termux",
		"device_id":     bc.getDeviceID(),
		"data_count":    len(data),
		"behavior_data": data,
		"sync_time":     time.Now(),
		"privacy_level": bc.config.PrivacyLevel,
	}

	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	// Send to orchestrator
	resp, err := bc.httpClient.Post(
		bc.config.OrchestratorEndpoint,
		"application/json",
		bytes.NewBuffer(jsonPayload),
	)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("sync failed with status %d: %s", resp.StatusCode, string(body))
	}

	// Clear synced data from buffer
	bc.bufferMutex.Lock()
	bc.dataBuffer = bc.dataBuffer[:0]
	bc.bufferMutex.Unlock()

	log.Printf("Synced %d behavior data records to orchestrator", len(data))
	return nil
}

// getDeviceID gets anonymized device identifier
func (bc *BehaviorCollector) getDeviceID() string {
	// Create consistent device ID based on device characteristics
	hasher := sha256.New()
	hasher.Write(bc.anonymizationKey[:])
	hasher.Write([]byte("termux_device"))

	// Add device-specific but non-identifying info
	if hostname, err := os.Hostname(); err == nil {
		hasher.Write([]byte(hostname))
	}

	hash := hasher.Sum(nil)
	return base64.URLEncoding.EncodeToString(hash[:8])
}

// StopCollection stops behavior data collection
func (bc *BehaviorCollector) StopCollection() {
	bc.collectionActive = false
	log.Println("Mobile behavior collection stopped")
}

// GetCollectionSummary returns collection summary
func (bc *BehaviorCollector) GetCollectionSummary() map[string]interface{} {
	bc.bufferMutex.RLock()
	defer bc.bufferMutex.RUnlock()

	dataTypes := make(map[string]int)
	for _, data := range bc.dataBuffer {
		dataTypes[data.DataType]++
	}

	return map[string]interface{}{
		"total_records":     len(bc.dataBuffer),
		"data_types":        dataTypes,
		"collection_active": bc.collectionActive,
		"privacy_level":     bc.config.PrivacyLevel,
		"last_sync":         time.Now(),
	}
}

// fileExists checks if file exists
func fileExists(filename string) bool {
	_, err := os.Stat(filename)
	return !os.IsNotExist(err)
}

// Main function for standalone execution
func main() {
	configPath := os.Getenv("BEHAVIOR_CONFIG_PATH")
	if configPath == "" {
		configPath = "config/mobile_behavior.json"
	}

	collector, err := NewBehaviorCollector(configPath)
	if err != nil {
		log.Fatalf("Failed to create behavior collector: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := collector.StartCollection(ctx); err != nil {
		log.Fatalf("Failed to start collection: %v", err)
	}

	// Keep the program running
	select {}
}

// collectBehaviorData collects comprehensive behavior data from the mobile device
func (bc *BehaviorCollector) collectBehaviorData() (*BehaviorData, error) {
	bc.bufferMutex.Lock()
	defer bc.bufferMutex.Unlock()

	behaviorData := &BehaviorData{
		Timestamp:      time.Now(),
		DataType:       "comprehensive_behavior",
		AnonymizedHash: bc.generateAnonymizedHash("behavior_" + time.Now().String()),
		PrivacyLevel:   bc.config.PrivacyLevel,
	}

	// Collect system information
	behaviorData.Payload = map[string]interface{}{
		"system_uptime":    time.Now().Unix(),
		"memory_usage":     "anonymized",
		"cpu_usage":        "anonymized",
		"network_activity": "anonymized",
		"app_usage":        "anonymized",
		"location":         "anonymized",
		"sensor_data":      "anonymized",
		"user_interaction": "anonymized",
	}

	// Anonymize sensitive data
	anonymizedData, err := bc.anonymizeData(behaviorData)
	if err != nil {
		return nil, fmt.Errorf("failed to anonymize behavior data: %v", err)
	}

	return anonymizedData, nil
}

// sendToOrchestrator sends behavior data to the Nexus Orchestrator
func (bc *BehaviorCollector) sendToOrchestrator(data *BehaviorData) error {
	// Convert data to JSON
	jsonData, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal behavior data: %v", err)
	}

	// Create HTTP client with timeout
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	// Create request
	orchestratorURL := "http://localhost:8080/api/behavior"
	req, err := http.NewRequest("POST", orchestratorURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to create request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Device-ID", "mobile_collector")
	req.Header.Set("X-Privacy-Level", bc.config.PrivacyLevel)

	// Send request
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("orchestrator returned status: %d", resp.StatusCode)
	}

	log.Printf("Successfully sent behavior data to orchestrator")
	return nil
}
