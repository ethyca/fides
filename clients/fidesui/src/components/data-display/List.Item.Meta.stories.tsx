import type { Meta, StoryObj } from "@storybook/react-vite";

import { Avatar, List, Typography } from "../../index";
import { PARAGRAPH_LOREM, TITLE_LOREM } from "../../stories/utils/content";

const {
  Item: { Meta: ListItemMeta },
} = List;

const meta = {
  title: "Data Entry/List/ItemMeta",
  component: ListItemMeta,
  tags: ["autodocs"],
} satisfies Meta<typeof ListItemMeta>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    avatar: <Avatar />,
    description: PARAGRAPH_LOREM,
    title: <Typography.Text>{TITLE_LOREM}</Typography.Text>,
  },
};
