import type { Meta, StoryObj } from "@storybook/react-vite";

import { Drawer } from "../../index";
import { PARAGRAPH_LOREM, TITLE_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";

const meta = {
  title: "Feedback/Drawer",
  component: Drawer,
  tags: ["autodocs"],
} satisfies Meta<typeof Drawer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    open: true,
    title: TITLE_LOREM,
    children: PARAGRAPH_LOREM,
  },
  argTypes: {
    closable: {
      control: "boolean",
    },
    closeIcon: iconControl,
    mask: {
      control: "boolean",
    },
    loading: {
      control: "boolean",
    },
    width: {
      control: "select",
      options: ["md", "lg", "xl"],
    },
    placement: {
      control: "select",
      options: ["left", "right", "top", "bottom"],
    },
  },
};

export const Large: Story = {
  args: {
    ...Primary.args,
    width: "lg",
  },
};

export const ExtraLarge: Story = {
  args: {
    ...Primary.args,
    width: "xl",
  },
};

export const LeftPlacement: Story = {
  args: {
    ...Primary.args,
    placement: "left",
  },
};
