import type { Meta, StoryObj } from "@storybook/react-vite";
import { useCallback, useState } from "react";

import { COLOR_OPTIONS } from "./chart-constants";
import { RadarChart, RadarChartProps } from "./RadarChart";

const sampleData = [
  { subject: "Coverage", value: 80 },
  { subject: "Classification", value: 65 },
  { subject: "Consent", value: 50, status: "warning" as const },
  { subject: "DSR", value: 30, status: "error" as const },
  { subject: "Enforcement", value: 70 },
  { subject: "Assessments", value: 45, status: "warning" as const },
];

const sampleDataNoStatus = [
  { subject: "Coverage", value: 80 },
  { subject: "Classification", value: 65 },
  { subject: "Consent", value: 90 },
  { subject: "DSR", value: 50 },
  { subject: "Enforcement", value: 70 },
  { subject: "Assessments", value: 55 },
];

const AnimatedRadarChart = (props: RadarChartProps) => {
  const [animationKey, setAnimationKey] = useState(0);

  const handleClick = useCallback(() => {
    setAnimationKey((prev) => prev + 1);
  }, []);

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions
    <div className="h-full w-full cursor-pointer" onClick={handleClick}>
      <RadarChart key={animationKey} {...props} />
    </div>
  );
};

const meta = {
  title: "Charts/RadarChart",
  component: RadarChart,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    data: {
      control: "object",
      description:
        'Chart data points. Each point can include an optional `status` ("success" | "warning" | "error") to color its dot and label using Ant Design tokens.',
    },
    color: {
      control: { type: "select" },
      options: COLOR_OPTIONS,
      description:
        "Stroke and fill color for the radar and grid. Provide an Ant Design color token key (e.g., colorText, colorPrimary). Defaults to the colorText token when not set.",
    },
    animationDuration: {
      control: { type: "range", min: 0, max: 3000, step: 100 },
      description:
        "Duration of the entry animation in ms. Set to 0 to disable.",
    },
  },
  decorators: [
    (Story) => (
      <div className="h-[300px] w-[300px]">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof RadarChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const WithStatus: Story = {
  args: {
    data: sampleData,
  },
  render: (args) => <AnimatedRadarChart {...args} />,
};

export const Default: Story = {
  args: {
    data: sampleDataNoStatus,
  },
  render: (args) => <AnimatedRadarChart {...args} />,
};

export const NoData: Story = {
  args: {
    data: null,
  },
};
