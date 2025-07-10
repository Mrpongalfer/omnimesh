import { onMount } from 'solid-js';
import './App.css';
import ControlPanel from './pages/ControlPanel';
import { keyboardManager } from './services/keyboardManager';
import { themeManager } from './services/themeManager';
import { initializeMockRealtime } from './services/mockRealtime';

function App() {
  onMount(() => {
    // Initialize global services
    keyboardManager.enable();
    themeManager.initialize();

    // Start mock real-time data for development
    initializeMockRealtime();

    // Apply initial theme
    themeManager.applyCurrentTheme();
  });

  return (
    <div class="omnitide-app">
      <ControlPanel />
    </div>
  );
}

export default App;
