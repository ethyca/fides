import type { Meta, StoryObj } from "@storybook/react-vite";

import { Input } from "../../index";
import { TITLE_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";
import { inputVariantControl } from "./Input.controls";

const { Search } = Input;

const meta = {
  title: "Data Entry/Input/Search",
  component: Search,
  tags: ["autodocs"],
} satisfies Meta<typeof Search>;

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
