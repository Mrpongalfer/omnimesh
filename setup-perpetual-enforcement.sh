#!/bin/bash

# 🔒 TIGER LILY PERPETUAL ENFORCEMENT SCHEDULER 🔒
# Sets up cron jobs for continuous Tiger Lily Manifestation Ω^9 enforcement

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CRON_FILE="/tmp/tiger-lily-cron"
readonly LOG_FILE="${SCRIPT_DIR}/tiger-lily-scheduler.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

setup_perpetual_enforcement() {
    log_message "🔒 Setting up perpetual Tiger Lily enforcement..."
    
    # Create cron jobs file
    cat > "${CRON_FILE}" << 'EOF'
# 🔒 TIGER LILY MANIFESTATION Ω^9 PERPETUAL ENFORCEMENT 🔒
# Runs every 2 hours to ensure absolute performance integrity

# Tiger Lily enforcement every 2 hours
0 */2 * * * /home/pong/Documents/OMNIMESH/tiger-lily-enforcement.sh >> /home/pong/Documents/OMNIMESH/security-feedback/tiger-lily-cron.log 2>&1

# System orchestrator health check every 30 minutes
*/30 * * * * /usr/bin/python3 /home/pong/Documents/OMNIMESH/omni_system_orchestrator.py --health-check >> /home/pong/Documents/OMNIMESH/security-feedback/orchestrator-health.log 2>&1

# Resource monitoring every 10 minutes
*/10 * * * * /bin/bash -c 'top -bn1 | grep "Cpu(s)" | awk "{print \$2}" | cut -d"%" -f1 | cut -d"," -f1 > /home/pong/Documents/OMNIMESH/security-feedback/cpu-usage.log'

# Memory monitoring every 10 minutes
*/10 * * * * /bin/bash -c 'free | grep Mem | awk "{printf \"%.1f\", \$3/\$2 * 100.0}" > /home/pong/Documents/OMNIMESH/security-feedback/memory-usage.log'

# Security audit every 6 hours
0 */6 * * * /home/pong/Documents/OMNIMESH/perpetual-security-feedback.sh >> /home/pong/Documents/OMNIMESH/security-feedback/security-audit-cron.log 2>&1

# Cleanup old logs weekly
0 0 * * 0 find /home/pong/Documents/OMNIMESH/security-feedback -name "*.log" -mtime +7 -delete
EOF

    # Install cron jobs
    if crontab "${CRON_FILE}"; then
        log_message "✅ Tiger Lily perpetual enforcement cron jobs installed successfully"
    else
        log_message "❌ Failed to install cron jobs"
        return 1
    fi
    
    # Clean up
    rm -f "${CRON_FILE}"
    
    # Display current cron jobs
    log_message "📋 Current cron jobs:"
    crontab -l | grep -E "(tiger-lily|orchestrator|security)" || echo "No Tiger Lily cron jobs found"
}

remove_perpetual_enforcement() {
    log_message "🗑️ Removing perpetual Tiger Lily enforcement..."
    
    # Get current cron jobs, remove Tiger Lily ones
    crontab -l 2>/dev/null | grep -v -E "(tiger-lily|orchestrator|security)" > "${CRON_FILE}" || true
    
    # Reinstall cleaned cron jobs
    if crontab "${CRON_FILE}"; then
        log_message "✅ Tiger Lily enforcement cron jobs removed successfully"
    else
        log_message "❌ Failed to remove cron jobs"
        return 1
    fi
    
    # Clean up
    rm -f "${CRON_FILE}"
}

check_enforcement_status() {
    log_message "🔍 Checking Tiger Lily enforcement status..."
    
    # Check if cron jobs exist
    if crontab -l 2>/dev/null | grep -q "tiger-lily"; then
        log_message "✅ Tiger Lily enforcement cron jobs are active"
        
        # Show active jobs
        log_message "📋 Active Tiger Lily enforcement jobs:"
        crontab -l | grep -E "(tiger-lily|orchestrator|security)" | while read line; do
            log_message "   → $line"
        done
        
        # Check recent logs
        local recent_logs=$(find "${SCRIPT_DIR}/security-feedback" -name "*tiger-lily*" -mtime -1 2>/dev/null | wc -l)
        log_message "📊 Recent Tiger Lily enforcement logs: $recent_logs"
        
        # Check system status
        if [ -f "${SCRIPT_DIR}/security-feedback/tiger-lily-metrics.json" ]; then
            log_message "📈 Latest Tiger Lily metrics:"
            cat "${SCRIPT_DIR}/security-feedback/tiger-lily-metrics.json" | jq . 2>/dev/null || echo "Invalid JSON format"
        fi
        
    else
        log_message "⚠️ Tiger Lily enforcement cron jobs not found"
        return 1
    fi
}

show_help() {
    cat << EOF
🔒 TIGER LILY PERPETUAL ENFORCEMENT SCHEDULER 🔒

Usage: $0 [COMMAND]

Commands:
  setup     Set up perpetual Tiger Lily enforcement cron jobs
  remove    Remove all Tiger Lily enforcement cron jobs
  status    Check current enforcement status
  help      Show this help message

Examples:
  $0 setup      # Enable perpetual enforcement
  $0 status     # Check enforcement status
  $0 remove     # Disable perpetual enforcement

The perpetual enforcement system includes:
- Tiger Lily enforcement every 2 hours
- System orchestrator health checks every 30 minutes
- Resource monitoring every 10 minutes
- Security audits every 6 hours
- Automatic log cleanup weekly

EOF
}

main() {
    local command="${1:-help}"
    
    case "$command" in
        "setup")
            setup_perpetual_enforcement
            ;;
        "remove")
            remove_perpetual_enforcement
            ;;
        "status")
            check_enforcement_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_message "❌ Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Create log directory
mkdir -p "${SCRIPT_DIR}/security-feedback"

# Execute main function
main "$@"
