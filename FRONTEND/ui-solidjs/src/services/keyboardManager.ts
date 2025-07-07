// src/services/keyboardManager.ts
// Global keyboard shortcut management for the Omnitide UI

import { executeCommand } from '../commands/commandLine';
import { playSound } from './soundManager';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  description: string;
  action: () => void;
  context?: string; // Optional context where shortcut is active
}

class KeyboardManager {
  private shortcuts: Map<string, KeyboardShortcut> = new Map();
  private activeContext: string | null = null;
  private enabled = true;

  constructor() {
    this.initializeDefaultShortcuts();
    this.bindEventListeners();
  }

  private initializeDefaultShortcuts(): void {
    // Global navigation shortcuts
    this.register({
      key: '/',
      description: 'Open universal command line',
      action: () => {
        // This will be handled by the UniversalCommandLine component
        playSound('button_click');
      },
    });

    this.register({
      key: 'h',
      description: 'Show help',
      action: () => {
        executeCommand('help');
        playSound('notification');
      },
    });

    this.register({
      key: 'Escape',
      description: 'Close overlays and deselect',
      action: () => {
        // This will be handled by individual components
        playSound('button_click');
      },
    });

    // Agent management shortcuts
    this.register({
      key: 'd',
      ctrlKey: true,
      description: 'Deploy agent (requires selection)',
      action: () => {
        executeCommand('help'); // Will show deployment syntax
        playSound('agent_deploy');
      },
    });

    this.register({
      key: 's',
      ctrlKey: true,
      description: 'Scan network',
      action: () => {
        executeCommand('scan network');
        playSound('scan_complete');
      },
    });

    // Notification management
    this.register({
      key: 'n',
      ctrlKey: true,
      description: 'Focus notifications',
      action: () => {
        // This will be handled by the NotificationFeed component
        playSound('button_click');
      },
    });

    this.register({
      key: 'Delete',
      context: 'notifications',
      description: 'Clear all notifications',
      action: () => {
        executeCommand('clear notifications');
        playSound('success');
      },
    });

    // Fabric map shortcuts
    this.register({
      key: 'f',
      ctrlKey: true,
      description: 'Focus fabric map',
      action: () => {
        const fabricMap = document.querySelector(
          '[role="application"]',
        ) as HTMLElement;
        if (fabricMap) {
          fabricMap.focus();
          playSound('button_click');
        }
      },
    });

    this.register({
      key: 'm',
      ctrlKey: true,
      description: 'Focus minimap',
      action: () => {
        const minimap = document.querySelector(
          '[aria-label*="minimap"]',
        ) as HTMLElement;
        if (minimap) {
          minimap.focus();
          playSound('button_click');
        }
      },
    });

    // Command bar shortcuts (Q, W, E, R for abilities)
    ['q', 'w', 'e', 'r'].forEach((key, index) => {
      this.register({
        key,
        description: `Trigger ability ${index + 1}`,
        action: () => {
          // This will be handled by the CommandBar component
          playSound('button_click');
        },
      });
    });

    // Debug shortcuts (only in development)
    if (import.meta.env.DEV) {
      this.register({
        key: 'F12',
        description: 'Toggle dev tools',
        action: () => {
          // Developer tools shortcut
          playSound('notification');
        },
      });
    }
  }

  public register(shortcut: KeyboardShortcut): void {
    const key = this.createKeyString(shortcut);
    this.shortcuts.set(key, shortcut);
  }

  public unregister(shortcut: Partial<KeyboardShortcut>): void {
    const key = this.createKeyString(shortcut);
    this.shortcuts.delete(key);
  }

  public setContext(context: string | null): void {
    this.activeContext = context;
  }

  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  public enable(): void {
    this.enabled = true;
  }

  public disable(): void {
    this.enabled = false;
  }

  public getShortcuts(context?: string): KeyboardShortcut[] {
    return Array.from(this.shortcuts.values()).filter(
      (shortcut) =>
        !context || !shortcut.context || shortcut.context === context,
    );
  }

  private createKeyString(shortcut: Partial<KeyboardShortcut>): string {
    const parts: string[] = [];
    if (shortcut.ctrlKey) parts.push('Ctrl');
    if (shortcut.shiftKey) parts.push('Shift');
    if (shortcut.altKey) parts.push('Alt');
    if (shortcut.metaKey) parts.push('Meta');
    if (shortcut.key) parts.push(shortcut.key);
    return parts.join('+');
  }

  private bindEventListeners(): void {
    document.addEventListener('keydown', this.handleKeyDown.bind(this));
  }

  private handleKeyDown(event: KeyboardEvent): void {
    if (!this.enabled) return;

    // Skip if user is typing in an input field
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.contentEditable === 'true'
    ) {
      return;
    }

    const keyString = this.createKeyString({
      key: event.key,
      ctrlKey: event.ctrlKey,
      shiftKey: event.shiftKey,
      altKey: event.altKey,
      metaKey: event.metaKey,
    });

    const shortcut = this.shortcuts.get(keyString);
    if (shortcut) {
      // Check if shortcut is valid for current context
      if (!shortcut.context || shortcut.context === this.activeContext) {
        event.preventDefault();
        shortcut.action();
      }
    }
  }

  public getHelpText(): string[] {
    const shortcuts = this.getShortcuts(this.activeContext);
    return shortcuts.map((shortcut) => {
      const keyString = this.createKeyString(shortcut);
      return `${keyString}: ${shortcut.description}`;
    });
  }
}

// Global keyboard manager instance
export const keyboardManager = new KeyboardManager();

// Convenience functions
export function registerShortcut(shortcut: KeyboardShortcut): void {
  keyboardManager.register(shortcut);
}

export function setKeyboardContext(context: string | null): void {
  keyboardManager.setContext(context);
}

export function getKeyboardHelp(): string[] {
  return keyboardManager.getHelpText();
}

export function setKeyboardEnabled(enabled: boolean): void {
  keyboardManager.setEnabled(enabled);
}
