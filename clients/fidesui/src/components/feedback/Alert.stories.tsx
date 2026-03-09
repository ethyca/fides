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

export const WithActions: Story = {
  args: {
    type: "info",
    message: "BRIEFING \u00b7 FEB 17, 2026",
    description:
      "Helios scanned 3 systems overnight. 12 fields classified, 4 need review \u2014 2 flagged as biometric in US systems. DSR-4892 SLA deadline tomorrow, pending Marketing.",
    showIcon: true,
    primaryAction: { label: "View actions \u2192", onClick: () => {} },
    secondaryAction: { label: "Dismiss", onClick: () => {} },
  },
};
