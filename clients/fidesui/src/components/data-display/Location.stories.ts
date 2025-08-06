import type { Meta, StoryObj } from "@storybook/react-vite";
import { iso31661, iso31662 } from "iso-3166";

import { getIsoEntry, LocationDisplay } from "./Location";

const meta = {
  title: "DataDisplay/Location",
  component: LocationDisplay,
  parameters: {},
  tags: ["autodocs"],
  args: { isoCode: getIsoEntry("US-NY") },
} satisfies Meta<typeof LocationDisplay>;

export default meta;
type Story = StoryObj<typeof meta>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: Story = {
  argTypes: {
    isoCode: {
      control: "select",
      options: [...iso31662, ...iso31661],
      mapping: [
        ...iso31662.map(({ code }) => code),
        ...iso31661.map(({ alpha2 }) => alpha2),
      ],
    },
    showFlag: {
      control: "boolean",
    },
  },
};

export const CountryDisplay: Story = {
  args: { isoCode: getIsoEntry("us") },
  argTypes: {
    isoCode: {
      control: false,
    },
    showFlag: {
      control: false,
    },
  },
};

export const TextOnly: Story = {
  args: { isoCode: getIsoEntry("us-ny"), showFlag: false },
  argTypes: {
    isoCode: {
      control: false,
    },
    showFlag: {
      control: false,
    },
  },
};
