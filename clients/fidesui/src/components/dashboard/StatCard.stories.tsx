import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { theme } from "antd";
import { Card, Statistic } from "fidesui";
import { useState } from "react";

import { RadarChart } from "../charts/RadarChart";
import { Sparkline } from "../charts/Sparkline";

const upwardTrendData = [12, 18, 15, 22, 28, 25, 34, 30, 38, 42, 39, 47];

const downwardTrendData = [47, 42, 45, 38, 34, 36, 28, 24, 26, 18, 15, 12];

const neutralTrendData = [28, 32, 25, 30, 27, 33, 26, 31, 28, 34, 29, 30];

const meta = {
  title: "Dashboard/Card",
  component: Card,
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
      description: "Card body content, e.g. `<Statistic />` component.",
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
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    variant: "borderless",
    coverPosition: "bottom",
    title: "Default Card",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <Card {...args}>
        <Statistic title="Data Sharing" value="15,112,893" />
        <Statistic
          trend="up"
          value="112,893"
          prefix={<ArrowUpOutlined />}
          valueStyle={{ fontSize: token.fontSize }}
        />
      </Card>
    );
  },
};

export const NoTitle: Story = {
  args: {
    variant: "borderless",
    coverPosition: "bottom",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <Card {...args}>
        <Statistic title="Data Sharing" value="15,112,893" />
        <Statistic
          trend="up"
          value="112,893"
          prefix={<ArrowUpOutlined />}
          valueStyle={{ fontSize: token.fontSize }}
        />
      </Card>
    );
  },
};

export const WithSparkline: Story = {
  args: {
    variant: "borderless",
    cover: (
      <div className="h-16">
        <Sparkline data={downwardTrendData} />
      </div>
    ),
    title: "Active Users",
    coverPosition: "bottom",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <Card {...args}>
        <Statistic title="Active Users" value="8,430" />
        <Statistic
          trend="down"
          value="1,204"
          prefix={<ArrowDownOutlined />}
          valueStyle={{ fontSize: token.fontSize }}
        />
      </Card>
    );
  },
};

export const WithRadarChart: Story = {
  args: {
    variant: "borderless",
  },
  render: (args) => {
    const { token } = theme.useToken();
    return (
      <Card title="Posture" {...args}>
        <>
          <Statistic value="67" />
          <Statistic
            trend="up"
            value="4"
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
      </Card>
    );
  },
};

export const Loading: Story = {
  args: {
    variant: "borderless",
    loading: true,
    children: <Statistic title="Data Sharing" value="15,112,893" />,
  },
};

const TAB_CONTENT: Record<string, string> = {
  a: "Content A",
  b: "Content B",
  c: "Content C",
};

export const WithTabs: Story = {
  args: {
    variant: "borderless",
    title: "Overview",
  },
  render: (args) => {
    const [activeTab, setActiveTab] = useState("a");
    return (
      <Card
        {...args}
        tabList={[
          { key: "a", label: "Tab A" },
          { key: "b", label: "Tab B" },
          { key: "c", label: "Tab C" },
        ]}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
          <Flex align="center" justify="center" className="bg-gray-50 p-8">
            {TAB_CONTENT[activeTab]}
          </Flex>
      </Card>
    );
  },
};

export const WithInlineTabs: Story = {
  args: {
    variant: "borderless",
    title: "Overview",
    headerLayout: "inline",
  },
  render: (args) => {
    const [activeTab, setActiveTab] = useState("a");
    return (
      <div className="w-[400px]">
        <Card
          {...args}
          tabList={[
            { key: "a", label: "Tab A" },
            { key: "b", label: "Tab B" },
            { key: "c", label: "Tab C" },
          ]}
          activeTabKey={activeTab}
          onTabChange={setActiveTab}
        >
          <div className="flex items-center justify-center bg-gray-50 p-8">
            {TAB_CONTENT[activeTab]}
          </div>
        </Card>
      </div>
    );
  },
};

export const DashboardRow: Story = {
  args: {},
  decorators: [
    () => {
      const { token } = theme.useToken();
      return (
        <div className="grid grid-cols-3 gap-4 w-[900px]">
          <Card
            variant="borderless"
            title="Data Sharing"
            className="overflow-clip"
            cover={
              <div className="h-16">
                <Sparkline data={upwardTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <Statistic value="15,112,893" />
            <Statistic
              trend="up"
              value="112,893"
              prefix={<ArrowUpOutlined />}
              valueStyle={{ fontSize: token.fontSize }}
            />
          </Card>
          <Card
            variant="borderless"
            title="Active Users"
            className="overflow-clip"
            cover={
              <div className="h-16">
                <Sparkline data={downwardTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <Statistic value="8,430" />
            <Statistic
              trend="down"
              value="1,204"
              prefix={<ArrowDownOutlined />}
              valueStyle={{ fontSize: token.fontSize }}
            />
          </Card>
          <Card
            variant="borderless"
            title="Total Requests"
            className="overflow-clip"
            cover={
              <div className="h-16">
                <Sparkline data={neutralTrendData} />
              </div>
            }
            coverPosition="bottom"
          >
            <Statistic value="3,201,554" />
          </Card>
        </div>
      );
    },
  ],
};
