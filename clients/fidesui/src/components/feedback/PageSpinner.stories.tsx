import type { Meta, StoryObj } from "@storybook/react-vite";

import { GetProps } from "../../index";
import { PageSpinner } from "./PageSpinner";

type PageSpinnerProps = GetProps<typeof PageSpinner>;

type PageSpinnerSize = NonNullable<PageSpinnerProps["size"]>;

const PAGE_SPINNER_SIZE_OPTIONS: Record<PageSpinnerSize, PageSpinnerSize> = {
  default: "default",
  small: "small",
  large: "large",
};

const meta = {
  title: "Feedback/PageSpinner",
  component: PageSpinner,
  argTypes: {
    size: {
      control: "select",
      options: Object.values(PAGE_SPINNER_SIZE_OPTIONS),
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof PageSpinner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};
