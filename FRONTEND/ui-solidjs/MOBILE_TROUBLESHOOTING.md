# 🔧 Mobile Development Troubleshooting Guide

## 🚨 Common Issues & Solutions

### **Issue 1: "Cannot find package 'vite-plugin-pwa'"**

**Solution:**
```bash
# Install missing PWA plugin
npm install vite-plugin-pwa --save-dev

# Verify installation
npm list vite-plugin-pwa
```

### **Issue 2: Development Server Won't Start**

**Quick Fix:**
```bash
# Method 1: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Method 2: Clear Vite cache
rm -rf node_modules/.vite
npm run dev

# Method 3: Check for port conflicts
lsof -i :5173  # Check if port is in use
pkill -f vite  # Kill any existing vite processes
```

### **Issue 3: Phone Can't Access Development Server**

**Solutions:**

1. **Check Network Configuration:**
   ```bash
   # Get your IP address
   hostname -I
   ip addr show | grep inet
   
   # Test server binding
   npm run dev
   # Look for "Network: http://YOUR_IP:5173" in output
   ```

2. **Firewall Issues:**
   ```bash
   # Ubuntu/Linux
   sudo ufw allow 5173
   sudo ufw allow 5174
   
   # Check firewall status
   sudo ufw status
   ```

3. **Network Troubleshooting:**
   ```bash
   # Ping from phone to computer (use terminal app)
   ping 192.168.0.96
   
   # Test port accessibility
   telnet 192.168.0.96 5173
   ```

### **Issue 4: PWA Not Installing**

**Requirements for PWA Installation:**
- ✅ HTTPS connection (use `npm run dev:https`)
- ✅ Service worker registered
- ✅ Web app manifest present
- ✅ Minimum 192x192 icon

**Fix:**
```bash
# Use HTTPS development server
npm run dev:https

# Accept certificate warning on phone
# Then try installing PWA again
```

### **Issue 5: Touch Interactions Not Working**

**Check CSS:**
```css
/* Ensure touch-action is enabled */
.interactive-element {
  touch-action: manipulation;
  user-select: none;
}
```

## 🔍 Diagnostic Commands

### **Full System Check:**
```bash
# Run comprehensive test suite
./test-suite.sh

# Mobile-specific setup
./mobile-setup.sh

# Check all dependencies
npm audit
npm outdated
```

### **Network Diagnostics:**
```bash
# Check network interfaces
ip addr show

# Check listening ports
netstat -tlnp | grep :5173

# Test from another device
curl http://YOUR_IP:5173
```

### **Development Server Diagnostics:**
```bash
# Verbose development server
npm run dev -- --debug

# Check Vite configuration
npx vite --help
```

## 🚀 Quick Mobile Test Procedure

### **1. Basic Setup (2 minutes):**
```bash
cd "project omnitide/ui-solidjs"
npm install
npm run type-check  # Should pass
npm run build      # Should complete
```

### **2. Mobile Access Test (3 minutes):**
```bash
# Start server
npm run dev

# On your phone:
# 1. Connect to same WiFi
# 2. Open browser
# 3. Go to: http://YOUR_IP:5173
# 4. Should see Omnitide interface
```

### **3. PWA Installation Test (2 minutes):**
```bash
# Start HTTPS server
npm run dev:https

# On your phone:
# 1. Go to: https://YOUR_IP:5174
# 2. Accept certificate warning
# 3. Install as PWA via browser menu
# 4. Should appear on home screen
```

## 💡 Pro Tips

### **Development Workflow:**
- Use `npm run dev:https` for PWA testing
- Keep DevTools open for debugging
- Test on multiple devices/browsers
- Use network throttling for performance testing

### **Performance Optimization:**
- Enable GPU acceleration in browser
- Close other apps on phone
- Use WiFi instead of mobile data
- Test in both portrait and landscape

### **Debugging Tools:**
- Chrome DevTools Remote Debugging
- Safari Web Inspector (iOS)
- Browser network analysis
- Console logging for touch events

## 🆘 Emergency Fixes

### **If Nothing Works:**
```bash
# Nuclear option: Fresh install
rm -rf node_modules package-lock.json dist .vite
npm install
npm run dev
```

### **Alternative Mobile Testing:**
```bash
# Use different port
npm run dev -- --port 3000

# Try different network interface
npm run dev -- --host 0.0.0.0

# Use local tunnel (if available)
npx localtunnel --port 5173
```

## 📞 Getting Help

1. **Check this troubleshooting guide first**
2. **Run `./test-suite.sh` for automated diagnostics**
3. **Search existing GitHub issues**
4. **Create new issue with:**
   - Your OS and browser versions
   - Complete error messages
   - Output of diagnostic commands
   - Steps to reproduce

---

**🎯 Most mobile issues are network/firewall related. The mobile setup script (`./mobile-setup.sh`) handles 90% of cases automatically!**
