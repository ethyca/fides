/* eslint-disable no-console */
/* eslint-disable jsx-a11y/label-has-associated-control */
import {
  AntCard as Card,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntDatePicker as DatePicker,
  AntForm as Form,
  AntInput as Input,
  AntInputNumber as InputNumber,
  AntRadio as Radio,
  AntRow as Row,
  AntSelect as Select,
  AntSwitch as Switch,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useState } from "react";

import { initialValues } from "../../../features/poc/constants";

const { Title } = Typography;

export const AntFormPOC = () => {
  const [form] = Form.useForm();
  const [values, setValues] = useState(initialValues);

  return (
    <Row>
      <Col span={12}>
        <Title level={2}>Pure Ant</Title>
        <div className="mb-4">
          <Tag color="green">funcitonal</Tag>
          <Tag color="green">low effort</Tag>
        </div>
        <Form
          initialValues={{ ...initialValues }}
          form={form}
          layout="vertical"
          onValuesChange={(c, a) => {
            setValues(a);
          }}
        >
          <Form.Item label="Input" name="input">
            <Input />
          </Form.Item>
          <Form.Item name="radio">
            <Radio.Group
              name="radio" // for a11y keyboard control
            >
              <Radio value="1">Radio 1</Radio>
              <Radio value="2">Radio 2</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item name="checkbox" valuePropName="checked">
            <Checkbox>Checkbox</Checkbox>
          </Form.Item>
          <Form.Item label="Switch" name="switch" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item label="Select" name="select">
            <Select
              allowClear
              className="w-full"
              options={[
                { value: "1", label: "Option 1" },
                { value: "2", label: "Option 2" },
              ]}
            />
          </Form.Item>
          <Form.Item label="Multiselect" name="multiselect">
            <Select
              mode="multiple"
              allowClear
              className="w-full"
              options={[
                { value: "1", label: "Option 1" },
                { value: "2", label: "Option 2" },
              ]}
            />
          </Form.Item>
          <Form.Item label="Tags" name="tags">
            <Select
              mode="tags"
              allowClear
              className="w-full"
              options={[
                { value: "1", label: "Option 1" },
                { value: "2", label: "Option 2" },
              ]}
            />
          </Form.Item>
          <Form.Item label="Date" name="date">
            <DatePicker />
          </Form.Item>
          <Form.Item label="Number" name="number">
            <InputNumber />
          </Form.Item>
        </Form>
      </Col>
      <Col span={8} offset={4}>
        <Title level={4}>Controlled Values</Title>
        <Card
          style={{
            backgroundColor: palette.FIDESUI_MINOS,
            color: palette.FIDESUI_CORINTH,
          }}
        >
          <pre>
            <code>
              {"{\n"}
              {Object.keys(values).map((key) => {
                const typedKey = key as keyof typeof values;
                return `  ${typedKey.toString()}: ${values[typedKey]}\n`;
              })}
              {"}"}
            </code>
          </pre>
        </Card>
      </Col>
    </Row>
  );
};

export default AntFormPOC;
