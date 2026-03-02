import type { Meta, StoryObj } from "@storybook/react-vite";
import { Alert } from "fidesui";

const meta = {
  title: "Custom/Alert",
  component: Alert,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    type: {
      control: "select",
      options: ["success", "info", "warning", "error"],
    },
  },
  decorators: [
    (Story) => (
      <div className="w-full">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
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
