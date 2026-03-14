import type { Meta, StoryObj } from "@storybook/react-vite";
import {
  Avatar,
  Button,
  Divider,
  Flex,
  Progress,
  Space,
  Steps,
  Tag,
  Typography,
} from "antd/lib";
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

const TITLE_FONT: Record<
  NonNullable<CardProps["titleFont"]>,
  CardProps["titleFont"]
> = {
  default: "default",
  mono: "mono",
};

const meta = {
  title: "Data Display/Card",
  component: Card,
  args: {
    title: "Card Title",
    variant: "borderless",
    children: <div className="p-2">Card body content</div>,
  },
  argTypes: {
    coverPosition: {
      control: "select",
      options: Object.values(COVER_POSITION),
    },
    titleFont: {
      control: "select",
      options: Object.values(TITLE_FONT),
    },
    showTitleDivider: {
      control: "boolean",
    },
    titleHeading: {
      control: "boolean",
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

/* ------------------------------------------------------------------ */
/*  New custom props                                                   */
/* ------------------------------------------------------------------ */

export const Default: Story = {};

export const MonoTitle: Story = {
  args: {
    titleFont: "mono",
  },
};

export const NoDivider: Story = {
  args: {
    showTitleDivider: false,
  },
};

/** Opt out of titleHeading to get the classic Ant Design card header */
export const ClassicHeader: Story = {
  args: {
    titleHeading: false,
    showTitleDivider: true,
  },
};

export const MonoNoDivider: Story = {
  args: {
    titleFont: "mono",
    showTitleDivider: false,
  },
};

/* ------------------------------------------------------------------ */
/*  Side-by-side comparisons: existing (Title in body) vs title prop   */
/* ------------------------------------------------------------------ */

const CompareLabel = ({ children }: { children: React.ReactNode }) => (
  <Text type="secondary" strong className="mb-2 block text-xs uppercase">
    {children}
  </Text>
);

/** PolicyBox pattern — existing Title-in-body vs title prop */
export const ComparePolicyBox: Story = {
  name: "Compare: PolicyBox",
  decorators: [
    () => (
      <Flex gap="middle" className="w-[800px]">
        <div className="flex-1">
          <CompareLabel>Existing (Title in body)</CompareLabel>
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
          <CompareLabel>New (title prop)</CompareLabel>
          <Card title="Access Request Policy">
            <Flex justify="space-between" align="flex-start">
              <Flex vertical gap="small">
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
      </Flex>
    ),
  ],
};

/** ConfigurationCard pattern — existing JSX-in-title vs titleHeading */
export const CompareConfigurationCard: Story = {
  name: "Compare: ConfigurationCard",
  decorators: [
    () => (
      <Flex gap="middle" className="w-[800px]">
        <div className="flex-1">
          <CompareLabel>Existing (JSX title prop)</CompareLabel>
          <Card
            titleHeading={false}
            title={
              <Space>
                <Avatar size={24}>C</Avatar>
                <Title level={5} style={{ margin: 0 }}>
                  Configuration
                </Title>
              </Space>
            }
          >
            <Flex vertical gap="middle" className="py-2">
              <Text type="secondary">Provider settings go here.</Text>
              <Button type="primary">Save</Button>
            </Flex>
          </Card>
        </div>
        <div className="flex-1">
          <CompareLabel>New (title prop + titleHeading)</CompareLabel>
          <Card title="Configuration">
            <Flex vertical gap="middle" className="py-2">
              <Text type="secondary">Provider settings go here.</Text>
              <Button type="primary">Save</Button>
            </Flex>
          </Card>
        </div>
      </Flex>
    ),
  ],
};

/** AssessmentCard pattern — existing Title-in-body vs title prop */
export const CompareAssessmentCard: Story = {
  name: "Compare: AssessmentCard",
  decorators: [
    () => {
      const assessmentBody = (
        <>
          <Text type="secondary">
            Processing <Tag>user.behavior</Tag> for <Tag>analytics</Tag>
          </Text>
          <Tag color="orange">Medium risk</Tag>
          <Divider className="my-3" />
          <Flex justify="space-between">
            <Text type="secondary">Completeness</Text>
            <Text strong>65%</Text>
          </Flex>
          <Progress percent={65} showInfo={false} size="small" />
          <Flex justify="space-between" align="center" className="mt-1">
            <Text type="secondary">In progress</Text>
            <Button type="link" className="p-0">
              Resume
            </Button>
          </Flex>
        </>
      );
      return (
        <Flex gap="middle" className="w-[800px]">
          <div className="flex-1">
            <CompareLabel>Existing (Title in body)</CompareLabel>
            <Card>
              <Flex vertical gap="small" justify="space-between">
                <Title level={5} style={{ marginBottom: "auto" }}>
                  User Analytics Assessment
                </Title>
                {assessmentBody}
              </Flex>
            </Card>
          </div>
          <div className="flex-1">
            <CompareLabel>New (title prop)</CompareLabel>
            <Card title="User Analytics Assessment">
              <Flex vertical gap="small" justify="space-between">
                {assessmentBody}
              </Flex>
            </Card>
          </div>
        </Flex>
      );
    },
  ],
};

/** IntegrationSetupSteps pattern — classic header vs titleHeading */
export const CompareIntegrationSetup: Story = {
  name: "Compare: IntegrationSetupSteps",
  decorators: [
    () => {
      const stepsContent = (
        <Steps
          direction="vertical"
          current={1}
          size="small"
          items={[
            { title: "Create integration", status: "finish" as const },
            { title: "Authorize integration", status: "process" as const },
            { title: "Create monitor", status: "wait" as const },
          ]}
        />
      );
      return (
        <Flex gap="middle" className="w-[800px]">
          <div className="flex-1">
            <CompareLabel>Existing (classic header)</CompareLabel>
            <Card title="Integration setup" titleHeading={false}>
              {stepsContent}
            </Card>
          </div>
          <div className="flex-1">
            <CompareLabel>New (titleHeading default)</CompareLabel>
            <Card title="Integration setup">{stepsContent}</Card>
          </div>
        </Flex>
      );
    },
  ],
};

/* ------------------------------------------------------------------ */
/*  Tab stories                                                        */
/* ------------------------------------------------------------------ */

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
