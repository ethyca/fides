import type { Meta, StoryObj } from "@storybook/react-vite";

import { Tag } from "../../index";
import { TITLE_LOREM } from "../../stories/utils/content";

const meta = {
  title: "Data Display/Tag",
  component: Tag,
  args: {
    children: TITLE_LOREM,
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Tag>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};
