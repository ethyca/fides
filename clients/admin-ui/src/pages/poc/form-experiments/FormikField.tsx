/* eslint-disable no-console */
/* eslint-disable jsx-a11y/label-has-associated-control */
import {
  AntCard as Card,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntDatePicker as DatePicker,
  AntFlex as Flex,
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
import { Field, Form, Formik } from "formik";

import { initialValues } from "../constants";

const { Text, Title } = Typography;

export const FormikFieldPOC = () => (
  <Formik initialValues={{ ...initialValues }} onSubmit={console.log}>
    {({ values }) => (
      <Row>
        <Col span={12}>
          <Title level={2}>{`<Formik> + <Field>`}</Title>
          <div className="mb-4">
            <Tag color="red">non functional</Tag>
            <Tag color="red">high effort</Tag>
          </div>
          <Form>
            <Flex vertical gap={16}>
              <div>
                <label htmlFor="input">Input</label>
                <div>
                  <Field as={Input} id="input" name="input" type="text" />
                </div>
              </div>
              <div>
                <Field as={Radio.Group} name="radio">
                  <Radio value="1">Radio 1</Radio>
                  <Radio value="2">Radio 2</Radio>
                </Field>
              </div>
              <div>
                <Field
                  as={Checkbox}
                  defaultChecked={values.checkbox}
                  name="checkbox"
                >
                  Checkbox
                </Field>
                <Text type="warning">
                  Requires additional logic to handle default state
                </Text>
              </div>
              <div>
                <label htmlFor="switch">Switch</label>
                <div>
                  <Field as={Switch} id="switch" name="switch" />
                </div>
                <Text type="danger">
                  Ant Switch&apos;s onChange is too different from Formik,
                  requires to be fully controlled. This will not work with{" "}
                  {`<Field>`} alone
                </Text>
              </div>
              <div>
                <label htmlFor="select">Select</label>
                <div>
                  <Field
                    as={Select}
                    allowClear
                    id="select"
                    name="select"
                    className="w-full"
                    status="error"
                    options={[
                      { value: "1", label: "Option 1" },
                      { value: "2", label: "Option 2" },
                    ]}
                  />
                </div>
                <Text type="danger">
                  Ant Select&apos;s onChange is too different from Formik,
                  requires to be fully controlled. This will not work with{" "}
                  {`<Field>`} alone
                </Text>
              </div>
              <div>
                <label htmlFor="multiselect">Multiselect</label>
                <div>
                  <Field
                    as={Select}
                    mode="multiple"
                    allowClear
                    id="multiselect"
                    name="multiselect"
                    className="w-full"
                    status="error"
                    options={[
                      { value: "1", label: "Option 1" },
                      { value: "2", label: "Option 2" },
                    ]}
                  />
                </div>
                <Text type="danger">
                  Ant Select&apos;s onChange is too different from Formik,
                  requires to be fully controlled. This will not work with{" "}
                  {`<Field>`} alone
                </Text>
              </div>
              <div>
                <label htmlFor="multiselect">Tags</label>
                <div>
                  <Field
                    as={Select}
                    mode="tags"
                    allowClear
                    id="tags"
                    name="tags"
                    className="w-full"
                    status="error"
                    options={[
                      { value: "1", label: "Option 1" },
                      { value: "2", label: "Option 2" },
                    ]}
                  />
                </div>
                <Text type="danger">
                  Ant Select&apos;s onChange is too different from Formik,
                  requires to be fully controlled. This will not work with{" "}
                  {`<Field>`} alone
                </Text>
              </div>
              <div>
                <label htmlFor="date">Date</label>
                <div>
                  <Field as={DatePicker} id="date" name="date" status="error" />
                </div>
                <Text type="danger">
                  Ant DatePicker&apos;s onChange is different from Formik,
                  requires to be fully controlled. This will not work with{" "}
                  {`<Field>`} alone
                </Text>
              </div>
              <div>
                <label htmlFor="number">Number</label>
                <div>
                  <Field
                    as={InputNumber}
                    id="number"
                    name="number"
                    status="error"
                  />
                </div>
                <Text type="danger">
                  Ant InputNumber&apos;s onChange is different from Formik,
                  requires to be fully controlled. This will not work with{" "}
                  {`<Field>`} alone
                </Text>
              </div>
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
