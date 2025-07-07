/**
 * Storybook configuration for Omnitide Control Panel
 * This configuration sets up Storybook for SolidJS components
 */

const config = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx|mdx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-docs',
    '@storybook/addon-controls',
    '@storybook/addon-viewport',
    '@storybook/addon-backgrounds',
  ],
  framework: {
    name: '@storybook/vite',
    options: {},
  },
  core: {
    disableTelemetry: true,
  },
  features: {
    buildStoriesJson: true,
  },
  viteFinal: async (config: any) => {
    // Ensure Vite handles SolidJS properly
    return {
      ...config,
      plugins: [
        ...config.plugins!,
      ],
      define: {
        ...config.define,
        global: 'globalThis',
      },
      resolve: {
        ...config.resolve,
        alias: {
          ...config.resolve?.alias,
          '@': '/src',
        },
      },
    };
  },
  docs: {
    autodocs: 'tag',
    defaultName: 'Docs',
  },
  typescript: {
    check: false,
    reactDocgen: false,
  },
};

export default config;
