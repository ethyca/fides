import type { Meta, StoryObj } from "@storybook/react-vite";

import { Icons } from "../index";
import type { CustomSelectProps } from "./CustomSelect";
import { CustomSelect } from "./CustomSelect";

const SELECT_VARIANT: Record<
  NonNullable<CustomSelectProps<unknown>["variant"]>,
  CustomSelectProps<unknown>["variant"]
> = {
  borderless: "borderless",
  filled: "filled",
  outlined: "outlined",
  underlined: "underlined",
};

type SelectSize = NonNullable<CustomSelectProps<unknown>["size"]>;

const SELECT_SIZE: Record<SelectSize, SelectSize> = {
  small: "small",
  middle: "middle",
  large: "large",
};

const SELECT_MODE: Record<
  NonNullable<CustomSelectProps<unknown>["mode"]>,
  CustomSelectProps<unknown>["mode"]
> = {
  multiple: "multiple",
  tags: "tags",
};

const meta = {
  title: "Data Entry/Select",
  component: CustomSelect,
  args: {
    size: "small",
    variant: "filled",
    options: [
      { key: 1, label: "Option 1" },
      { key: 2, label: "Option 2" },
    ],
    placeholder: "Select...",
  },
  argTypes: {
    variant: {
      control: "select",
      options: Object.values(SELECT_VARIANT),
    },
    size: {
      control: "select",
      options: Object.values(SELECT_SIZE),
    },
    mode: {
      control: "select",
      options: Object.values(SELECT_MODE),
    },
    allowClear: {
      control: "boolean",
    },
    autoFocus: {
      control: "boolean",
    },
    defaultOpen: {
      control: "boolean",
    },
    disabled: {
      control: "boolean",
    },
    open: {
      control: "boolean",
    },
    labelInValue: {
      control: "boolean",
    },
    loading: {
      control: "boolean",
    },
    suffixIcon: {
      control: "select",
      options: Object.keys(Icons),
      mapping: Object.fromEntries(
        Object.entries(Icons).map(([key, Component]) => {
          return [key, <Component key={key} />];
        }),
      ),
    },
    removeIcon: {
      control: "select",
      options: Object.keys(Icons),
      mapping: Object.fromEntries(
        Object.entries(Icons).map(([key, Component]) => {
          return [key, <Component key={key} />];
        }),
      ),
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof CustomSelect>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};
