import type { Meta, StoryObj } from "@storybook/react-vite";
import { GetProps } from "antd";

import { Typography } from "../../index";
import { PARAGRAPH_LOREM } from "../../stories/utils/content";

const { Paragraph } = Typography;

type ParagraphType = NonNullable<GetProps<typeof Paragraph>["type"]>;

const PARAGRAPH_TYPE: Record<ParagraphType, ParagraphType> = {
  danger: "danger",
  secondary: "secondary",
  success: "success",
  warning: "warning",
};

const meta = {
  title: "General/Typography/Paragraph",
  component: Paragraph,
  args: {
    children: PARAGRAPH_LOREM,
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
    italic: {
      control: "boolean",
    },
    type: {
      control: "select",
      options: Object.values(PARAGRAPH_TYPE),
    },
    underline: {
      control: "boolean",
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Paragraph>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};

export const Ellipsis: Story = {
  args: {
    ellipsis: true,
  },
};
