import type { Meta, StoryObj } from "@storybook/react-vite";
import { Breakpoint } from "antd/lib";

import type { AvatarProps } from "../index";
import { Avatar, Icons } from "../index";
import palette from "../palette/palette.module.scss";
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

const AVATAR_FIT: Record<
  NonNullable<AvatarProps["imageFit"]>,
  AvatarProps["imageFit"]
> = {
  contain: "contain",
  cover: "cover",
};

const meta = {
  title: "Data Display/Avatar",
  component: Avatar,
  tags: ["autodocs"],
} satisfies Meta<typeof Avatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: { icon: <Icons.User color={palette.FIDESUI_MINOS} /> },
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
    imageFit: {
      control: "select",
      options: Object.values(AVATAR_FIT),
    },
  },
};

export const Square: Story = {
  args: {
    icon: <Icons.User color={palette.FIDESUI_MINOS} />,
    shape: "square",
  },
  parameters: { controls: { include: [] } },
};

export const Outlined: Story = {
  args: {
    icon: <Icons.User color={palette.FIDESUI_MINOS} />,
    variant: "outlined",
  },
  parameters: { controls: { include: [] } },
};

export const ContainedImage: Story = {
  args: {
    src: <img src="/context.png" alt="alt" />,
    imageFit: "contain",
  },
  parameters: { controls: { include: [] } },
};

export const CoveredImage: Story = {
  args: {
    src: <img src="/context.png" alt="alt" />,
    imageFit: "cover",
  },
  parameters: { controls: { include: [] } },
};
