import type { Meta, StoryObj } from "@storybook/react-vite";

import { GetProps } from "../../index";
import { CenteredSpinner } from "./CenteredSpinner";

type CenteredSpinnerProps = GetProps<typeof CenteredSpinner>;

type CenteredSpinnerSize = NonNullable<CenteredSpinnerProps["size"]>;

const CENTERED_SPINNER_SIZE_OPTIONS: CenteredSpinnerSize[] = [
  "small",
  "default",
  "large",
];

const meta = {
  title: "Feedback/CenteredSpinner",
  component: CenteredSpinner,
  argTypes: {
    size: {
      control: "select",
      options: Object.values(CENTERED_SPINNER_SIZE_OPTIONS),
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof CenteredSpinner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};
