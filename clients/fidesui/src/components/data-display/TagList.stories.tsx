import type { Meta, StoryObj } from "@storybook/react-vite";

import { TagList } from "./TagList";

const meta = {
  title: "Data Display/TagList",
  component: TagList,
  args: {},
  argTypes: {
    maxTags: {
      control: "number",
    },
    expandable: {
      control: "boolean",
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof TagList>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    tags: [...Array(10)].map((_, i) => String(i)),
  },
};

export const Expandable: Story = {
  args: {
    tags: [...Array(10)].map((_, i) => String(i)),
    expandable: true,
  },
};
