// import type { CustomDateRangePickerProps } from "../../hoc";
import type { Meta, StoryObj } from "@storybook/react-vite";

import { CustomDateRangePicker } from "../../hoc";

const meta = {
  title: "Data Entry/DateRangePicker",
  component: CustomDateRangePicker,
  args: {},
  argTypes: {},
  tags: ["autodocs"],
} satisfies Meta<typeof CustomDateRangePicker>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};
