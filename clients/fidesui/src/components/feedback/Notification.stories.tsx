import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect } from "react";

import { useNotification } from "../../index";
import { SUBTITLE_LOREM, TITLE_LOREM } from "../../stories/utils/content";
import { iconControl } from "../../stories/utils/controls";

type NotificationAPI = ReturnType<typeof useNotification>;
type NotificationProps = Parameters<NotificationAPI["info"]>[0] & {
  type: Exclude<keyof NotificationAPI, "destroy">;
};

const Notification = ({ type, ...args }: NotificationProps) => {
  const notification = useNotification();
  useEffect(() => {
    notification[type](args);
  }, []);

  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <></>;
};

const meta = {
  title: "Feedback/Notification",
  component: Notification,
  args: {
    message: TITLE_LOREM,
    description: SUBTITLE_LOREM,
    key: "key",
    duration: null,
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Notification>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    type: "info",
  },
  argTypes: {
    closable: {
      control: "boolean",
    },
    icon: iconControl,
    closeIcon: iconControl,
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
