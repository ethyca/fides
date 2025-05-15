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
import { Form, Formik } from "formik";

import { initialValues } from "../../../features/poc/constants";

const { Title } = Typography;

export const FormikControlledPOC = () => (
  <Formik initialValues={{ ...initialValues }} onSubmit={console.log}>
    {({ values, setFieldValue }) => (
      <Row>
        <Col span={12}>
          <Title level={2}>{`<Formik> + Controlled`}</Title>
          <div className="mb-4">
            <Tag color="green">funcitonal</Tag>
            <Tag color="red">high effort</Tag>
          </div>
          <Form>
            <Flex vertical gap={16}>
              <div>
                <label htmlFor="input">Input</label>
                <div>
                  <Input
                    id="input"
                    onChange={(e) => setFieldValue("input", e.target.value)}
                    defaultValue={values.input}
                  />
                </div>
              </div>
              <div>
                <Radio.Group
                  name="radio" // for a11y keyboard control
                  onChange={(e) => setFieldValue("radio", e.target.value)}
                  defaultValue={values.radio}
                >
                  <Radio value="1">Radio 1</Radio>
                  <Radio value="2">Radio 2</Radio>
                </Radio.Group>
              </div>
              <div>
                <Checkbox
                  onChange={(e) => setFieldValue("checkbox", e.target.checked)}
                  defaultChecked={values.checkbox}
                >
                  Checkbox
                </Checkbox>
              </div>
              <div>
                <label htmlFor="switch">Switch</label>
                <div>
                  <Switch
                    id="switch"
                    onChange={(value) => setFieldValue("switch", value)}
                    defaultChecked={values.switch}
                  />
                </div>
              </div>
              <div>
                <label htmlFor="select">Select</label>
                <div>
                  <Select
                    allowClear
                    id="select"
                    defaultValue={values.select}
                    onChange={(value) => setFieldValue("select", value)}
                    className="w-full"
                    options={[
                      { value: "1", label: "Option 1" },
                      { value: "2", label: "Option 2" },
                    ]}
                  />
                </div>
              </div>
              <div>
                <label htmlFor="multiselect">Multiselect</label>
                <div>
                  <Select
                    mode="multiple"
                    allowClear
                    id="multiselect"
                    defaultValue={values.multiselect}
                    onChange={(value) => setFieldValue("multiselect", value)}
                    className="w-full"
                    options={[
                      { value: "1", label: "Option 1" },
                      { value: "2", label: "Option 2" },
                    ]}
                  />
                </div>
              </div>
              <div>
                <label htmlFor="tags">Tags</label>
                <div>
                  <Select
                    mode="tags"
                    allowClear
                    id="tags"
                    defaultValue={values.tags}
                    onChange={(value) => setFieldValue("tags", value)}
                    className="w-full"
                    options={[
                      { value: "1", label: "Option 1" },
                      { value: "2", label: "Option 2" },
                    ]}
                  />
                </div>
              </div>
              <div>
                <label htmlFor="date">Date</label>
                <div>
                  <DatePicker
                    id="date"
                    onChange={(date) =>
                      setFieldValue("date", date.toISOString())
                    }
                  />
                </div>
              </div>
              <div>
                <label htmlFor="number">Number</label>
                <div>
                  <InputNumber
                    id="number"
                    defaultValue={values.number}
                    onChange={(value) => setFieldValue("number", value)}
                  />
                </div>
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

export default FormikControlledPOC;
