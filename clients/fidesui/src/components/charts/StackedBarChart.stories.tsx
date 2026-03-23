import type { Meta, StoryObj } from "@storybook/react-vite";

import type { StackedBarChartProps } from "../../index";
import { StackedBarChart } from "../../index";

const sampleSegments: StackedBarChartProps["segments"] = [
  { key: "on_track", color: "colorSuccess", label: "On track" },
  { key: "approaching", color: "colorWarning", label: "Approaching" },
  { key: "overdue", color: "colorError", label: "Overdue" },
];

const sampleData: StackedBarChartProps["data"] = {
  access: { on_track: 12, approaching: 3, overdue: 1 },
  erasure: { on_track: 8, approaching: 5, overdue: 2 },
  consent: { on_track: 20, approaching: 0, overdue: 0 },
};

const meta = {
  title: "Charts/StackedBarChart",
  component: StackedBarChart,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <div className="w-[400px]">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof StackedBarChart>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    data: sampleData,
    segments: sampleSegments,
  },
};

export const WithClickableCategories: Story = {
  args: {
    data: sampleData,
    segments: sampleSegments,
    onCategoryClick: (category: string) => {
      // eslint-disable-next-line no-console
      console.log("Clicked:", category);
    },
  },
};
