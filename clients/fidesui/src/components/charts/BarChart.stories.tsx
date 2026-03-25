import type { Meta, StoryObj } from "@storybook/react-vite";
import { Flex } from "antd/lib";

import type { BarChartProps } from "../../index";
import { BarChart, HOUR_MS } from "../../index";
import { seededRandom } from "./story-utils";

const generateData = (hours: number): BarChartProps["data"] => {
  const rand = seededRandom(42);
  const now = new Date("2026-03-18T12:00:00Z").getTime();
  const start = now - hours * HOUR_MS;
  return Array.from({ length: hours }, (_, index) => ({
    label: new Date(start + index * HOUR_MS).toISOString(),
    value: Math.floor(rand() * 30) + 1,
  }));
};

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
    showTooltip: {
      control: "boolean",
      description: "Whether to show the tooltip on hover.",
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
      description:
        "Bar width mapped to Ant Design size tokens: sm (8px), md (12px), lg (24px).",
    },
  },
  decorators: [
    (Story) => (
      <Flex style={{ width: "100%", height: 500 }}>
        <Story />
      </Flex>
    ),
  ],
} satisfies Meta<typeof BarChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    data: generateData(168),
    color: "colorError",
    size: "md",
  },
  render: (args) => (
    <Flex
      vertical
      style={{
        width: 800,
        resize: "horizontal",
        overflow: "auto",
        border: "1px dashed #ccc",
        padding: 4,
      }}
    >
      <Flex style={{ height: 160, width: "100%" }}>
        <BarChart {...args} />
      </Flex>
    </Flex>
  ),
};
