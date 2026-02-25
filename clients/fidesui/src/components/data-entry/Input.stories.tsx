// import type { CustomInputProps } from "../../hoc";
import type { Meta, StoryObj } from "@storybook/react-vite";

import { CustomInput } from "../../hoc";

const meta = {
  title: "Data Entry/Input",
  component: CustomInput,
  args: {},
  argTypes: {},
  tags: ["autodocs"],
} satisfies Meta<typeof CustomInput>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};
