import type { Meta, StoryObj } from "@storybook/react-vite";

import { Alert, GetProps } from "../../index";

const ALERT_TYPE: Record<
  NonNullable<GetProps<typeof Alert>["type"]>,
  GetProps<typeof Alert>["type"]
> = {
  error: "error",
  info: "info",
  success: "success",
  warning: "warning",
};

const meta = {
  title: "Feedback/Alert",
  component: Alert,
  tags: ["autodocs"],
  argTypes: {
    type: {
      control: "select",
      options: Object.values(ALERT_TYPE),
    },
    showIcon: {
      control: "boolean",
    },
  },
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    message:
      "Our mission is to become the trusted data layer for enterprise and AI—unifying privacy, governance, and policy enforcement to make AI adoption safe and scalable.",
    description:
      "Ethyca was founded to build the trusted data layer for enterprise and AI: where privacy, governance, and policy enforcement are integrated directly into systems, not bolted on after the fact. As AI adoption accelerates, the stakes for responsible data use grow exponentially. Organizations need more than guidelines. They need data infrastructure that turns policy into practice, automatically and at scale.",
    type: "info",
  },
};

export const Error: Story = {
  args: {
    message:
      "Our mission is to become the trusted data layer for enterprise and AI—unifying privacy, governance, and policy enforcement to make AI adoption safe and scalable.",
    description:
      "Ethyca was founded to build the trusted data layer for enterprise and AI: where privacy, governance, and policy enforcement are integrated directly into systems, not bolted on after the fact. As AI adoption accelerates, the stakes for responsible data use grow exponentially. Organizations need more than guidelines. They need data infrastructure that turns policy into practice, automatically and at scale.",
    type: "error",
    showIcon: true,
  },
};

export const Success: Story = {
  args: {
    message:
      "Our mission is to become the trusted data layer for enterprise and AI—unifying privacy, governance, and policy enforcement to make AI adoption safe and scalable.",
    description:
      "Ethyca was founded to build the trusted data layer for enterprise and AI: where privacy, governance, and policy enforcement are integrated directly into systems, not bolted on after the fact. As AI adoption accelerates, the stakes for responsible data use grow exponentially. Organizations need more than guidelines. They need data infrastructure that turns policy into practice, automatically and at scale.",
    type: "success",
    showIcon: true,
  },
};

export const Warning: Story = {
  args: {
    message:
      "Our mission is to become the trusted data layer for enterprise and AI—unifying privacy, governance, and policy enforcement to make AI adoption safe and scalable.",
    description:
      "Ethyca was founded to build the trusted data layer for enterprise and AI: where privacy, governance, and policy enforcement are integrated directly into systems, not bolted on after the fact. As AI adoption accelerates, the stakes for responsible data use grow exponentially. Organizations need more than guidelines. They need data infrastructure that turns policy into practice, automatically and at scale.",
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
