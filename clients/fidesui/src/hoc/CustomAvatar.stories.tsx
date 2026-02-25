import type { Meta, StoryObj } from "@storybook/react-vite";
import { Breakpoint } from "antd/lib";

import type { AvatarProps } from "../index";
import { Avatar } from "../index";
import { iconControl } from "../stories/utils/controls";

const AVATAR_SHAPE: Record<
  NonNullable<AvatarProps["shape"]>,
  AvatarProps["shape"]
> = {
  circle: "circle",
  square: "square",
};

const AVATAR_VARIANT: Record<
  NonNullable<AvatarProps["variant"]>,
  AvatarProps["variant"]
> = {
  outlined: "outlined",
  filled: "filled",
};

type AvatarSize = NonNullable<
  Exclude<AvatarProps["size"], number | Partial<Record<Breakpoint, number>>>
>;

const AVATAR_SIZE: Record<AvatarSize, AvatarSize> = {
  default: "default",
  small: "small",
  large: "large",
};

const meta = {
  title: "Data Display/Avatar",
  component: Avatar,
  args: {
    draggable: false,
    shape: "circle",
    size: "default",
  },
  argTypes: {
    icon: iconControl,
    gap: {
      control: "number",
    },
    variant: {
      control: "select",
      options: Object.values(AVATAR_VARIANT),
    },
    shape: {
      control: "select",
      options: Object.values(AVATAR_SHAPE),
    },
    size: {
      control: "select",
      options: Object.values(AVATAR_SIZE),
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Avatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};
