/* eslint-disable no-console */
/* eslint-disable jsx-a11y/label-has-associated-control */
import {
  AntCard as Card,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntDatePicker as DatePicker,
  AntDivider as Divider,
  AntFlex as Flex,
  AntInput as Input,
  AntInputNumber as InputNumber,
  AntLayout as Layout,
  AntRadio as Radio,
  AntRow as Row,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Field, Form, Formik } from "formik";

const { Content } = Layout;
const { Title } = Typography;

const initialValues = {
  input: "default text",
  radio: "2",
  checkbox1: true,
  checkbox2: false,
  select: "2",
  multiselect: ["2"],
  tags: ["1"],
  date: "",
  number: 12,
};

export const FormsPOC = () => {
  return (
    <Content className="overflow-auto px-10 py-6">
      <Row>
        <Title>Forms POC</Title>
      </Row>
      <Divider />
      <Formik initialValues={{ ...initialValues }} onSubmit={console.log}>
        {({ values, setFieldValue }) => (
          <Row>
            <Col span={12}>
              <Title level={2}>{`<Formik> + <Field>`}</Title>
              <Form>
                <Flex vertical gap={16}>
                  <div>
                    <label htmlFor="input">Input</label>
                    <div>
                      {/* I wasn't able to get any other field type to work with <Field> as nicely as <Input> does. They all require custom controller value/onChange */}
                      <Field as={Input} id="input" name="input" type="text" />
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
                      onChange={(e) =>
                        setFieldValue("checkbox1", e.target.checked)
                      }
                      defaultChecked={values.checkbox1}
                    >
                      Checkbox 1
                    </Checkbox>
                    <Checkbox
                      onChange={(e) =>
                        setFieldValue("checkbox2", e.target.checked)
                      }
                      defaultChecked={values.checkbox2}
                    >
                      Checkbox 2
                    </Checkbox>
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
                      >
                        <option value="1">Option 1</option>
                        <option value="2">Option 2</option>
                      </Select>
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
                        onChange={(value) =>
                          setFieldValue("multiselect", value)
                        }
                        className="w-full"
                      >
                        <option value="1">Option 1</option>
                        <option value="2">Option 2</option>
                      </Select>
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
                      >
                        <option value="1">Option 1</option>
                        <option value="2">Option 2</option>
                      </Select>
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
      <Divider />
    </Content>
  );
};

export default FormsPOC;
