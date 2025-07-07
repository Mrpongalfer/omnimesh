// src/services/themeManager.ts
// Theme and styling management for consistent UI appearance

export type ThemeMode = 'dark' | 'light' | 'auto';
export type ColorScheme = 'blue' | 'green' | 'purple' | 'amber' | 'red';

export interface Theme {
  mode: ThemeMode;
  colorScheme: ColorScheme;
  fontSize: 'small' | 'medium' | 'large';
  animations: boolean;
  highContrast: boolean;
  reduceMotion: boolean;
}

export interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  critical: string;
}

const COLOR_SCHEMES: Record<ColorScheme, ThemeColors> = {
  blue: {
    primary: '#3b82f6',
    secondary: '#1e40af',
    accent: '#06b6d4',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f8fafc',
    textSecondary: '#cbd5e1',
    border: '#334155',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    critical: '#dc2626',
  },
  green: {
    primary: '#22c55e',
    secondary: '#16a34a',
    accent: '#84cc16',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f8fafc',
    textSecondary: '#cbd5e1',
    border: '#334155',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    critical: '#dc2626',
  },
  purple: {
    primary: '#8b5cf6',
    secondary: '#7c3aed',
    accent: '#a855f7',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f8fafc',
    textSecondary: '#cbd5e1',
    border: '#334155',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    critical: '#dc2626',
  },
  amber: {
    primary: '#f59e0b',
    secondary: '#d97706',
    accent: '#fbbf24',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f8fafc',
    textSecondary: '#cbd5e1',
    border: '#334155',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    critical: '#dc2626',
  },
  red: {
    primary: '#ef4444',
    secondary: '#dc2626',
    accent: '#f87171',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f8fafc',
    textSecondary: '#cbd5e1',
    border: '#334155',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    critical: '#dc2626',
  },
};

class ThemeManager {
  private currentTheme: Theme;
  private listeners: Array<(theme: Theme) => void> = [];

  constructor() {
    this.currentTheme = this.loadTheme();
    this.applyTheme();
    this.setupMediaQueryListeners();
  }

  private loadTheme(): Theme {
    const stored = localStorage.getItem('omnitide-theme');
    if (stored) {
      try {
        return { ...this.getDefaultTheme(), ...JSON.parse(stored) };
      } catch {
        // Fall back to default if stored theme is invalid
      }
    }
    return this.getDefaultTheme();
  }

  private getDefaultTheme(): Theme {
    return {
      mode: 'auto',
      colorScheme: 'blue',
      fontSize: 'medium',
      animations: true,
      highContrast: false,
      reduceMotion: false,
    };
  }

  private saveTheme(): void {
    localStorage.setItem('omnitide-theme', JSON.stringify(this.currentTheme));
  }

  private setupMediaQueryListeners(): void {
    // Listen for system theme changes
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    darkModeQuery.addEventListener('change', () => {
      if (this.currentTheme.mode === 'auto') {
        this.applyTheme();
      }
    });

    // Listen for reduced motion preference
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    motionQuery.addEventListener('change', (e) => {
      this.updateTheme({ reduceMotion: e.matches });
    });

    // Listen for high contrast preference
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    contrastQuery.addEventListener('change', (e) => {
      this.updateTheme({ highContrast: e.matches });
    });
  }

  private applyTheme(): void {
    const isDark = this.isDarkMode();
    const colors = COLOR_SCHEMES[this.currentTheme.colorScheme];

    // Set CSS custom properties
    const root = document.documentElement;

    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

    // Set theme mode
    root.setAttribute('data-theme', isDark ? 'dark' : 'light');
    root.setAttribute('data-color-scheme', this.currentTheme.colorScheme);

    // Set font size
    root.setAttribute('data-font-size', this.currentTheme.fontSize);

    // Set accessibility preferences
    root.setAttribute(
      'data-high-contrast',
      this.currentTheme.highContrast.toString(),
    );
    root.setAttribute(
      'data-reduce-motion',
      this.currentTheme.reduceMotion.toString(),
    );
    root.setAttribute(
      'data-animations',
      this.currentTheme.animations.toString(),
    );

    // Apply font size classes
    root.classList.toggle('text-sm', this.currentTheme.fontSize === 'small');
    root.classList.toggle('text-lg', this.currentTheme.fontSize === 'large');

    // Apply accessibility classes
    root.classList.toggle('high-contrast', this.currentTheme.highContrast);
    root.classList.toggle('reduce-motion', this.currentTheme.reduceMotion);

    // Notify listeners
    this.listeners.forEach((listener) => listener(this.currentTheme));
  }

  public applyCurrentTheme(): void {
    this.applyTheme();
  }

  private isDarkMode(): boolean {
    if (this.currentTheme.mode === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return this.currentTheme.mode === 'dark';
  }

  public updateTheme(updates: Partial<Theme>): void {
    this.currentTheme = { ...this.currentTheme, ...updates };
    this.saveTheme();
    this.applyTheme();
  }

  public getTheme(): Theme {
    return { ...this.currentTheme };
  }

  public getColors(): ThemeColors {
    return COLOR_SCHEMES[this.currentTheme.colorScheme];
  }

  public addListener(listener: (theme: Theme) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  public resetToDefaults(): void {
    this.currentTheme = this.getDefaultTheme();
    this.saveTheme();
    this.applyTheme();
  }

  public initialize(): void {
    // Re-apply the current theme (useful for initialization)
    this.applyTheme();
  }
}

// Global theme manager instance
export const themeManager = new ThemeManager();

// Convenience functions
export function updateTheme(updates: Partial<Theme>): void {
  themeManager.updateTheme(updates);
}

export function getTheme(): Theme {
  return themeManager.getTheme();
}

export function getThemeColors(): ThemeColors {
  return themeManager.getColors();
}

export function addThemeListener(listener: (theme: Theme) => void): () => void {
  return themeManager.addListener(listener);
}

export function resetTheme(): void {
  themeManager.resetToDefaults();
}

// Utility functions for components
export function getColorValue(colorName: keyof ThemeColors): string {
  return getThemeColors()[colorName];
}

export function getCSSCustomProperty(property: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(property);
}
