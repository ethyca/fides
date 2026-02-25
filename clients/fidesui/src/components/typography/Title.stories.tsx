import type { Meta, StoryObj } from "@storybook/react-vite";
import { GetProps } from "antd";

import { CustomTypography } from "../../hoc/CustomTypography";
import { TITLE_LOREM } from "../../stories/utils/content";

const { Title } = CustomTypography;

type TitleType = NonNullable<GetProps<typeof Title>["type"]>;

const TITLE_TYPE: Record<TitleType, TitleType> = {
  danger: "danger",
  secondary: "secondary",
  success: "success",
  warning: "warning",
};

const TITLE_LEVEL: Record<
  NonNullable<GetProps<typeof Title>["level"]>,
  GetProps<typeof Title>["level"]
> = {
  1: 1,
  2: 2,
  3: 3,
  4: 4,
  5: 5,
};

const meta = {
  title: "General/Typography/Title",
  component: Title,
  args: {
    children: TITLE_LOREM,
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
    level: {
      control: "select",
      options: Object.values(TITLE_LEVEL),
    },
    mark: {
      control: "boolean",
    },
    italic: {
      control: "boolean",
    },
    type: {
      control: "select",
      options: Object.values(TITLE_TYPE),
    },
    underline: {
      control: "boolean",
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Title>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};
