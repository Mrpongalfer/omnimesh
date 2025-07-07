// src/services/soundManager.ts
// Enhanced sound management for UI feedback and notifications

export type SoundType =
  | 'notification'
  | 'critical_alert'
  | 'success'
  | 'error'
  | 'button_click'
  | 'agent_deploy'
  | 'scan_complete'
  | 'connection_established'
  | 'connection_lost';

interface SoundConfig {
  frequency: number;
  type: OscillatorType;
  duration: number;
  volume: number;
  fadeOut?: boolean;
}

const SOUND_CONFIGS: Record<SoundType, SoundConfig> = {
  notification: {
    frequency: 400,
    type: 'sine',
    duration: 0.3,
    volume: 0.1,
    fadeOut: true,
  },
  critical_alert: {
    frequency: 800,
    type: 'sawtooth',
    duration: 0.5,
    volume: 0.2,
    fadeOut: true,
  },
  success: {
    frequency: 600,
    type: 'sine',
    duration: 0.2,
    volume: 0.1,
    fadeOut: true,
  },
  error: {
    frequency: 200,
    type: 'square',
    duration: 0.4,
    volume: 0.15,
    fadeOut: true,
  },
  button_click: {
    frequency: 800,
    type: 'sine',
    duration: 0.1,
    volume: 0.05,
    fadeOut: false,
  },
  agent_deploy: {
    frequency: 440,
    type: 'triangle',
    duration: 0.3,
    volume: 0.1,
    fadeOut: true,
  },
  scan_complete: {
    frequency: 660,
    type: 'sine',
    duration: 0.25,
    volume: 0.1,
    fadeOut: true,
  },
  connection_established: {
    frequency: 523,
    type: 'sine',
    duration: 0.2,
    volume: 0.08,
    fadeOut: true,
  },
  connection_lost: {
    frequency: 220,
    type: 'triangle',
    duration: 0.4,
    volume: 0.12,
    fadeOut: true,
  },
};

// Global sound settings
let globalVolume = 1.0;
let soundEnabled = true;

export function setSoundEnabled(enabled: boolean): void {
  soundEnabled = enabled;
}

export function setGlobalVolume(volume: number): void {
  globalVolume = Math.max(0, Math.min(1, volume));
}

export function playSound(soundType: SoundType): void {
  if (!soundEnabled || globalVolume === 0) return;

  try {
    const audioContext = new (window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext)();

    const config = SOUND_CONFIGS[soundType];
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.setValueAtTime(
      config.frequency,
      audioContext.currentTime,
    );
    oscillator.type = config.type;

    const finalVolume = config.volume * globalVolume;
    gainNode.gain.setValueAtTime(finalVolume, audioContext.currentTime);

    if (config.fadeOut) {
      gainNode.gain.exponentialRampToValueAtTime(
        0.01,
        audioContext.currentTime + config.duration,
      );
    }

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + config.duration);
  } catch (error) {
    console.warn(`Audio not available for sound: ${soundType}`, error);
  }
}

// Play compound sounds for complex actions
export function playCompoundSound(
  sounds: { type: SoundType; delay: number }[],
): void {
  sounds.forEach(({ type, delay }) => {
    setTimeout(() => playSound(type), delay);
  });
}

// Predefined compound sounds
export function playDeploymentSequence(): void {
  playCompoundSound([
    { type: 'button_click', delay: 0 },
    { type: 'agent_deploy', delay: 200 },
    { type: 'success', delay: 600 },
  ]);
}

export function playScanSequence(): void {
  playCompoundSound([
    { type: 'button_click', delay: 0 },
    { type: 'notification', delay: 100 },
    { type: 'scan_complete', delay: 1000 },
  ]);
}

export function playConnectionSequence(): void {
  playCompoundSound([
    { type: 'connection_established', delay: 0 },
    { type: 'success', delay: 300 },
  ]);
}

export function playDisconnectionSequence(): void {
  playCompoundSound([
    { type: 'connection_lost', delay: 0 },
    { type: 'error', delay: 300 },
  ]);
}
