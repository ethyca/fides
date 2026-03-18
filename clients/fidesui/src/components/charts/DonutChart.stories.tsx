import type { Meta, StoryObj } from "@storybook/react-vite";

import type { AntColorTokenKey } from "../../index";
import { DonutChart, DonutChartProps } from "../../index";

const sampleSegments: DonutChartProps["segments"] = [
  { value: 60, color: "colorSuccess", name: "Compliant" },
  { value: 25, color: "colorWarning", name: "In progress" },
  { value: 15, color: "colorError", name: "Non-compliant" },
];

const meta = {
  title: "Charts/DonutChart",
  component: DonutChart,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    segments: {
      control: "object",
      description: "Array of donut segments with value, color, and name",
    },
    variant: {
      control: "select",
      options: ["default", "thick"],
      description: "Donut ring thickness variant",
    },
    animationDuration: {
      control: { type: "range", min: 0, max: 3000, step: 100 },
      description:
        "Duration of the entry animation in ms. Set to 0 to disable.",
    },
  },
  decorators: [
    (Story) => (
      <div className="h-[150px] w-[150px]">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof DonutChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    segments: sampleSegments,
  },
};

export const Thick: Story = {
  args: {
    segments: sampleSegments,
    variant: "thick",
  },
};

export const WithCenterLabel: Story = {
  args: {
    segments: sampleSegments,
    variant: "thick",
    centerLabel: <span className="text-sm font-semibold">60%</span>,
  },
};

const MANY_SEGMENT_COLORS: AntColorTokenKey[] = [
  "colorPrimary",
  "colorSuccess",
  "colorWarning",
  "colorError",
  "colorInfo",
  "colorLink",
  "colorPrimaryBorder",
  "colorSuccessBorder",
  "colorWarningBorder",
  "colorErrorBorder",
  "colorInfoBorder",
  "colorPrimaryBgHover",
  "colorFillSecondary",
  "colorSuccessHover",
  "colorWarningHover",
];

const manySegments: DonutChartProps["segments"] = MANY_SEGMENT_COLORS.map(
  (color, i) => ({
    value: 10 + ((i * 7) % 30),
    color,
    name: `Segment ${i + 1}`,
  }),
);

export const ManySegments: Story = {
  args: {
    segments: manySegments,
    variant: "thick",
  },
};
