// MindForge Storybook Stories
// Note: This is a basic story structure. Full Storybook integration requires additional packages.

import type { Component } from 'solid-js';

interface MindForgeStoryMeta {
  title: string;
  component: Component;
  parameters: {
    layout: string;
    docs: {
      description: {
        component: string;
      };
    };
  };
  argTypes: {
    theme: {
      control: string;
      options: string[];
      description: string;
    };
    showMetrics: {
      control: string;
      description: string;
    };
  };
}

export const meta: MindForgeStoryMeta = {
  title: 'Components/MindForge',
  component: () => import('./MindForge') as any,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Advanced AI visualization and management interface with 3D neural networks and real-time metrics.',
      },
    },
  },
  argTypes: {
    theme: {
      control: 'select',
      options: ['dark', 'light'],
      description: 'Theme for the component',
    },
    showMetrics: {
      control: 'boolean',
      description: 'Show performance metrics',
    },
  },
};

export default meta;

// Story configurations
export const Default = {
  args: {
    theme: 'dark',
    showMetrics: true,
  },
};

export const LightTheme = {
  args: {
    theme: 'light',
    showMetrics: true,
  },
};

export const MinimalView = {
  args: {
    theme: 'dark',
    showMetrics: false,
  },
};
