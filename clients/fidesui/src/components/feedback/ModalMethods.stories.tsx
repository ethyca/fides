import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect } from "react";

import { useModal } from "../../index";
import { PARAGRAPH_LOREM, TITLE_LOREM } from "../../stories/utils/content";

type ModalAPI = ReturnType<typeof useModal>;
type ModalMethodProps = {
  title: string;
  content: string;
  type: Extract<
    keyof ModalAPI,
    "info" | "success" | "warning" | "error" | "confirm"
  >;
  hideIcon?: boolean;
};

const ModalMethod = ({ type, title, content, hideIcon }: ModalMethodProps) => {
  const modalApi = useModal();
  useEffect(() => {
    const ref = modalApi[type]({
      title,
      content,
      ...(hideIcon ? { icon: null } : {}),
    });
    return () => ref?.destroy?.();
  }, [modalApi, type, title, content, hideIcon]);

  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <></>;
};

const meta = {
  title: "Feedback/Modal/Methods",
  component: ModalMethod,
  args: {
    title: TITLE_LOREM,
    content: PARAGRAPH_LOREM,
    hideIcon: false,
  },
  tags: ["autodocs"],
} satisfies Meta<typeof ModalMethod>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Info: Story = {
  args: {
    type: "info",
  },
  argTypes: {
    type: { control: false },
  },
};

export const Success: Story = {
  args: {
    type: "success",
  },
  argTypes: {
    type: { control: false },
  },
};

export const Warning: Story = {
  args: {
    type: "warning",
  },
  argTypes: {
    type: { control: false },
  },
};

export const Error: Story = {
  args: {
    type: "error",
  },
  argTypes: {
    type: { control: false },
  },
};

export const Confirm: Story = {
  args: {
    type: "confirm",
  },
  argTypes: {
    type: { control: false },
  },
};
