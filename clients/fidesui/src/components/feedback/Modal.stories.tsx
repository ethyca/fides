import type { Meta, StoryObj } from "@storybook/react-vite";

import { Modal } from "../../index";
import { PARAGRAPH_LOREM, TITLE_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";

const meta = {
  title: "Feedback/Modal",
  component: Modal,
  tags: ["autodocs"],
} satisfies Meta<typeof Modal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    open: true,
    title: TITLE_LOREM,
    children: PARAGRAPH_LOREM,
  },
  argTypes: {
    centered: {
      control: "boolean",
    },
    closable: {
      control: "boolean",
    },
    cancelText: {
      control: "text",
    },
    closeIcon: iconControl,
    okText: {
      control: "text",
    },
    mask: {
      control: "boolean",
    },
    loading: {
      control: "boolean",
    },
  },
};
