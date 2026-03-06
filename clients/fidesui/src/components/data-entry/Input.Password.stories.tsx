import type { Meta, StoryObj } from "@storybook/react-vite";

import { Input } from "../../index";
import { TITLE_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";
import { inputVariantControl } from "./Input.controls";

const { Password } = Input;

const meta = {
  title: "Data Entry/Input/Password",
  component: Password,
  tags: ["autodocs"],
} satisfies Meta<typeof Password>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  argTypes: {
    addonAfter: iconControl,
    addonBefore: iconControl,
    maxLength: {
      control: "number",
    },
    minLength: {
      control: "number",
    },
    showCount: {
      control: "boolean",
    },
    placeholder: {
      control: "text",
    },
    allowClear: {
      control: "boolean",
    },
    variant: inputVariantControl,
    visibilityToggle: {
      control: "boolean",
    },
  },
};

export const Placeholder: Story = {
  args: {
    placeholder: TITLE_LOREM,
  },
};

export const WithValue: Story = {
  args: {
    value: TITLE_LOREM,
  },
};
