import type { Meta, StoryObj } from "@storybook/react-vite";
import { iso31661 } from "iso-3166";
import { fn } from "storybook/test";

import { LocationSelect } from "./LocationSelect";

const meta = {
  title: "DataEntry/Select/LocationSelect",
  component: LocationSelect,
  parameters: {},
  tags: ["autodocs"],
  argTypes: {
    mode: { control: "select", options: ["tags", "multiple"] },
  },
  args: { onClick: fn() },
} satisfies Meta<typeof LocationSelect>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};

export const OnlyCountries: Story = {
  args: {
    options: {
      countries: iso31661,
      regions: [],
    },
  },
};

export const TagMode: Story = {
  args: {
    mode: "tags",
    styles: { root: { minWidth: "30rem" } },
  },
};
