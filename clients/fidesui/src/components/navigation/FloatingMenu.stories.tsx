import type { Meta, StoryObj } from "@storybook/react-vite";

import { FloatingMenu } from "./FloatingMenu";
import { Primary as MenuStory } from "./Menu.stories";

const meta = {
  title: "Navigation/FloatingMenu",
  component: FloatingMenu,
  tags: ["autodocs"],
} satisfies Meta<typeof FloatingMenu>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: MenuStory.args,
};
