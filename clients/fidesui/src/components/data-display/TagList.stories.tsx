import type { Meta, StoryObj } from "@storybook/react-vite";

import { TagList } from "../../index";

const meta = {
  title: "Data Display/TagList",
  component: TagList,
  tags: ["autodocs"],
} satisfies Meta<typeof TagList>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    tags: [...Array(10)].map((_, i) => String(i)),
  },
  argTypes: {
    maxTags: {
      control: "number",
    },
    expandable: {
      control: "boolean",
    },
  },
};

export const Expandable: Story = {
  args: {
    tags: [...Array(10)].map((_, i) => String(i)),
    expandable: true,
  },
};
