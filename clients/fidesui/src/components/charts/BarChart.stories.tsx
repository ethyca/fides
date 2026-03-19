import type { Meta, StoryObj } from "@storybook/react-vite";

import type { BarChartProps } from "../../index";
import { BarChart, DAY_MS, HOUR_MS } from "../../index";

const generateTimeSeries = (
  count: number,
  intervalMs: number,
): BarChartProps["data"] => {
  const now = new Date("2026-03-18T12:00:00Z").getTime();
  const start = now - count * intervalMs;
  return Array.from({ length: count }, (_, i) => ({
    label: new Date(start + i * intervalMs).toISOString(),
    value: Math.floor(Math.random() * 40) + 5,
  }));
};

const categoricalData: BarChartProps["data"] = [
  { label: "Marketing", value: 34 },
  { label: "Analytics", value: 28 },
  { label: "Warehouse", value: 22 },
  { label: "Support", value: 12 },
  { label: "Billing", value: 9 },
];

const meta = {
  title: "Charts/BarChart",
  component: BarChart,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    color: {
      control: "select",
      options: [
        "colorPrimary",
        "colorSuccess",
        "colorWarning",
        "colorError",
        "colorInfo",
        "colorText",
      ],
      description: "Ant Design color token for bar fill",
    },
    animationDuration: {
      control: { type: "range", min: 0, max: 3000, step: 100 },
      description:
        "Duration of the entry animation in ms. Set to 0 to disable.",
    },
    intervalMs: {
      control: "select",
      options: [undefined, HOUR_MS, 6 * HOUR_MS, DAY_MS],
      description:
        "Time interval between data points. Enables timestamp formatting when set.",
    },
    showTooltip: {
      control: "boolean",
      description: "Whether to show the tooltip on hover.",
    },
  },
  decorators: [
    (Story) => (
      <div style={{ width: 500, height: 200 }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof BarChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    data: categoricalData,
  },
};

export const TimeSeries: Story = {
  args: {
    data: generateTimeSeries(24, HOUR_MS),
    intervalMs: HOUR_MS,
    color: "colorError",
  },
};

export const TooltipDisabled: Story = {
  args: {
    data: categoricalData,
    showTooltip: false,
  },
};
