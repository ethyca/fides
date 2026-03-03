import type { Meta, StoryObj } from "@storybook/react-vite";

import { Alert, GetProps } from "../../index";
import { PARAGRAPH_LOREM, SUBTITLE_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";

const meta = {
  title: "Feedback/Alert",
  component: Alert,
  tags: ["autodocs"],
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

const ALERT_TYPE: Record<
  NonNullable<GetProps<typeof Alert>["type"]>,
  GetProps<typeof Alert>["type"]
> = {
  error: "error",
  info: "info",
  success: "success",
  warning: "warning",
};

export const Primary: Story = {
  args: {
    message: SUBTITLE_LOREM,
    description: PARAGRAPH_LOREM,
    type: "info",
  },
  argTypes: {
    type: {
      control: "select",
      options: Object.values(ALERT_TYPE),
    },
    showIcon: {
      control: "boolean",
    },
    icon: iconControl,
  },
};

export const Error: Story = {
  args: {
    message: SUBTITLE_LOREM,
    description: PARAGRAPH_LOREM,
    type: "error",
    showIcon: true,
  },
};

export const Success: Story = {
  args: {
    message: SUBTITLE_LOREM,
    description: PARAGRAPH_LOREM,
    type: "success",
    showIcon: true,
  },
};

export const Warning: Story = {
  args: {
    message: SUBTITLE_LOREM,
    description: PARAGRAPH_LOREM,
    type: "warning",
    showIcon: true,
  },
};
