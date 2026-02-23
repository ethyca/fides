import type { Meta, StoryObj } from "@storybook/react-vite";
import { useCallback, useState } from "react";

import Sparkline, { SparklineProps } from "./Sparkline";

const sampleData = [
  { value: 12 },
  { value: 18 },
  { value: 15 },
  { value: 22 },
  { value: 28 },
  { value: 25 },
  { value: 34 },
  { value: 30 },
  { value: 38 },
  { value: 42 },
  { value: 39 },
  { value: 47 },
];

const AnimatedSparkline = (props: SparklineProps) => {
  const [animationKey, setAnimationKey] = useState(0);

  const handleClick = useCallback(() => {
    setAnimationKey((prev) => prev + 1);
  }, []);

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions
    <div className="h-full w-full cursor-pointer" onClick={handleClick}>
      <Sparkline key={animationKey} {...props} />
    </div>
  );
};

const meta = {
  title: "Charts/Sparkline",
  component: Sparkline,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    data: {
      control: "object",
      description: "Chart data points as an array of { value: number } objects",
    },
    color: {
      control: "color",
      description:
        "Stroke and fill color. Defaults to the Ant Design colorText token when not set.",
    },
    strokeWidth: {
      control: { type: "range", min: 1, max: 6, step: 0.5 },
      description: "Width of the area stroke line",
    },
    animationDuration: {
      control: { type: "range", min: 0, max: 3000, step: 100 },
      description:
        "Duration of the entry animation in ms. Set to 0 to disable.",
    },
  },
  decorators: [
    (Story) => (
      <div className="h-[150px] w-[200px]">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Sparkline>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    data: sampleData,
  },
  render: (args) => <AnimatedSparkline {...args} />,
};

export const NoData: Story = {
  args: {
    data: null,
  },
};
