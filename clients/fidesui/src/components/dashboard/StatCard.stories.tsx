import type { Meta, StoryObj } from "@storybook/react-vite";

import Sparkline from "../charts/Sparkline";
import Stat from "./Stat";
import StatCard from "./StatCard";

const upwardTrendData = [
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

const downwardTrendData = [
  { value: 47 },
  { value: 42 },
  { value: 45 },
  { value: 38 },
  { value: 34 },
  { value: 36 },
  { value: 28 },
  { value: 24 },
  { value: 26 },
  { value: 18 },
  { value: 15 },
  { value: 12 },
];

const neutralTrendData = [
  { value: 28 },
  { value: 32 },
  { value: 25 },
  { value: 30 },
  { value: 27 },
  { value: 33 },
  { value: 26 },
  { value: 31 },
  { value: 28 },
  { value: 34 },
  { value: 29 },
  { value: 30 },
];

const ContentPlaceholder = () => (
  <div className="h-20 flex items-center justify-center bg-gray-50 rounded text-xs text-gray-300">
    chart / content
  </div>
);

const meta = {
  title: "Dashboard/Card",
  component: StatCard,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    title: {
      description: "Label rendered above the stat value in secondary text",
      control: "text",
    },
    stat: {
      description: "The stat display component, e.g. `<Stat />`",
      control: false,
    },
    content: {
      description:
        "Optional content rendered below the stat and above the footer",
      control: false,
    },
    footer: {
      description:
        "Optional edge-to-edge footer content, ideal for sparkline charts",
      control: false,
    },
    footerClassName: {
      description:
        "Class names applied to the footer wrapper. Defaults to `h-16`.",
      control: "text",
    },
  },
  decorators: [
    (Story) => (
      <div className="w-72">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof StatCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: "Data Sharing",
    stat: <Stat value="15,112,893" change="112,893" trend="up" />,
    footer: <Sparkline data={upwardTrendData} />,
  },
};

export const DownTrend: Story = {
  args: {
    title: "Active Users",
    stat: <Stat value="8,430" change="1,204" trend="down" />,
    footer: <Sparkline data={downwardTrendData} />,
  },
};

export const NoChange: Story = {
  args: {
    title: "Total Requests",
    stat: <Stat value="3,201,554" />,
    footer: <Sparkline data={neutralTrendData} />,
  },
};

export const NoFooter: Story = {
  args: {
    title: "Data Sharing",
    stat: <Stat value="15,112,893" change="112,893" trend="up" />,
  },
};

export const WithContentAndFooter: Story = {
  args: {
    title: "Data Sharing",
    stat: <Stat value="15,112,893" change="112,893" trend="up" />,
    content: <ContentPlaceholder />,
    footer: <Sparkline data={upwardTrendData} />,
  },
};

export const Loading: Story = {
  args: {
    title: "Data Sharing",
    stat: <Stat value="15,112,893" change="112,893" trend="up" />,
    loading: true,
  },
};

export const DashboardRow: Story = {
  args: {
    title: "Data Sharing",
    stat: <Stat value="15,112,893" change="112,893" trend="up" />,
  },
  decorators: [
    () => (
      <div className="grid grid-cols-3 gap-4 w-[900px]">
        <StatCard
          title="Data Sharing"
          stat={<Stat value="15,112,893" change="112,893" trend="up" />}
          footer={<Sparkline data={upwardTrendData} />}
        />
        <StatCard
          title="Active Users"
          stat={<Stat value="8,430" change="1,204" trend="down" />}
          footer={<Sparkline data={downwardTrendData} />}
        />
        <StatCard
          title="Total Requests"
          stat={<Stat value="3,201,554" />}
          footer={<Sparkline data={neutralTrendData} />}
        />
      </div>
    ),
  ],
};
