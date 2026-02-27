import type { Meta, StoryObj } from "@storybook/react-vite";

import { SelectInline } from "./SelectInline";

const meta = {
  title: "Data Entry/SelectInline",
  component: SelectInline,
  args: {},
  argTypes: {},
  tags: ["autodocs"],
} satisfies Meta<typeof SelectInline>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};
