import type { Meta, StoryObj } from "@storybook/react-vite";

import { Tooltip } from "../../index";
import { PARAGRAPH_LOREM, TITLE_LOREM } from "../../stories/utils/content";

const meta = {
  title: "Data Display/Tooltip",
  component: Tooltip,
  tags: ["autodocs"],
} satisfies Meta<typeof Tooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    children: TITLE_LOREM,
    title: PARAGRAPH_LOREM,
  },
};

export const Opened: Story = {
  args: {
    children: TITLE_LOREM,
    title: PARAGRAPH_LOREM,
    open: true,
  },
};
