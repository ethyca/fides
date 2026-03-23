import type { Meta, StoryObj } from "@storybook/react-vite";
import { Flex } from "antd/lib";

import { HOUR_MS } from "../../index";
import type { AreaChartProps } from "./AreaChart";
import { AreaChart } from "./AreaChart";
import { seededRandom } from "./story-utils";

const generateData = (hours: number): AreaChartProps["data"] => {
  const rand = seededRandom(99);
  const now = new Date("2026-03-18T12:00:00Z").getTime();
  const start = now - hours * HOUR_MS;
  return Array.from({ length: hours }, (_, index) => ({
    label: new Date(start + index * HOUR_MS).toISOString(),
    requests: Math.floor(rand() * 200) + 50,
    violations: Math.floor(rand() * 30) + 1,
  }));
};

const meta = {
  title: "Charts/AreaChart",
  component: AreaChart,
  parameters: { layout: "fullscreen" },
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <Flex
        style={{
          width: 800,
          height: 350,
          resize: "horizontal",
          overflow: "auto",
          border: "1px dashed #ccc",
          padding: 4,
          margin: 16,
        }}
      >
        <Story />
      </Flex>
    ),
  ],
} satisfies Meta<typeof AreaChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    data: generateData(72),
    series: [{ key: "violations", name: "Violations", color: "colorError" }],
  },
};

export const MultipleSeries: Story = {
  args: {
    data: generateData(168),
    series: [
      { key: "requests", name: "Total Requests", color: "colorBorder" },
      { key: "violations", name: "Violations", color: "colorText" },
    ],
  },
};
