import type { Meta, StoryObj } from "@storybook/react-vite";

import { Icons, List, Typography } from "../../index";
import { Primary as ListItemMetaStory } from "./List.Item.Meta.stories";

const { Item } = List;

const meta = {
  title: "Data Entry/List/Item",
  component: Item,
  tags: ["autodocs"],
} satisfies Meta<typeof Item>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    actions: [<Icons.Star key="1" />, <Icons.Share key="2" />],
    children: (
      <>
        <Item.Meta {...ListItemMetaStory.args} />
        <Typography.Paragraph>Lorem Ipsum</Typography.Paragraph>
      </>
    ),
  },
};
