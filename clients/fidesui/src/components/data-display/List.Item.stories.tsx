import type { Meta, StoryObj } from "@storybook/react-vite";

import { CustomList } from "../../hoc/CustomList";
import { Icons, Typography } from "../../index";
import { Primary as ListItemMeta } from "./List.Item.Meta.stories";

const { Item } = CustomList;

const meta = {
  title: "Data Entry/List/Item",
  component: Item,
  args: {},
  argTypes: {},
  tags: ["autodocs"],
} satisfies Meta<typeof Item>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    actions: [<Icons.Star key="1" />, <Icons.Share key="2" />],
    children: (
      <>
        <Item.Meta {...ListItemMeta.args} />
        <Typography.Paragraph>Lorem Ipsum</Typography.Paragraph>
      </>
    ),
  },
};
