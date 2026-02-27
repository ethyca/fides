import type { Meta, StoryObj } from "@storybook/react-vite";

import type { FormProps } from "../../index";
import { Button, Flex, Form, Input, Select } from "../../index";
import { LocationSelect } from "./LocationSelect";

const LayoutOptions: Array<FormProps["layout"]> = [
  "vertical",
  "inline",
  "horizontal",
];
const SizeOptions: Array<FormProps["size"]> = ["middle", "small", "large"];

const meta = {
  title: "Data Entry/Form",
  args: {
    style: { maxWidth: "50rem" },
  },
} satisfies Meta<typeof Form>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  argTypes: {
    layout: {
      control: "select",
      options: LayoutOptions,
    },
    size: {
      control: "select",
      options: SizeOptions,
    },
  },
  render: (args) => (
    <Form {...args}>
      <Form.Item label="Name" required>
        <Input placeholder="Name" />
      </Form.Item>
      <Form.Item label="Select">
        {/* eslint-disable-next-line jsx-a11y/control-has-associated-label */}
        <Select placeholder="Select Option" />
      </Form.Item>
      <Form.Item label="Location">
        <LocationSelect />
      </Form.Item>

      <Form.Item>
        <Flex justify="space-between" gap="middle">
          <Button type="default" variant="outlined" htmlType="reset" block>
            Reset
          </Button>
          <Button type="primary" htmlType="submit" block>
            Submit
          </Button>
        </Flex>
      </Form.Item>
    </Form>
  ),
};

export const Validation: Story = {
  render: (args) => (
    <Form {...args}>
      <Form.Item
        label="Name"
        validateStatus="error"
        help="Name is a required field"
        extra="Extra Text"
        required
      >
        <Input placeholder="Name" />
      </Form.Item>
      <Form.Item label="Select" validateStatus="success">
        {/* eslint-disable-next-line jsx-a11y/control-has-associated-label */}
        <Select placeholder="Select Option" />
      </Form.Item>
      <Form.Item label="Location" validateStatus="validating">
        <LocationSelect />
      </Form.Item>

      <Form.Item>
        <Flex justify="space-between" gap="middle">
          <Button type="default" variant="outlined" htmlType="reset" block>
            Reset
          </Button>
          <Button type="primary" htmlType="submit" block disabled>
            Submit
          </Button>
        </Flex>
      </Form.Item>
    </Form>
  ),
};
