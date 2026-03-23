import type { Meta, StoryObj } from "@storybook/react-vite";
import { Flex } from "antd/lib";
import { useMemo, useState } from "react";

import type { BarChartProps, ChartDataRequest } from "../../index";
import { BarChart, HOUR_MS } from "../../index";
import { seededRandom } from "./story-utils";

interface ViolationPoint {
  timestamp: string;
  violations: number;
}

const generateViolationLogs = (hours: number): ViolationPoint[] => {
  const rand = seededRandom(42);
  const now = new Date("2026-03-18T12:00:00Z").getTime();
  const start = now - hours * HOUR_MS;
  return Array.from({ length: hours }, (_, index) => ({
    timestamp: new Date(start + index * HOUR_MS).toISOString(),
    violations: Math.floor(rand() * 30) + 1,
  }));
};

const VIOLATION_DATA_7D = generateViolationLogs(168);

const mockBucketData = (
  points: ViolationPoint[],
  intervalHours: number,
): BarChartProps["data"] => {
  const ms = intervalHours * HOUR_MS;
  const timestamps = points.map((p) => new Date(p.timestamp).getTime());
  const minTs = Math.min(...timestamps);
  const maxTs = Math.max(...timestamps);
  const flooredStart = Math.floor(minTs / ms) * ms;
  const bucketCount = Math.max(1, Math.ceil((maxTs - flooredStart) / ms));

  const buckets = Array.from({ length: bucketCount }, (_, i) => ({
    label: new Date(flooredStart + i * ms).toISOString(),
    value: 0,
  }));

  timestamps.forEach((ts, idx) => {
    const bucketIndex = Math.min(
      Math.floor((ts - flooredStart) / ms),
      bucketCount - 1,
    );
    buckets[bucketIndex].value += points[idx].violations;
  });

  return buckets;
};

const DynamicBucketedChart = ({
  points,
  ...props
}: Omit<BarChartProps, "data" | "onIntervalChange"> & {
  points: ViolationPoint[];
}) => {
  const [request, setRequest] = useState<ChartDataRequest | null>(null);
  const data = useMemo(
    () =>
      request
        ? mockBucketData(points, request.interval)
        : mockBucketData(points, 6),
    [points, request],
  );

  return <BarChart {...props} data={data} onIntervalChange={setRequest} />;
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
        <DynamicBucketedChart
          points={VIOLATION_DATA_7D}
          color={args.color}
          size={args.size}
        />
      </Flex>
    </Flex>
  ),
};
