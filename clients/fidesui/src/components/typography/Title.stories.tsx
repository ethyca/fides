import type { Meta, StoryObj } from "@storybook/react-vite";

import { GetProps, Typography } from "../../index";
import { TITLE_LOREM } from "../../stories/utils/content";

const { Title } = Typography;

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
  tags: ["autodocs"],
} satisfies Meta<typeof Title>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
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
};

export const Level1: Story = {
  args: {
    level: 1,
  },
};

export const Level2: Story = {
  args: {
    level: 2,
  },
};

export const Level3: Story = {
  args: {
    level: 3,
  },
};

export const Level4: Story = {
  args: {
    level: 4,
  },
};

export const Level5: Story = {
  args: {
    level: 5,
  },
};
