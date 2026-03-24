import type { Meta, StoryObj } from "@storybook/react-vite";
import { Flex, List, Typography } from "antd";

import {
  ArrowDownRightIcon,
  CompassIcon,
  ManualSetupIcon,
  MonitorIcon,
  SparkleIcon,
} from "./index";

const icons = [
  { name: "ArrowDownRightIcon", component: ArrowDownRightIcon },
  { name: "CompassIcon", component: CompassIcon },
  { name: "ManualSetupIcon", component: ManualSetupIcon },
  { name: "MonitorIcon", component: MonitorIcon },
  { name: "SparkleIcon", component: SparkleIcon },
];

const meta = {
  title: "General/Custom Icons",
  tags: ["autodocs"],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const Gallery: Story = {
  render: () => (
    <List
      dataSource={icons}
      renderItem={(item) => (
        <List.Item>
          <Flex align="center" gap={16}>
            <item.component size={24} />
            <Typography.Text code>{item.name}</Typography.Text>
          </Flex>
        </List.Item>
      )}
    />
  ),
};

export const ArrowDownRight: Story = {
  args: { size: 24 },
  argTypes: { size: { control: { type: "range", min: 8, max: 64 } } },
  render: (args) => <ArrowDownRightIcon size={args.size as number} />,
};

export const Compass: Story = {
  args: { size: 24 },
  argTypes: { size: { control: { type: "range", min: 8, max: 64 } } },
  render: (args) => <CompassIcon size={args.size as number} />,
};

export const ManualSetup: Story = {
  args: { size: 24 },
  argTypes: { size: { control: { type: "range", min: 8, max: 64 } } },
  render: (args) => <ManualSetupIcon size={args.size as number} />,
};

export const Monitor: Story = {
  args: { size: 24 },
  argTypes: { size: { control: { type: "range", min: 8, max: 64 } } },
  render: (args) => <MonitorIcon size={args.size as number} />,
};

export const Sparkle: Story = {
  args: { size: 24 },
  argTypes: { size: { control: { type: "range", min: 8, max: 64 } } },
  render: (args) => <SparkleIcon size={args.size as number} />,
};
