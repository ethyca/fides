import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button, Flex, Typography } from "antd/lib";
import { useState } from "react";

import type { CardProps } from "../index";
import { Card } from "../index";

const { Title, Text } = Typography;

const COVER_POSITION: Record<
  NonNullable<CardProps["coverPosition"]>,
  CardProps["coverPosition"]
> = {
  top: "top",
  bottom: "bottom",
};

const meta = {
  title: "Data Display/Card",
  component: Card,
  args: {
    title: "Card Title",
    variant: "borderless",
    children: <div>Card body content</div>,
  },
  argTypes: {
    coverPosition: {
      control: "select",
      options: Object.values(COVER_POSITION),
    },
  },
  decorators: [
    (Story) => (
      <div className="w-96">
        <Story />
      </div>
    ),
  ],
  tags: ["autodocs"],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

const TAB_CONTENT: Record<string, string> = {
  a: "Content A",
  b: "Content B",
  c: "Content C",
};

const TAB_LIST = [
  { key: "a", label: "Tab A" },
  { key: "b", label: "Tab B" },
  { key: "c", label: "Tab C" },
];

export const WithTabs: Story = {
  args: {
    variant: "borderless",
    title: "Overview",
  },
  render: (args) => {
    const [activeTab, setActiveTab] = useState("a");
    return (
      <div className="w-[400px]">
        <Card
          {...args}
          tabList={TAB_LIST}
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

export const WithExtra: Story = {
  args: {
    title: "Access Request Policy",
    extra: (
      <Flex gap="small">
        <Button>Edit</Button>
        <Button danger>Delete</Button>
      </Flex>
    ),
    children: (
      <Flex vertical gap="small">
        <Text type="secondary" code>
          default_access_policy
        </Text>
        <Text type="secondary">Execution timeframe: 45 days</Text>
      </Flex>
    ),
  },
};

/* ------------------------------------------------------------------ */
/*  Comparison: existing Title-in-body vs title prop                   */
/* ------------------------------------------------------------------ */

const CompareLabel = ({ children }: { children: React.ReactNode }) => (
  <Text type="secondary" strong className="mb-2 block text-xs uppercase">
    {children}
  </Text>
);

export const CompareTitleInBody: Story = {
  name: "Compare: Title in body vs title prop",
  decorators: [
    () => (
      <Flex gap="middle" className="w-[800px]">
        <div className="flex-1">
          <CompareLabel>Existing (Title in body)</CompareLabel>
          <Card>
            <Flex vertical gap="small">
              <Title level={5}>Access Request Policy</Title>
              <Text type="secondary" code>
                default_access_policy
              </Text>
              <Text type="secondary">Execution timeframe: 45 days</Text>
            </Flex>
          </Card>
        </div>
        <div className="flex-1">
          <CompareLabel>New (title prop)</CompareLabel>
          <Card title="Access Request Policy">
            <Flex vertical gap="small">
              <Text type="secondary" code>
                default_access_policy
              </Text>
              <Text type="secondary">Execution timeframe: 45 days</Text>
            </Flex>
          </Card>
        </div>
      </Flex>
    ),
  ],
};

export const CompareWithActions: Story = {
  name: "Compare: Actions in body vs extra prop",
  decorators: [
    () => (
      <Flex gap="middle" className="w-[800px]">
        <div className="flex-1">
          <CompareLabel>Existing (buttons in body)</CompareLabel>
          <Card>
            <Flex justify="space-between" align="flex-start">
              <Flex vertical gap="small">
                <Title level={5}>Access Request Policy</Title>
                <Text type="secondary" code>
                  default_access_policy
                </Text>
                <Text type="secondary">Execution timeframe: 45 days</Text>
              </Flex>
              <Flex gap="small">
                <Button>Edit</Button>
                <Button danger>Delete</Button>
              </Flex>
            </Flex>
          </Card>
        </div>
        <div className="flex-1">
          <CompareLabel>New (extra prop)</CompareLabel>
          <Card
            title="Access Request Policy"
            extra={
              <Flex gap="small">
                <Button>Edit</Button>
                <Button danger>Delete</Button>
              </Flex>
            }
          >
            <Flex vertical gap="small">
              <Text type="secondary" code>
                default_access_policy
              </Text>
              <Text type="secondary">Execution timeframe: 45 days</Text>
            </Flex>
          </Card>
        </div>
      </Flex>
    ),
  ],
};
