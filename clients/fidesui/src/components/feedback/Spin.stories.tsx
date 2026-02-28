import type { Meta, StoryObj } from "@storybook/react-vite";

import { GetProps, Spin } from "../../index";

type SpinProps = GetProps<typeof Spin>;

type SpinSize = NonNullable<SpinProps["size"]>;

const SPIN_SIZE_OPTIONS: Record<SpinSize, SpinSize> = {
  default: "default",
  small: "small",
  large: "large",
};

const meta = {
  title: "Feedback/Spin",
  component: Spin,
  tags: ["autodocs"],
} satisfies Meta<typeof Spin>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
  argTypes: {
    size: {
      control: "select",
      options: Object.values(SPIN_SIZE_OPTIONS),
    },
    spinning: {
      control: "boolean",
    },
    fullscreen: {
      control: "boolean",
    },
  },
};

export const FullScreen: Story = {
  args: {
    fullscreen: true,
  },
};
