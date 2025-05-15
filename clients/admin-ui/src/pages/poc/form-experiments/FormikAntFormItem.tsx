/* eslint-disable no-console */
/* eslint-disable jsx-a11y/label-has-associated-control */
import {
  AntCard as Card,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntDatePicker as DatePicker,
  AntFlex as Flex,
  AntForm,
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
import { Form, Formik } from "formik";

import { initialValues } from "../../../features/poc/constants";

const { Title } = Typography;

export const FormikAntFormItemPOC = () => (
  <Formik initialValues={{ ...initialValues }} onSubmit={console.log}>
    {({ values, setFieldValue }) => (
      <Row>
        <Col span={12}>
          <Title level={2}>{`<Formik> + Controlled + Ant's <Form.Item>`}</Title>
          <div className="mb-4">
            <Tag color="green">funcitonal</Tag>
            <Tag color="orange">mid effort</Tag>
          </div>
          <Form>
            <Flex vertical>
              <AntForm.Item label="Input" name="input" layout="vertical">
                <Input
                  onChange={(e) => setFieldValue("input", e.target.value)}
                  defaultValue={values.input}
                />
              </AntForm.Item>
              <Radio.Group
                name="radio" // for a11y keyboard control
                onChange={(e) => setFieldValue("radio", e.target.value)}
                defaultValue={values.radio}
              >
                <Radio value="1">Radio 1</Radio>
                <Radio value="2">Radio 2</Radio>
              </Radio.Group>
              <AntForm.Item name="checkbox">
                <Checkbox
                  onChange={(e) => setFieldValue("checkbox", e.target.checked)}
                  defaultChecked={values.checkbox}
                >
                  Checkbox
                </Checkbox>
              </AntForm.Item>
              <AntForm.Item label="Switch" name="switch" layout="vertical">
                <Switch
                  onChange={(value) => setFieldValue("switch", value)}
                  defaultChecked={values.switch}
                />
              </AntForm.Item>
              <AntForm.Item label="Select" name="select" layout="vertical">
                <Select
                  allowClear
                  className="w-full"
                  defaultValue={values.select}
                  onChange={(value) => setFieldValue("select", value)}
                  options={[
                    { value: "1", label: "Option 1" },
                    { value: "2", label: "Option 2" },
                  ]}
                />
              </AntForm.Item>
              <AntForm.Item
                label="Multiselect"
                name="multiselect"
                layout="vertical"
              >
                <Select
                  mode="multiple"
                  allowClear
                  className="w-full"
                  defaultValue={values.multiselect}
                  onChange={(value) => setFieldValue("multiselect", value)}
                  options={[
                    { value: "1", label: "Option 1" },
                    { value: "2", label: "Option 2" },
                  ]}
                />
              </AntForm.Item>
              <AntForm.Item label="Tags" name="tags" layout="vertical">
                <Select
                  mode="tags"
                  allowClear
                  className="w-full"
                  defaultValue={values.tags}
                  onChange={(value) => setFieldValue("tags", value)}
                  options={[
                    { value: "1", label: "Option 1" },
                    { value: "2", label: "Option 2" },
                  ]}
                />
              </AntForm.Item>
              <AntForm.Item label="Date" name="date" layout="vertical">
                <DatePicker
                  onChange={(date) => setFieldValue("date", date.toISOString())}
                />
              </AntForm.Item>
              <AntForm.Item label="Number" name="number" layout="vertical">
                <InputNumber
                  defaultValue={values.number}
                  onChange={(value) => setFieldValue("number", value)}
                />
              </AntForm.Item>
            </Flex>
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
                  return `  ${typedKey}: ${values[typedKey]}\n`;
                })}
                {"}"}
              </code>
            </pre>
          </Card>
        </Col>
      </Row>
    )}
  </Formik>
);

export default FormikAntFormItemPOC;
