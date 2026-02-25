import type { Meta, StoryObj } from "@storybook/react-vite";

import { CustomList } from "../../hoc/CustomList";
import { Avatar, Typography } from "../../index";
import { SUBTITLE_LOREM, TITLE_LOREM } from "../../stories/utils/content";

const {
  Item: { Meta: ListMeta },
} = CustomList;

const meta = {
  title: "Data Entry/List/ItemMeta",
  component: ListMeta,
  args: {},
  argTypes: {},
  tags: ["autodocs"],
} satisfies Meta<typeof ListMeta>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    avatar: <Avatar />,
    description: SUBTITLE_LOREM,
    title: <Typography.Text>{TITLE_LOREM}</Typography.Text>,
  },
};
