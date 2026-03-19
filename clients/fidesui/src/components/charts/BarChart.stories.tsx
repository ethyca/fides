import type { Meta, StoryObj } from "@storybook/react-vite";
import { Flex, theme } from "antd/lib";
import { useMemo, useRef, useState } from "react";

import type { BarChartProps, BarSize, ChartDataRequest, ChartInterval } from "../../index";
import {
  BarChart,
  computeDataRequest,
  HOUR_MS,
  intervalToMs,
  useContainerWidth,
} from "../../index";
import { BAR_SIZE_TOKEN } from "./chart-constants";

const categoricalData: BarChartProps["data"] = [
  { label: "Marketing", value: 34 },
  { label: "Analytics", value: 28 },
  { label: "Warehouse", value: 22 },
  { label: "Support", value: 12 },
  { label: "Billing", value: 9 },
];

const seededRandom = (seed: number) => {
  let state = seed;
  return () => {
    state = (state * 16807 + 0) % 2147483647;
    return (state - 1) / 2147483646;
  };
};

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

/**
 * Simulates what a backend would return: raw points aggregated into
 * `{ label, value }` buckets at the given interval.
 */
const mockBucketData = (
  points: ViolationPoint[],
  interval: ChartInterval,
): BarChartProps["data"] => {
  const ms = intervalToMs(interval);
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
}: Omit<BarChartProps, "data" | "interval" | "onDataRequest" | "timeRangeMs"> & {
  points: ViolationPoint[];
}) => {
  const timestamps = points.map((p) => new Date(p.timestamp).getTime());
  const timeRangeMs = Math.max(...timestamps) - Math.min(...timestamps);

  const [request, setRequest] = useState<ChartDataRequest | null>(null);
  const data = useMemo(
    () => (request ? mockBucketData(points, request.interval) : []),
    [points, request],
  );

  return (
    <BarChart
      {...props}
      data={data}
      interval={request?.interval}
      timeRangeMs={timeRangeMs}
      onDataRequest={setRequest}
    />
  );
};

const DebugPanel = ({
  size = "md",
  points,
}: {
  size?: BarSize;
  points: ViolationPoint[];
}) => {
  const { token } = theme.useToken();
  const ref = useRef<HTMLDivElement>(null);
  const containerWidth = useContainerWidth(ref);
  const barWidth = token[BAR_SIZE_TOKEN[size]];
  const dataRangeMs =
    new Date(points[points.length - 1].timestamp).getTime() -
    new Date(points[0].timestamp).getTime();

  const maxBuckets = Math.max(1, Math.floor(containerWidth / barWidth));

  // With user-provided range (uses data range as proxy)
  const withRange =
    containerWidth > 0
      ? computeDataRequest(containerWidth, barWidth, dataRangeMs)
      : null;
  // Without range — chart computes optimal
  const withoutRange =
    containerWidth > 0 ? computeDataRequest(containerWidth, barWidth) : null;

  const bucketCount = withRange
    ? Math.ceil(dataRangeMs / intervalToMs(withRange.interval))
    : 0;
  const barPx = bucketCount > 0 ? containerWidth / bucketCount : 0;

  const candidates: ChartInterval[] = ["1h", "6h", "1d", "3d"];

  return (
    <div
      ref={ref}
      style={{
        fontFamily: token.fontFamilyCode,
        fontSize: 11,
        color: token.colorTextSecondary,
        padding: "8px 0",
        lineHeight: 1.6,
      }}
    >
      <div>
        <strong>Container:</strong> {Math.round(containerWidth)}px
        &nbsp;&middot;&nbsp;
        <strong>Size:</strong> {size} ({barWidth}px min) &nbsp;&middot;&nbsp;
        <strong>Points:</strong> {points.length}
        &nbsp;&middot;&nbsp;
        <strong>Data range:</strong> {(dataRangeMs / HOUR_MS).toFixed(0)}h
        &nbsp;&middot;&nbsp;
        <strong>Max buckets:</strong> {maxBuckets}
      </div>
      <div>
        <strong>With range ({(dataRangeMs / HOUR_MS).toFixed(0)}h):</strong>{" "}
        <span style={{ color: token.colorPrimary, fontWeight: 600 }}>
          {withRange?.interval}
        </span>{" "}
        → {bucketCount} bars × {barPx.toFixed(1)}px
      </div>
      <div>
        <strong>Without range (optimal):</strong>{" "}
        <span style={{ color: token.colorSuccess, fontWeight: 600 }}>
          {withoutRange?.interval}
        </span>{" "}
        → request {((withoutRange?.rangeMs ?? 0) / HOUR_MS).toFixed(0)}h of data
        ({maxBuckets} bars)
      </div>
      <div style={{ marginTop: 4 }}>
        {candidates.map((interval) => {
          const count = Math.ceil(dataRangeMs / intervalToMs(interval));
          const width = containerWidth > 0 ? containerWidth / count : 0;
          const fits = count <= maxBuckets;
          const picked = interval === withRange?.interval;

          const getStatus = () => {
            if (picked) {
              return { color: token.colorPrimary, label: " ✓" };
            }
            if (fits) {
              return { color: token.colorSuccess, label: " ok" };
            }
            return { color: token.colorTextQuaternary, label: " ✗" };
          };
          const status = getStatus();

          return (
            <span
              key={interval}
              style={{
                marginRight: 12,
                color: status.color,
                fontWeight: picked ? 700 : 400,
              }}
            >
              {interval}: {count} bars ({width.toFixed(1)}px)
              {status.label}
            </span>
          );
        })}
      </div>
    </div>
  );
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
    data: categoricalData,
  },
};

export const AutoBucketed: Story = {
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
      <DebugPanel size={args.size} points={VIOLATION_DATA_7D} />
    </Flex>
  ),
};
