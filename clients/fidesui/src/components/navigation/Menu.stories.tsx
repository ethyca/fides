import type { Meta, StoryObj } from "@storybook/react-vite";

import { Menu } from "../../index";

const meta = {
  title: "Navigation/Menu",
  args: {
    selectable: false,
    selectedKeys: ["2"],
  },
  argTypes: {},
} satisfies Meta<typeof Menu>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  render: (args) => (
    <Menu
      {...args}
      items={[
        {
          key: 1,
          label: "menu 1",
        },
        {
          key: 2,
          label: "menu 2",
        },
      ]}
    />
  ),
};
