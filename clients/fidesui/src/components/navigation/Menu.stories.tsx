import type { Meta, StoryObj } from "@storybook/react-vite";

import { Menu } from "../../index";
import { MENU_NAMES } from "../../stories/utils/content";

const meta = {
  title: "Navigation/Menu",
  component: Menu,
  argTypes: {
    selectable: {
      control: "boolean",
    },
  },
} satisfies Meta<typeof Menu>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    items: MENU_NAMES.map((name) => ({ key: name, label: name })),
    selectedKeys: [MENU_NAMES[0]],
  },
};
