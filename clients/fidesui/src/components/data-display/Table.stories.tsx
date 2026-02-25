import type { Meta, StoryObj } from "@storybook/react-vite";

import { Table, TableProps } from "../../index";

const meta = {
  title: "Data Display/Table",
  component: Table,
  tags: ["autodocs"],
} satisfies Meta<typeof Table>;

export default meta;
type Story = StoryObj<typeof meta>;

const TABLE_SIZE: Record<
  NonNullable<TableProps["size"]>,
  TableProps["size"]
> = {
  large: "large",
  middle: "middle",
  small: "small",
};

export const Primary: Story = {
  args: {
    dataSource: [
      {
        name: "Bob",
        email: "bob@ethyca.com",
        username: "EthycaBob",
        age: 21,
      },
    ],
    columns: [
      {
        dataIndex: "name",
        title: "Name",
      },
      {
        dataIndex: "email",
        title: "Email",
      },
      {
        dataIndex: "username",
        title: "Username",
      },
      {
        dataIndex: "age",
        title: "Age",
      },
    ],
  },
  argTypes: {
    size: {
      control: "select",
      options: Object.values(TABLE_SIZE),
    },
    bordered: {
      control: "boolean",
    },
  },
};

export const Empty: Story = {
  args: {
    dataSource: [],
    columns: [
      {
        dataIndex: "name",
        title: "Name",
      },
      {
        dataIndex: "email",
        title: "Email",
      },
      {
        dataIndex: "",
        title: "Username",
      },
      {
        dataIndex: "age",
        title: "Age",
      },
    ],
  },
};
