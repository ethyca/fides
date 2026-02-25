import type { Meta, StoryObj } from "@storybook/react-vite";

import { Input } from "../../index";
import { PARAGRAPH_LOREM } from "../../stories/utils/content";
import { inputVariantControl } from "./Input.controls";

const { TextArea } = Input;

const meta = {
  title: "Data Entry/Input/TextArea",
  component: TextArea,
  tags: ["autodocs"],
} satisfies Meta<typeof TextArea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  argTypes: {
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
  },
};

export const Placeholder: Story = {
  args: {
    placeholder: PARAGRAPH_LOREM,
  },
};

export const WithValue: Story = {
  args: {
    value: PARAGRAPH_LOREM,
  },
};
