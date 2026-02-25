import type { Meta, StoryObj } from "@storybook/react-vite";

import { Input } from "../../index";
import { TITLE_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";
import { inputVariantControl } from "./Input.controls";

const meta = {
  title: "Data Entry/Input",
  component: Input,
  tags: ["autodocs"],
} satisfies Meta<typeof Input>;

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

export const Filled: Story = {
  args: {
    value: TITLE_LOREM,
    variant: "filled",
  },
};

export const Borderless: Story = {
  args: {
    value: TITLE_LOREM,
    variant: "borderless",
  },
};

export const Outlined: Story = {
  args: {
    value: TITLE_LOREM,
    variant: "outlined",
  },
};

export const Underlined: Story = {
  args: {
    value: TITLE_LOREM,
    variant: "underlined",
  },
};
