import type { Meta, StoryObj } from "@storybook/react-vite";

import { GetProps, Typography } from "../../index";
import { SUBTITLE_LOREM } from "../../stories/utils/content";

const { Text } = Typography;

type TextType = NonNullable<GetProps<typeof Text>["type"]>;

const TEXT_TYPE: Record<TextType, TextType> = {
  danger: "danger",
  secondary: "secondary",
  success: "success",
  warning: "warning",
};

const meta = {
  title: "General/Typography/Text",
  component: Text,
  args: {
    children: SUBTITLE_LOREM,
  },
  argTypes: {
    code: {
      control: "boolean",
    },
    copyable: {
      control: "boolean",
    },
    delete: {
      control: "boolean",
    },
    disabled: {
      control: "boolean",
    },
    editable: {
      control: "boolean",
    },
    ellipsis: {
      control: "boolean",
    },
    keyboard: {
      control: "boolean",
    },
    mark: {
      control: "boolean",
    },
    strong: {
      control: "boolean",
    },
    italic: {
      control: "boolean",
    },
    type: {
      control: "select",
      options: Object.values(TEXT_TYPE),
    },
    underline: {
      control: "boolean",
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Text>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};
