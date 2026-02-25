import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { theme } from "antd";

import { CustomCard } from "../../hoc/CustomCard";
import { CustomStatistic } from "../../hoc/CustomStatistic";
import Sparkline from "../charts/Sparkline";

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
  component: CustomCard,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    coverPosition: {
      description:
        "Position of the cover relative to the card body. Use `bottom` to place a sparkline below the stat.",
      control: "radio",
      options: ["top", "bottom"],
    },
    cover: {
      description:
        "Cover content (e.g. a sparkline). Set `coverPosition=\"bottom\"` to display it below the card body.",
      control: false,
    },
    children: {
      description:
        "Card body content, e.g. `<CustomStatistic />` component.",
      control: false,
    },
  },
  decorators: [
    (Story) => (
      <div className="w-full min-w-72">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof CustomCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    variant: "borderless",
    cover: (
      <div className="h-16">
        <Sparkline data={upwardTrendData} />
      </div>
    ),
    coverPosition: "bottom",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <CustomCard {...args}>
        <CustomStatistic title="Data Sharing" value="15,112,893" />
        <CustomStatistic
          trend="up"
          value="112,893"
          prefix={<ArrowUpOutlined />}
          valueStyle={{ fontSize: token.fontSize }}
        />
      </CustomCard>
    );
  },
};

export const DownTrend: Story = {
  args: {
    variant: "borderless",
    cover: (
      <div className="h-16">
        <Sparkline data={downwardTrendData} />
      </div>
    ),
    coverPosition: "bottom",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <CustomCard {...args}>
        <CustomStatistic title="Active Users" value="8,430" />
        <CustomStatistic
          trend="down"
          value="1,204"
          prefix={<ArrowDownOutlined />}
          valueStyle={{ fontSize: token.fontSize }}
        />
      </CustomCard>
    );
  },
};

export const NoChange: Story = {
  args: {
    variant: "borderless",
    cover: (
      <div className="h-16">
        <Sparkline data={neutralTrendData} />
      </div>
    ),
    coverPosition: "bottom",
    children: <CustomStatistic title="Total Requests" value="3,201,554" />,
  },
};

export const NoFooter: Story = {
  args: {
    variant: "borderless",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <CustomCard {...args}>
        <CustomStatistic title="Data Sharing" value="15,112,893" />
        <CustomStatistic
          trend="up"
          value="112,893"
          prefix={<ArrowUpOutlined />}
          valueStyle={{ fontSize: token.fontSize }}
        />
      </CustomCard>
    );
  },
};

export const WithContentAndFooter: Story = {
  args: {
    variant: "borderless",
    cover: (
      <div className="h-16">
        <Sparkline data={upwardTrendData} />
      </div>
    ),
    coverPosition: "bottom",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <CustomCard {...args}>
        <>
          <CustomStatistic title="Data Sharing" value="15,112,893" />
          <CustomStatistic
            trend="up"
            value="112,893"
            prefix={<ArrowUpOutlined />}
            valueStyle={{ fontSize: token.fontSize }}
          />
          <div className="mt-3">
            <ContentPlaceholder />
          </div>
        </>
      </CustomCard>
    );
  },
};

export const Loading: Story = {
  args: {
    variant: "borderless",
    loading: true,
    children: <CustomStatistic title="Data Sharing" value="15,112,893" />,
  },
};

export const DashboardRow: Story = {
  args: {},
  decorators: [
    () => {
      const { token } = theme.useToken();
      return (
        <div className="grid grid-cols-3 gap-4 w-[900px]">
          <CustomCard
            variant="borderless"
            title="Data Sharing"
            cover={
              <div className="h-16">
                <Sparkline data={upwardTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <CustomStatistic value="15,112,893" />
            <CustomStatistic
              trend="up"
              value="112,893"
              prefix={<ArrowUpOutlined />}
              valueStyle={{ fontSize: token.fontSize }}
            />
          </CustomCard>
          <CustomCard
            variant="borderless"
            title="Active Users"
            cover={
              <div className="h-16">
                <Sparkline data={downwardTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <CustomStatistic value="8,430" />
            <CustomStatistic
              trend="down"
              value="1,204"
              prefix={<ArrowDownOutlined />}
              valueStyle={{ fontSize: token.fontSize }}
            />
          </CustomCard>
          <CustomCard
            variant="borderless"
            title="Total Requests"
            cover={
              <div className="h-16">
                <Sparkline data={neutralTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <CustomStatistic value="3,201,554" />
          </CustomCard>
        </div>
      );
    },
  ],
};
