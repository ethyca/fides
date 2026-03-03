import type { Meta, StoryObj } from "@storybook/react-vite";

import type { DropdownProps } from "../../index";
import { Dropdown } from "../../index";

const TriggerOptions: DropdownProps["trigger"] = [
  "contextMenu",
  "click",
  "hover",
];

const meta = {
  title: "Navigation/Dropdown",
  args: {
    menu: {
      selectable: false,
      selectedKeys: ["2"],
      items: [
        {
          key: 1,
          label: "menu 1",
        },

        {
          key: 2,
          label: "menu 2",
        },
      ],
    },
    open: true,
  },
  argTypes: {
    trigger: {
      control: "multi-select",
      options: TriggerOptions,
    },
  },
} satisfies Meta<typeof Dropdown>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  render: (args) => <Dropdown {...args}>Target</Dropdown>,
};
