import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";

import { Sender } from "../../index";

const meta = {
  title: "Chat/Sender",
  component: Sender,
  args: {
    placeholder: "Describe your policy…",
    loading: false,
    disabled: false,
  },
  argTypes: {
    loading: {
      control: "boolean",
    },
    disabled: {
      control: "boolean",
    },
    placeholder: {
      control: "text",
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Sender>;

export default meta;
type Story = StoryObj<typeof meta>;

const ControlledSender = (
  args: React.ComponentProps<typeof Sender>,
): React.ReactElement => {
  const [value, setValue] = useState("");
  return <Sender {...args} value={value} onChange={setValue} />;
};

export const Primary: Story = {
  render: (args) => <ControlledSender {...args} />,
};

export const Loading: Story = {
  args: {
    loading: true,
    placeholder: "Thinking…",
  },
  render: (args) => <ControlledSender {...args} />,
};

export const Disabled: Story = {
  args: {
    disabled: true,
  },
  render: (args) => <ControlledSender {...args} />,
};
