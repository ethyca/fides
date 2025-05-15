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

import { initialValues } from "../../../features/poc/constants";

const { Text, Title } = Typography;

export const FormikSpreadFieldPOC = () => (
  <Formik initialValues={{ ...initialValues }} onSubmit={console.log}>
    {({ values }) => (
      <Row>
        <Col span={12}>
          <Title level={2}>{`<Formik> + <Form> + {...field}`}</Title>
          <div className="mb-4">
            <Tag color="red">non functional</Tag>
            <Tag color="red">high effort</Tag>
          </div>
          <Form>
            <Flex vertical gap={16}>
              <div>
                <label htmlFor="input">Input</label>
                <div>
                  <Field name="input">
                    {({ field }: any) => (
                      <Input {...field} id="input" type="text" />
                    )}
                  </Field>
                </div>
              </div>
              <div>
                <Field name="radio">
                  {({ field }: any) => (
                    <Radio.Group {...field}>
                      <Radio value="1">Radio 1</Radio>
                      <Radio value="2">Radio 2</Radio>
                    </Radio.Group>
                  )}
                </Field>
              </div>
              <div>
                <Field name="checkbox">
                  {({ field }: any) => (
                    <Checkbox {...field} defaultChecked={values.checkbox}>
                      Checkbox
                    </Checkbox>
                  )}
                </Field>
                <Text type="warning">
                  Requires additional logic to handle default state
                </Text>
              </div>
              <div>
                <label htmlFor="switch">Switch</label>
                <div>
                  <Field name="switch">
                    {({ field }: any) => <Switch id="switch" {...field} />}
                  </Field>
                </div>
                <Text type="danger">
                  Ant Switch&apos;s onChange is too different from Formik,
                  requires to be fully controlled.
                </Text>
              </div>
              <div>
                <label htmlFor="select">Select</label>
                <div>
                  <Field name="select">
                    {({ field }: any) => (
                      <Select
                        allowClear
                        id="select"
                        className="w-full"
                        defaultValue={values.select}
                        status="error"
                        {...field}
                        options={[
                          { value: "1", label: "Option 1" },
                          { value: "2", label: "Option 2" },
                        ]}
                      />
                    )}
                  </Field>
                </div>
                <Text type="danger">
                  Ant Select&apos;s onChange is too different from Formik,
                  requires to be fully controlled.
                </Text>
              </div>
              <div>
                <label htmlFor="multiselect">Multiselect</label>
                <div>
                  <Field name="multiselect">
                    {({ field }: any) => (
                      <Select
                        mode="multiple"
                        allowClear
                        id="multiselect"
                        className="w-full"
                        defaultValue={values.multiselect}
                        status="error"
                        {...field}
                        options={[
                          { value: "1", label: "Option 1" },
                          { value: "2", label: "Option 2" },
                        ]}
                      />
                    )}
                  </Field>
                </div>
                <Text type="danger">
                  Ant Select&apos;s onChange is too different from Formik,
                  requires to be fully controlled.
                </Text>
              </div>
              <div>
                <label htmlFor="tags">Tags</label>
                <div>
                  <Field name="tags">
                    {({ field }: any) => (
                      <Select
                        mode="tags"
                        allowClear
                        id="tags"
                        className="w-full"
                        defaultValue={values.tags}
                        status="error"
                        {...field}
                        options={[
                          { value: "1", label: "Option 1" },
                          { value: "2", label: "Option 2" },
                        ]}
                      />
                    )}
                  </Field>
                </div>
                <Text type="danger">
                  Ant Select&apos;s onChange is too different from Formik,
                  requires to be fully controlled.
                </Text>
              </div>
              <div>
                <label htmlFor="date">Date</label>
                <div>
                  <Field name="date">
                    {({ field }: any) => (
                      <DatePicker id="date" status="error" {...field} />
                    )}
                  </Field>
                </div>
                <Text type="danger">
                  Ant DatePicker&apos;s onChange is different from Formik,
                  requires to be fully controlled.
                </Text>
              </div>
              <div>
                <label htmlFor="number">Number</label>
                <div>
                  <Field name="number">
                    {({ field }: any) => (
                      <InputNumber
                        id="number"
                        defaultValue={values.number}
                        status="error"
                        {...field}
                      />
                    )}
                  </Field>
                </div>
                <Text type="danger">
                  Ant InputNumber&apos;s onChange is different from Formik,
                  requires to be fully controlled.
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

export default FormikSpreadFieldPOC;
