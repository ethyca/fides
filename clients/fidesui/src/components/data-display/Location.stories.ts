import type { Meta, StoryObj } from "@storybook/react-vite";
import { iso31661, ISO31661Entry, iso31662, ISO31662Entry } from "iso-3166";

import { LocationDisplay } from "./Location";
import { isoStringToEntry } from "./location.utils";

const meta = {
  title: "DataDisplay/Location",
  component: LocationDisplay,
  parameters: {},
  tags: ["autodocs"],
  args: { isoEntry: isoStringToEntry("US-NY") },
} satisfies Meta<typeof LocationDisplay>;

export default meta;
type Story = StoryObj<typeof meta>;

const codeValues = [...iso31662, ...iso31661].reduce(
  (agg, current) => {
    return "code" in current
      ? {
          ...agg,
          [current.code]: current,
        }
      : {
          ...agg,
          [current.alpha2]: current,
        };
  },
  {} as { [key: string]: ISO31661Entry | ISO31662Entry },
);

export const Primary: Story = {
  argTypes: {
    isoEntry: {
      control: "select",
      options: Object.keys(codeValues),
      mapping: codeValues,
    },
    showFlag: {
      control: "boolean",
    },
  },
};

export const CountryDisplay: Story = {
  args: { isoEntry: isoStringToEntry("us") },
  argTypes: {
    isoEntry: {
      control: false,
    },
    showFlag: {
      control: false,
    },
  },
};

export const TextOnly: Story = {
  args: { isoEntry: isoStringToEntry("us-ny"), showFlag: false },
  argTypes: {
    isoEntry: {
      control: false,
    },
    showFlag: {
      control: false,
    },
  },
};
