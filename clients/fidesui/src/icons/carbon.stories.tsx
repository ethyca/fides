import type { Meta, StoryObj } from "@storybook/react-vite";
import { Flex, Input, Typography } from "antd";
import { useState } from "react";

import * as CarbonIcons from "./carbon";

const iconEntries = Object.entries(CarbonIcons).filter(
  ([, value]) => value != null,
) as [string, React.ComponentType<{ size?: number }>][];

const meta: Meta = {
  title: "General/Icons/Carbon Icons",
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj;

export const Gallery: Story = {
  render: () => {
    const [filter, setFilter] = useState("");
    const filtered = iconEntries.filter(([name]) =>
      name.toLowerCase().includes(filter.toLowerCase()),
    );

    return (
      <Flex vertical gap={16}>
        <Input
          placeholder="Filter icons..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          allowClear
          style={{ maxWidth: 300 }}
        />
        <Typography.Text type="secondary">
          {filtered.length} of {iconEntries.length} icons
        </Typography.Text>
        <Flex wrap gap={8}>
          {filtered.map(([name, Icon]) => (
            <Flex
              key={name}
              vertical
              align="center"
              gap={4}
              style={{
                width: 120,
                padding: 12,
                borderRadius: 6,
                border: "1px solid #f0f0f0",
              }}
            >
              <Icon size={24} />
              <Typography.Text
                style={{ fontSize: 11, textAlign: "center" }}
                ellipsis
              >
                {name}
              </Typography.Text>
            </Flex>
          ))}
        </Flex>
      </Flex>
    );
  },
};
