import type { Meta, StoryObj } from "@storybook/react-vite";

import type { ListProps } from "../../index";
import { Button, List, Typography } from "../../index";
import { TITLE_LOREM } from "../../stories/utils/content";
import { Primary as ListItem } from "./List.Item.stories";

type ListItemLayout = NonNullable<ListProps<unknown>["itemLayout"]>;

type ListItemSize = NonNullable<ListProps<unknown>["size"]>;

const LIST_ITEM_SIZE: Record<ListItemSize, ListItemSize> = {
  default: "default",
  small: "small",
  large: "large",
};
const LIST_ITEM_LAYOUT: Record<ListItemLayout, ListItemLayout> = {
  horizontal: "horizontal",
  vertical: "vertical",
};

const meta = {
  title: "Data Entry/List",
  component: List,
  tags: ["autodocs"],
} satisfies Meta<typeof List>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    dataSource: [...Array(5)].map((_, i) => i),
    renderItem: (key) => <List.Item {...ListItem.args} key={Number(key)} />,
  },
  argTypes: {
    itemLayout: {
      control: "select",
      options: Object.values(LIST_ITEM_LAYOUT),
    },
    size: {
      control: "select",
      options: Object.values(LIST_ITEM_SIZE),
    },
    bordered: {
      control: "boolean",
    },
    header: {
      control: "text",
    },
    loading: {
      control: "boolean",
    },
    footer: {
      control: "text",
    },
  },
};

export const ListWithHeader: Story = {
  args: {
    ...Primary.args,
    header: <Typography.Title>{TITLE_LOREM}</Typography.Title>,
  },
};

export const PaginatedList: Story = {
  args: {
    ...Primary.args,
    pagination: {
      current: 1,
      pageSize: 2,
    },
  },
};

export const LoadMoreList: Story = {
  args: {
    ...Primary.args,
    loadMore: <Button>Load More</Button>,
  },
};
