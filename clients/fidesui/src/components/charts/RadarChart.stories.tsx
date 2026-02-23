import type { Meta, StoryObj } from "@storybook/react-vite";
import { useCallback, useState } from "react";

import RadarChart, { RadarChartProps } from "./RadarChart";

const sampleData = [
  { subject: "Access", value: 80 },
  { subject: "Erasure", value: 65 },
  { subject: "Consent", value: 90 },
  { subject: "Portability", value: 50 },
  { subject: "Rectification", value: 70 },
  { subject: "Objection", value: 55 },
];

/**
 * Click the chart to replay its entry animation.
 * This wrapper is only for the Storybook demo.
 */
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
        "Chart data points as an array of { subject: string, value: number } objects",
    },
    color: {
      control: "color",
      description:
        "Stroke and fill color. Defaults to the Ant Design colorText token when not set.",
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

/** Click the chart to replay its entry animation. */
export const Default: Story = {
  args: {
    data: sampleData,
  },
  render: (args) => <AnimatedRadarChart {...args} />,
};

/** Renders a neutral hexagon shape when no data is provided. */
export const NoData: Story = {
  args: {
    data: null,
  },
};
