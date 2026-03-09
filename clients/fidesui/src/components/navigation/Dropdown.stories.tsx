import type { Meta, StoryObj } from "@storybook/react-vite";

import type { DropdownProps } from "../../index";
import { Button, Dropdown } from "../../index";
import { Primary as MenuStory } from "./Menu.stories";

const TriggerOptions: DropdownProps["trigger"] = [
  "contextMenu",
  "click",
  "hover",
];

const meta = {
  title: "Navigation/Dropdown",
  component: Dropdown,
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
  args: {
    menu: MenuStory.args,
    children: <Button>Target</Button>,
    open: true,
  },
};
