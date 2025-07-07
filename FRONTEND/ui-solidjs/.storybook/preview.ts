import '../src/index.css';

// Global preview configuration for Storybook
export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
  backgrounds: {
    default: 'dark',
    values: [
      {
        name: 'dark',
        value: '#1a1a1a',
      },
      {
        name: 'gray',
        value: '#2d2d2d',
      },
      {
        name: 'light',
        value: '#ffffff',
      },
    ],
  },
  viewport: {
    viewports: {
      mobile: {
        name: 'Mobile',
        styles: {
          width: '375px',
          height: '667px',
        },
      },
      tablet: {
        name: 'Tablet',
        styles: {
          width: '768px',
          height: '1024px',
        },
      },
      desktop: {
        name: 'Desktop',
        styles: {
          width: '1920px',
          height: '1080px',
        },
      },
      ultrawide: {
        name: 'Ultrawide',
        styles: {
          width: '3440px',
          height: '1440px',
        },
      },
    },
  },
  docs: {
    theme: {
      base: 'dark',
      brandTitle: 'Omnitide Control Panel',
      brandUrl: 'https://github.com/omnitide/control-panel',
    },
  },
  options: {
    storySort: {
      order: [
        'Introduction',
        'Components',
        ['Basic', 'Layout', 'Data', 'Visualization'],
        'Pages',
        'Services',
        'Utils',
      ],
    },
  },
};

// Global decorators
export const decorators = [
  (Story: any) => {
    // Create a simple wrapper element
    const wrapper = document.createElement('div');
    wrapper.style.padding = '20px';
    wrapper.style.background = '#1a1a1a';
    wrapper.style.color = '#ffffff';
    wrapper.style.fontFamily = 'Inter, system-ui, sans-serif';
    wrapper.style.minHeight = '100vh';
    
    const storyElement = Story();
    wrapper.appendChild(storyElement);
    
    return wrapper;
  },
];
