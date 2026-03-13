import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect } from "react";

import { useMessage } from "../../index";
import { TITLE_LOREM } from "../../stories/utils/content";

type MessageAPI = ReturnType<typeof useMessage>;
type MessageProps = {
  content: Parameters<MessageAPI["info"]>[0];
  type: Exclude<keyof MessageAPI, "destroy" | "open">;
};

const Message = ({ type, content }: MessageProps) => {
  const notification = useMessage();
  useEffect(() => {
    notification[type](content);
  }, []);

  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <></>;
};

const meta = {
  title: "Feedback/Message",
  component: Message,
  args: {
    content: TITLE_LOREM,
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Message>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    type: "info",
  },
};

export const Success: Story = {
  args: {
    type: "success",
  },
};

export const Warning: Story = {
  args: {
    type: "warning",
  },
};

export const Error: Story = {
  args: {
    type: "error",
  },
};
