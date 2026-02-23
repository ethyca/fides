import type { Meta, StoryObj } from "@storybook/react-vite";

import palette from "../../palette/palette.module.scss";
import RadarChart from "./RadarChart";

const meta = {
  title: "Charts/RadarChart",
  component: RadarChart,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof RadarChart>;

export default meta;
type Story = StoryObj<typeof meta>;

const radarData = [
  { subject: "Access", value: 80 },
  { subject: "Erasure", value: 65 },
  { subject: "Consent", value: 90 },
  { subject: "Portability", value: 50 },
  { subject: "Rectification", value: 70 },
  { subject: "Objection", value: 55 },
];

export const Primary: Story = {
  args: {
    data: radarData,
    color: palette.FIDESUI_TERRACOTTA,
  },
  decorators: [
    (Story) => (
      <div style={{ width: 300, height: 300 }}>
        <Story />
      </div>
    ),
  ],
};

export const DefaultColor: Story = {
  args: {
    data: radarData,
  },
  decorators: [
    (Story) => (
      <div style={{ width: 300, height: 300 }}>
        <Story />
      </div>
    ),
  ],
};

export const Large: Story = {
  args: {
    data: radarData,
    color: palette.FIDESUI_OLIVE,
  },
  decorators: [
    (Story) => (
      <div style={{ width: 450, height: 450 }}>
        <Story />
      </div>
    ),
  ],
};
