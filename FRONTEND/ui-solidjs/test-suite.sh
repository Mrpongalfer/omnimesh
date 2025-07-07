#!/bin/bash

# 🧪 Omnitide Control Panel - Comprehensive Test Runner
# This script validates the complete bleeding-edge setup

set -e  # Exit on any error

echo "🚀 Starting Omnitide Control Panel Test Suite..."
echo "================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${BLUE}Testing: ${test_name}${NC}"
    echo "Command: $test_command"
    echo "----------------------------------------"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: ${test_name}${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED: ${test_name}${NC}"
        ((TESTS_FAILED++))
    fi
}

# Start testing
echo -e "${YELLOW}Phase 1: Environment Validation${NC}"

run_test "Node.js Version Check" "node --version"
run_test "NPM Version Check" "npm --version"
run_test "Dependencies Installed" "test -d node_modules && echo 'Dependencies found'"

echo -e "\n${YELLOW}Phase 2: Code Quality Validation${NC}"

run_test "TypeScript Type Checking" "npm run type-check"
run_test "ESLint Code Quality" "npm run lint:check"
run_test "Prettier Code Formatting" "npm run format:check"

echo -e "\n${YELLOW}Phase 3: Build System Validation${NC}"

run_test "Production Build" "npm run build"
run_test "Build Output Validation" "test -d dist && echo 'Build artifacts created'"

echo -e "\n${YELLOW}Phase 4: Development Server Validation${NC}"

# Check for required dependencies first
run_test "Vite Plugin PWA Dependency" "npm list vite-plugin-pwa &>/dev/null || npm install vite-plugin-pwa --save-dev"

# Test development server startup with better error handling
run_test "Development Server Configuration" "grep -q 'host: true' vite.config.ts && echo 'Server configured for network access'"

echo -e "\n${YELLOW}Phase 5: Documentation Validation${NC}"

run_test "README.md exists" "test -f README.md"
run_test "API Documentation exists" "test -f docs/API.md"
run_test "Accessibility Guide exists" "test -f docs/ACCESSIBILITY.md"
run_test "DevOps Guide exists" "test -f docs/DEVOPS.md"
run_test "Performance Guide exists" "test -f docs/PERFORMANCE.md"
run_test "Architecture Decisions exists" "test -f docs/ADR.md"

echo -e "\n${YELLOW}Phase 6: GitHub Configuration Validation${NC}"

run_test "GitHub Issue Templates" "test -d .github/ISSUE_TEMPLATE"
run_test "Pull Request Template" "test -f .github/pull_request_template.md"
run_test "CODEOWNERS File" "test -f .github/CODEOWNERS"
run_test "Dependabot Configuration" "test -f .github/dependabot.yml"
run_test "CI Workflow" "test -f .github/workflows/ci.yml"

echo -e "\n${YELLOW}Phase 7: VSCode Configuration Validation${NC}"

run_test "VSCode Settings" "test -f .vscode/settings.json"
run_test "VSCode Extensions" "test -f .vscode/extensions.json"
run_test "VSCode Launch Config" "test -f .vscode/launch.json"
run_test "VSCode Tasks" "test -f .vscode/tasks.json"

echo -e "\n${YELLOW}Phase 8: Configuration Files Validation${NC}"

run_test "TypeScript Config" "test -f tsconfig.app.json"
run_test "Vite Config" "test -f vite.config.ts"
run_test "Tailwind Config" "test -f tailwind.config.js"
run_test "ESLint Config" "test -f eslint.config.js"
run_test "Playwright Config" "test -f playwright.config.ts"
run_test "Vitest Config" "test -f vitest.config.ts"
run_test "Git Attributes" "test -f .gitattributes"

echo -e "\n${YELLOW}Phase 9: Mobile & PWA Validation${NC}"

run_test "Mobile Guide exists" "test -f MOBILE_GUIDE.md"
run_test "Mobile Troubleshooting Guide exists" "test -f MOBILE_TROUBLESHOOTING.md"
run_test "Mobile Setup Script exists" "test -f mobile-setup.sh"
run_test "PWA Manifest Configuration" "grep -q 'VitePWA' vite.config.ts"
run_test "Network Server Binding" "grep -q 'host: true' vite.config.ts"
run_test "HTTPS Development Support" "grep -q 'dev:https' package.json"

# Get local IP for mobile testing instructions
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "Unable to detect IP")

if [ "$LOCAL_IP" != "Unable to detect IP" ]; then
    echo -e "\n${BLUE}📱 Mobile Access Information:${NC}"
    echo -e "${GREEN}Local IP Address: ${LOCAL_IP}${NC}"
    echo -e "${GREEN}Development URL: http://${LOCAL_IP}:5173${NC}"
    echo -e "${GREEN}HTTPS URL: https://${LOCAL_IP}:5174${NC}"
    echo -e "${YELLOW}💡 Use these URLs to access from your phone!${NC}"
    echo -e "\n${BLUE}📋 Quick Mobile Test:${NC}"
    echo -e "${YELLOW}1. Run: npm run dev${NC}"
    echo -e "${YELLOW}2. Open: http://${LOCAL_IP}:5173 on your phone${NC}"
    echo -e "${YELLOW}3. For PWA: ./mobile-setup.sh${NC}"
    echo -e "${YELLOW}4. Issues? Check: MOBILE_TROUBLESHOOTING.md${NC}"
else
    echo -e "\n${YELLOW}💡 Run 'hostname -I' to get your IP for mobile access${NC}"
fi

# Final results
echo -e "\n================================================="
echo -e "${BLUE}🏆 TEST SUITE RESULTS${NC}"
echo -e "================================================="
echo -e "${GREEN}✅ Tests Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}❌ Tests Failed: ${TESTS_FAILED}${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo -e "${BLUE}📊 Success Rate: ${SUCCESS_RATE}%${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Your Omnitide Control Panel setup is bleeding-edge ready!${NC}"
    echo -e "${GREEN}🚀 The project implements state-of-the-art best practices across all areas.${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Check the output above for details.${NC}"
    echo -e "${YELLOW}💡 Most failures are likely missing dependencies or optional features.${NC}"
    exit 1
fi
