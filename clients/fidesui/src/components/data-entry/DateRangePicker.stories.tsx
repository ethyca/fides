import type { Meta, StoryObj } from "@storybook/react-vite";

import { DateRangePicker } from "../../index";
import { DAYJS_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";

const meta = {
  title: "Data Entry/DateRangePicker",
  component: DateRangePicker,
  tags: ["autodocs"],
} satisfies Meta<typeof DateRangePicker>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  argTypes: {
    allowClear: {
      control: "boolean",
    },
    allowEmpty: {
      control: "boolean",
    },
    defaultOpen: {
      control: "boolean",
    },
    open: {
      control: "boolean",
    },
    separator: iconControl,
    showHour: {
      control: "boolean",
    },
    showMillisecond: {
      control: "boolean",
    },
    showMinute: {
      control: "boolean",
    },
    showNow: {
      control: "boolean",
    },
    showSecond: {
      control: "boolean",
    },
    showTime: {
      control: "boolean",
    },
    showWeek: {
      control: "boolean",
    },
    suffixIcon: iconControl,
    use12Hours: {
      control: "boolean",
    },
  },
};

export const Opened: Story = {
  args: {
    value: [DAYJS_LOREM, null],
    open: true,
  },
};
