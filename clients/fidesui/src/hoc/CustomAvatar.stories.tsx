import type { Meta, StoryObj } from "@storybook/react-vite";
import { Breakpoint } from "antd/lib";

import { Icons } from "../index";
import type { CustomAvatarProps } from "./CustomAvatar";
import { CustomAvatar } from "./CustomAvatar";

const AVATAR_SHAPE: Record<
  NonNullable<CustomAvatarProps["shape"]>,
  CustomAvatarProps["shape"]
> = {
  circle: "circle",
  square: "square",
};

const AVATAR_VARIANT: Record<
  NonNullable<CustomAvatarProps["variant"]>,
  CustomAvatarProps["variant"]
> = {
  outlined: "outlined",
  filled: "filled",
};

type AvatarSize = NonNullable<
  Exclude<
    CustomAvatarProps["size"],
    number | Partial<Record<Breakpoint, number>>
  >
>;

const AVATAR_SIZE: Record<AvatarSize, AvatarSize> = {
  default: "default",
  small: "small",
  large: "large",
};

const meta = {
  title: "Data Display/Avatar",
  component: CustomAvatar,
  args: {
    draggable: false,
    shape: "circle",
    size: "default",
  },
  argTypes: {
    icon: {
      control: "select",
      options: Object.keys(Icons),
      mapping: Object.fromEntries(
        Object.entries(Icons).map(([key, Component]) => {
          return [key, <Component key={key} />];
        }),
      ),
    },
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
} satisfies Meta<typeof CustomAvatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};
