import { For, createSignal, onMount, onCleanup, createEffect } from 'solid-js';
import {
  notifications,
  setNotifications,
  criticalOverlay,
  setCriticalOverlay,
} from '../store/appState';

// Sound effects for notifications
const playNotificationSound = (type: 'normal' | 'critical' = 'normal') => {
  try {
    const audioContext = new (window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Different frequencies for different notification types
    oscillator.frequency.setValueAtTime(
      type === 'critical' ? 800 : 400,
      audioContext.currentTime,
    );
    oscillator.type = type === 'critical' ? 'sawtooth' : 'sine';

    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(
      0.01,
      audioContext.currentTime + 0.3,
    );

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.3);
  } catch (e) {
    console.warn('Audio not available:', e);
  }
};

export default function NotificationFeed() {
  const [focused, setFocused] = createSignal(false);
  const [selectedIndex, setSelectedIndex] = createSignal(0);
  const [showCriticalOverlay, setShowCriticalOverlay] = createSignal(false);
  let feedRef: HTMLDivElement | undefined;

  // Monitor for critical notifications and play sounds
  createEffect(() => {
    const msgs = notifications();
    if (msgs.length > 0) {
      const latestMsg = msgs[0];
      const isCritical =
        latestMsg.toLowerCase().includes('anomaly') ||
        latestMsg.toLowerCase().includes('critical') ||
        latestMsg.toLowerCase().includes('alert');

      if (isCritical) {
        playNotificationSound('critical');
        setCriticalOverlay(latestMsg);
        setShowCriticalOverlay(true);
        // Auto-hide critical overlay after 5 seconds
        setTimeout(() => {
          setShowCriticalOverlay(false);
          setCriticalOverlay(null);
        }, 5000);
      } else {
        playNotificationSound('normal');
      }
    }
  });

  // Enhanced keyboard navigation: focus, clear, and dismiss notifications
  onMount(() => {
    const handler = (e: KeyboardEvent) => {
      // Global shortcuts (work even when not focused)
      if (e.key === 'n' && e.ctrlKey) {
        feedRef?.focus();
        e.preventDefault();
        return;
      }

      if (!focused()) return;

      const msgs = notifications();

      switch (e.key) {
        case 'Escape':
          feedRef?.blur();
          break;
        case 'c':
          // Clear all notifications
          setNotifications([]);
          break;
        case 'Delete':
        case 'x':
          // Remove selected notification
          if (msgs.length > 0) {
            const index = selectedIndex();
            setNotifications(msgs.filter((_, i) => i !== index));
            setSelectedIndex(Math.max(0, Math.min(index, msgs.length - 2)));
          }
          break;
        case 'ArrowUp':
          setSelectedIndex(Math.max(0, selectedIndex() - 1));
          e.preventDefault();
          break;
        case 'ArrowDown':
          setSelectedIndex(Math.min(msgs.length - 1, selectedIndex() + 1));
          e.preventDefault();
          break;
        case 'Enter':
          // Dismiss critical overlay
          if (showCriticalOverlay()) {
            setShowCriticalOverlay(false);
            setCriticalOverlay(null);
          }
          break;
      }
    };
    window.addEventListener('keydown', handler);

    onCleanup(() => {
      window.removeEventListener('keydown', handler);
    });
  });

  return (
    <>
      {/* Critical Overlay - Full screen alert for urgent events */}
      {showCriticalOverlay() && (
        <div class="fixed inset-0 bg-red-900 bg-opacity-90 flex items-center justify-center z-50 animate-pulse">
          <div class="bg-red-800 border-2 border-red-400 rounded-lg p-6 max-w-md mx-4 text-center shadow-2xl">
            <div class="text-red-100 text-2xl font-bold mb-4">
              ⚠️ CRITICAL ALERT
            </div>
            <div class="text-red-200 mb-4">{criticalOverlay()}</div>
            <div class="text-red-300 text-sm">
              Press Enter or wait 5 seconds to dismiss
            </div>
          </div>
        </div>
      )}

      <div
        ref={feedRef}
        class="absolute top-4 left-1/2 transform -translate-x-1/2 w-96 max-w-full bg-black bg-opacity-80 rounded shadow-lg p-2 z-40 focus:outline-none md:rounded-xl transition-all duration-300"
        tabIndex={0}
        aria-label="Notifications Feed - Ctrl+N to focus, C to clear, X to delete selected"
        role="log"
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
      >
        <div class="font-bold text-white mb-2 flex justify-between items-center">
          <span>Notifications</span>
          <span class="text-xs text-gray-400">
            {focused() ? 'C:clear X:delete ↑↓:nav' : 'Ctrl+N to focus'}
          </span>
        </div>
        <ul>
          <For each={notifications()}>
            {(msg, index) => (
              <li
                class={`text-white text-sm mb-1 animate-fade-in-down shadow-md rounded px-2 py-1 transition-colors duration-200 ${
                  focused() && index() === selectedIndex()
                    ? 'bg-blue-700/80 border border-blue-400'
                    : 'bg-gray-800/80'
                } ${
                  msg.toLowerCase().includes('anomaly') ||
                  msg.toLowerCase().includes('critical') ||
                  msg.toLowerCase().includes('alert')
                    ? 'border-l-4 border-red-400'
                    : ''
                }`}
              >
                {msg}
                {/* Critical indicator */}
                {(msg.toLowerCase().includes('anomaly') ||
                  msg.toLowerCase().includes('critical') ||
                  msg.toLowerCase().includes('alert')) && (
                  <span class="ml-2 text-red-300 font-bold animate-pulse">
                    🚨 [CRITICAL]
                  </span>
                )}
              </li>
            )}
          </For>
        </ul>
        {notifications().length === 0 && (
          <div class="text-gray-400 text-sm text-center py-4">
            No notifications
          </div>
        )}
        {/* Explainable AI region */}
        <div class="mt-2 p-2 bg-gray-900 rounded text-blue-200 text-xs shadow-inner animate-fade-in">
          <span class="font-bold">Explainable AI:</span> Critical events trigger
          sound alerts and overlays. Keyboard shortcuts enable rapid triage.
        </div>
      </div>
    </>
  );
}
