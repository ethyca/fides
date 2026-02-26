import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { theme } from "antd";

import { CustomCard } from "../../hoc/CustomCard";
import { CustomStatistic } from "../../hoc/CustomStatistic";
import { RadarChart } from "../charts/RadarChart";
import { Sparkline } from "../charts/Sparkline";

const upwardTrendData = [12, 18, 15, 22, 28, 25, 34, 30, 38, 42, 39, 47];

const downwardTrendData = [47, 42, 45, 38, 34, 36, 28, 24, 26, 18, 15, 12];

const neutralTrendData = [28, 32, 25, 30, 27, 33, 26, 31, 28, 34, 29, 30];

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
        'Cover content (e.g. a sparkline). Set `coverPosition="bottom"` to display it below the card body.',
      control: false,
    },
    children: {
      description: "Card body content, e.g. `<CustomStatistic />` component.",
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
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <CustomCard title="Posture" {...args}>
        <>
          <CustomStatistic value="67" />
          <CustomStatistic
            trend="up"
            value="112,893"
            prefix={<ArrowUpOutlined />}
            valueStyle={{ fontSize: token.fontSize }}
          />
          <div
            className="h-48"
            style={{
              marginLeft: -token.paddingLG,
              marginRight: -token.paddingLG,
            }}
          >
            <RadarChart
              data={[
                { subject: "Coverage", value: 80 },
                { subject: "Classification", value: 65 },
                { subject: "Consent", value: 50, status: "warning" },
                { subject: "DSR", value: 30, status: "error" },
                { subject: "Enforcement", value: 70 },
                { subject: "Assessments", value: 45, status: "warning" },
              ]}
            />
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
