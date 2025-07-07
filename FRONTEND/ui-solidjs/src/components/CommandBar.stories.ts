import type { Meta, StoryObj } from '@storybook/web-components';
import { CommandBar } from '../components/CommandBar';

const meta: Meta<typeof CommandBar> = {
  title: 'Components/CommandBar',
  component: CommandBar,
  parameters: {
    docs: {
      description: {
        component: 'Advanced command interface with hotkeys, suggestions, and real-time execution.',
      },
    },
  },
  argTypes: {
    // Add any prop controls here when the component has props
  },
};

export default meta;
type Story = StoryObj<typeof CommandBar>;

export const Default: Story = {
  name: 'Default Command Bar',
  render: () => CommandBar(),
  parameters: {
    docs: {
      description: {
        story: 'The default command bar with all abilities and command line interface.',
      },
    },
  },
};

export const WithSelectedNode: Story = {
  name: 'With Selected Node',
  render: () => {
    // Mock a selected node for context-sensitive abilities
    // This would normally be set via the app state
    return CommandBar();
  },
  parameters: {
    docs: {
      description: {
        story: 'Command bar when a node is selected, showing context-sensitive abilities.',
      },
    },
  },
};
