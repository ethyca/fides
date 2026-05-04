import type { Meta, StoryObj } from "@storybook/react-vite";

import { Bubble } from "../../index";

const BUBBLE_PLACEMENT = ["start", "end"] as const;
const BUBBLE_VARIANT = ["filled", "borderless", "outlined", "shadow"] as const;
const BUBBLE_SHAPE = ["round", "corner"] as const;

const meta = {
  title: "Chat/Bubble",
  component: Bubble,
  args: {
    content: "How can I help you build a policy today?",
    placement: "start",
    variant: "outlined",
    loading: false,
  },
  argTypes: {
    placement: {
      control: "select",
      options: BUBBLE_PLACEMENT,
    },
    variant: {
      control: "select",
      options: BUBBLE_VARIANT,
    },
    shape: {
      control: "select",
      options: BUBBLE_SHAPE,
    },
    loading: {
      control: "boolean",
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Bubble>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};

export const UserMessage: Story = {
  args: {
    content: "Draft a policy that blocks third-party advertising.",
    placement: "end",
    variant: "filled",
  },
};

export const Loading: Story = {
  args: {
    loading: true,
    content: "",
  },
};

export const List: Story = {
  render: () => (
    <Bubble.List
      autoScroll
      items={[
        {
          key: "u1",
          role: "user",
          content: "Draft a policy blocking third-party advertising.",
        },
        {
          key: "a1",
          role: "ai",
          content:
            "Here's a draft that denies user.contact and user.unique_id for third-party targeted advertising.",
        },
        {
          key: "u2",
          role: "user",
          content: "Allow it when the user has opted in.",
        },
        {
          key: "a2",
          role: "ai",
          content:
            "Added a consent exception for the `advertising_opt_in` privacy notice.",
        },
      ]}
      role={{
        user: { placement: "end", variant: "filled" },
        ai: { placement: "start", variant: "outlined" },
      }}
    />
  ),
};
