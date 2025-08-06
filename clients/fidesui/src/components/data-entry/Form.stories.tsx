import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button, Flex, Form, Input } from "antd";
import FormItem from "antd/es/form/FormItem";

import { CustomSelect } from "../../hoc";
import { LocationSelect } from "../select/LocationSelect";

const meta = {
  title: "DataEntry/Form",
  args: {
    layout: "vertical",
    size: "middle",
    style: { maxWidth: "50rem" },
  },
  argTypes: {},
} satisfies Meta<typeof Form>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  render: (args) => (
    <Form {...args}>
      <Form.Item label="Name" required>
        <Input placeholder="Name" />
      </Form.Item>
      <Form.Item label="Select">
        <CustomSelect placeholder="Select Option" style={{ width: "100%" }} />
      </Form.Item>
      <Form.Item label="Location">
        <LocationSelect style={{ width: "100%" }} />
      </Form.Item>

      <FormItem>
        <Flex justify="space-between" gap="middle">
          <Button type="default" variant="outlined" htmlType="reset" block>
            Reset
          </Button>
          <Button type="primary" htmlType="submit" block>
            Submit
          </Button>
        </Flex>
      </FormItem>
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
        required
      >
        <Input placeholder="Name" />
      </Form.Item>
      <Form.Item label="Select" validateStatus="success">
        <CustomSelect placeholder="Select Option" />
      </Form.Item>
      <Form.Item label="Location" validateStatus="validating">
        <LocationSelect />
      </Form.Item>

      <FormItem>
        <Flex justify="space-between" gap="middle">
          <Button type="default" variant="outlined" htmlType="reset" block>
            Reset
          </Button>
          <Button type="primary" htmlType="submit" block disabled>
            Submit
          </Button>
        </Flex>
      </FormItem>
    </Form>
  ),
};
