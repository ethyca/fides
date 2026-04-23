import type { Meta, StoryObj } from "@storybook/react-vite";

import { Tag } from "../../index";
import { OPTION_NAMES } from "../../stories/utils/content";
import { SelectInline } from "./SelectInline";

const meta = {
  title: "Data Entry/SelectInline",
  component: SelectInline,
  args: {},
  argTypes: {},
  tags: ["autodocs"],
} satisfies Meta<typeof SelectInline>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {},
};

export const Selected: Story = {
  args: {
    options: OPTION_NAMES.map((value) => ({ label: value, value })),
    value: OPTION_NAMES,
  },
  parameters: { controls: { includes: [] } },
};

export const CustomTags: Story = {
  args: {
    options: OPTION_NAMES.map((value) => ({ label: value, value })),
    value: OPTION_NAMES,
    mode: "tags",
    tagRender: (props) => <Tag closable>{props.value}</Tag>,
  },
  parameters: { controls: { includes: [] } },
};
