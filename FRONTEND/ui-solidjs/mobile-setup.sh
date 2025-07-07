#!/bin/bash

# 📱 Mobile Testing Script for Omnitide Control Panel
# Quick setup for mobile development and testing

set -e

echo "📱 Omnitide Control Panel - Mobile Setup"
echo "========================================"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get local IP address
get_local_ip() {
    # Try different methods to get local IP
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || \
               ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' || \
               ifconfig 2>/dev/null | grep -E "inet.*broadcast" | awk '{print $2}' | head -1 || \
               echo "")
    
    if [ -z "$LOCAL_IP" ]; then
        echo "Unable to automatically detect IP address"
        echo "Please run: hostname -I  or  ip addr show"
        exit 1
    fi
    
    echo "$LOCAL_IP"
}

echo -e "${BLUE}🔍 Detecting network configuration...${NC}"
IP_ADDRESS=$(get_local_ip)

echo -e "${GREEN}✅ Local IP Address: ${IP_ADDRESS}${NC}"
echo ""

echo -e "${YELLOW}📋 Mobile Access Instructions:${NC}"
echo "=================================="
echo ""
echo -e "${BLUE}1. Start Development Server:${NC}"
echo "   npm run dev"
echo ""
echo -e "${BLUE}2. Access from Phone Browser:${NC}"
echo -e "   ${GREEN}http://${IP_ADDRESS}:5173${NC}"
echo ""
echo -e "${BLUE}3. For PWA Installation (HTTPS):${NC}"
echo "   npm run dev:https"
echo -e "   ${GREEN}https://${IP_ADDRESS}:5174${NC}"
echo "   (Accept certificate warning)"
echo ""
echo -e "${BLUE}4. Install as PWA:${NC}"
echo "   📱 Android: Menu → Add to Home Screen"
echo "   🍎 iOS: Share → Add to Home Screen"
echo ""

# QR Code generation (if qrencode is available)
if command -v qrencode &> /dev/null; then
    echo -e "${YELLOW}📱 QR Code for Easy Access:${NC}"
    echo ""
    qrencode -t ANSI "http://${IP_ADDRESS}:5173"
    echo ""
else
    echo -e "${YELLOW}💡 Install 'qrencode' for QR code generation:${NC}"
    echo "   sudo apt install qrencode  # Ubuntu/Debian"
    echo "   brew install qrencode      # macOS"
    echo ""
fi

echo -e "${YELLOW}🔧 Testing Checklist:${NC}"
echo "===================="
echo "□ Phone and computer on same WiFi network"
echo "□ Development server starts without errors"
echo "□ Mobile browser can access the URL"
echo "□ Touch interactions work smoothly"
echo "□ PWA installation successful"
echo "□ Offline functionality works"
echo "□ Performance feels responsive"
echo ""

echo -e "${YELLOW}🚀 Ready to Start?${NC}"
echo "=================="
echo -e "${GREEN}Run: npm run dev${NC}"
echo -e "${GREEN}Then open: http://${IP_ADDRESS}:5173 on your phone${NC}"

# Optional: Start development server automatically
read -p "Start development server now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🚀 Starting development server...${NC}"
    npm run dev
fi
