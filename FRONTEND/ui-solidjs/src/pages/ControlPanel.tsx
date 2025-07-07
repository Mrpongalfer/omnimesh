import { onMount, createEffect, createSignal, Show } from 'solid-js';
import FabricMap from '../components/FabricMap';
import Minimap from '../components/Minimap';
import CommandBar from '../components/CommandBar';
import ContextPanel from '../components/ContextPanel';
import NotificationFeed from '../components/NotificationFeed';
import UniversalCommandLine from '../components/UniversalCommandLine';
import MindForge from '../components/MindForge';
import DataFabricManager from '../components/DataFabricManager';
import SecurityNexus from '../components/SecurityNexus';
import { realtimeEvent, connectRealtime } from '../services/realtime';
import { criticalOverlay, setCriticalOverlay } from '../store/appState';

function useIsMobile() {
  const [isMobile, setIsMobile] = createSignal(false);
  onMount(() => {
    const check = () =>
      setIsMobile(
        window.innerWidth < 900 || /Mobi|Android/i.test(navigator.userAgent),
      );
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  });
  return isMobile;
}

// Sound feedback for critical events
function playAlertSound() {
  const audio = new Audio('/public/alert.mp3'); // Place alert.mp3 in public/
  audio.volume = 0.5;
  audio.play();
}

export default function ControlPanel() {
  const isMobile = useIsMobile();
  // Panel switching state
  const [activePanel, setActivePanel] = createSignal<
    'main' | 'mindforge' | 'datafabric' | 'security'
  >('main');

  onMount(() => {
    connectRealtime();
  });

  // Listen for real-time events and show overlay
  createEffect(() => {
    const event = realtimeEvent();
    if (event) {
      setCriticalOverlay(
        `${event.type}: ${JSON.stringify(event.data) || 'Critical event detected'}`,
      );
    }
  });

  // Play sound on critical overlay
  createEffect(() => {
    if (criticalOverlay()) playAlertSound();
  });

  // Panel switcher bar (top right)
  function PanelSwitcher() {
    return (
      <div class="fixed top-4 right-4 z-50 flex gap-2">
        <button
          class={`px-3 py-2 rounded bg-gray-800 text-white font-bold shadow border-2 border-blue-700 hover:bg-blue-700 transition ${activePanel() === 'main' ? 'bg-blue-700' : ''}`}
          onClick={() => setActivePanel('main')}
        >
          Main
        </button>
        <button
          class={`px-3 py-2 rounded bg-gray-800 text-white font-bold shadow border-2 border-purple-700 hover:bg-purple-700 transition ${activePanel() === 'mindforge' ? 'bg-purple-700' : ''}`}
          onClick={() => setActivePanel('mindforge')}
        >
          Mind Forge
        </button>
        <button
          class={`px-3 py-2 rounded bg-gray-800 text-white font-bold shadow border-2 border-green-700 hover:bg-green-700 transition ${activePanel() === 'datafabric' ? 'bg-green-700' : ''}`}
          onClick={() => setActivePanel('datafabric')}
        >
          Data Fabric
        </button>
        <button
          class={`px-3 py-2 rounded bg-gray-800 text-white font-bold shadow border-2 border-pink-700 hover:bg-pink-700 transition ${activePanel() === 'security' ? 'bg-pink-700' : ''}`}
          onClick={() => setActivePanel('security')}
        >
          Security
        </button>
      </div>
    );
  }

  // Global overlay for critical notifications, explainable AI, etc.
  function GlobalOverlay() {
    return (
      <Show when={criticalOverlay()}>
        <div class="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[100] animate-fade-in">
          <div class="bg-gray-900 border-4 border-blue-400 rounded-xl p-8 shadow-2xl text-white text-xl font-bold">
            {criticalOverlay()}
            <button
              class="mt-6 px-4 py-2 bg-blue-700 rounded text-white font-bold"
              onClick={() => setCriticalOverlay(null)}
            >
              Dismiss
            </button>
          </div>
        </div>
      </Show>
    );
  }

  return (
    <div
      class={`relative w-screen h-screen bg-black overflow-hidden ${isMobile() ? 'touch-manipulation' : ''}`}
    >
      <PanelSwitcher />
      <Show when={activePanel() === 'main'}>
        <div class="flex flex-col md:flex-row w-full h-full">
          <div class="flex-1 min-w-0 min-h-0">
            <FabricMap />
          </div>
          <div class="w-full md:w-96 max-w-full md:max-w-xs">
            <ContextPanel />
          </div>
        </div>
        <Minimap />
      </Show>
      <Show when={activePanel() === 'mindforge'}>
        <div class="w-full h-full flex items-center justify-center">
          <MindForge />
        </div>
      </Show>
      <Show when={activePanel() === 'datafabric'}>
        <div class="w-full h-full flex items-center justify-center">
          <DataFabricManager />
        </div>
      </Show>
      <Show when={activePanel() === 'security'}>
        <div class="w-full h-full flex items-center justify-center">
          <SecurityNexus />
        </div>
      </Show>
      <NotificationFeed />
      <UniversalCommandLine />
      <CommandBar />
      <GlobalOverlay />
      
      {/* Advanced Mobile Interface Enhancements */}
      <Show when={isMobile()}>
        <div class="fixed bottom-0 left-0 w-full bg-gradient-to-t from-black/90 via-black/60 to-transparent pointer-events-none z-50 h-32 md:hidden">
          <div class="absolute bottom-4 left-4 right-4 pointer-events-auto">
            <div class="flex items-center justify-between bg-gray-800/80 backdrop-blur-md rounded-xl p-3 border border-gray-600/50">
              <div class="flex items-center space-x-3">
                <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span class="text-xs text-gray-300">Omnitide Active</span>
              </div>
              <div class="flex items-center space-x-2">
                <button
                  class="p-2 bg-blue-600/80 rounded-lg text-white text-xs font-medium hover:bg-blue-500 transition-colors"
                  onClick={() => {
                    // Quick command access for mobile
                    (document.querySelector('[data-command-bar]') as HTMLElement)?.focus();
                  }}
                  aria-label="Open command bar"
                >
                  ⌘
                </button>
                <button
                  class="p-2 bg-gray-600/80 rounded-lg text-white text-xs font-medium hover:bg-gray-500 transition-colors"
                  onClick={() => {
                    // Toggle between main panels for mobile
                    const panels: Array<'main' | 'mindforge' | 'datafabric' | 'security'> = ['main', 'mindforge', 'datafabric', 'security'];
                    const currentIndex = panels.indexOf(activePanel());
                    const nextIndex = (currentIndex + 1) % panels.length;
                    const nextPanel = panels[nextIndex];
                    if (nextPanel) {
                      setActivePanel(nextPanel);
                    }
                  }}
                  aria-label="Switch view"
                >
                  ⟷
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Mobile haptic feedback and touch optimization overlay */}
        <div class="fixed inset-0 pointer-events-none z-40 md:hidden">
          <style>{`
            /* Touch-optimized interactions for mobile */
            .mobile-touch-target {
              min-height: 44px;
              min-width: 44px;
            }
            
            /* Enhanced contrast for mobile */
            @media (max-width: 768px) {
              .text-gray-400 { color: #d1d5db; }
              .bg-gray-800 { background-color: #1f2937; }
            }
            
            /* Mobile-specific animations */
            @media (max-width: 768px) {
              .animate-pulse {
                animation: mobile-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
              }
            }
            
            @keyframes mobile-pulse {
              0%, 100% { opacity: 1; }
              50% { opacity: 0.7; }
            }
          `}</style>
        </div>
      </Show>
    </div>
  );
}
