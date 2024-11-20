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
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Field, Form, Formik } from "formik";

const { Content } = Layout;
const { Text, Title, Paragraph } = Typography;

const initialValues = {
  input: "default text",
  radio: "2",
  checkbox: true,
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
              <Title level={2}>{`<Formik> + Controlled`}</Title>
              <Tag color="green">funcitonal</Tag>
              <Tag color="red">high effort</Tag>
              <Paragraph>
                This is the most controlled way to handle forms with Formik.
                This is the most flexible way to handle forms, but also requires
                the most effort. Labels and errors are manually handled.
              </Paragraph>
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
                      onChange={(e) =>
                        setFieldValue("checkbox", e.target.checked)
                      }
                      defaultChecked={values.checkbox}
                    >
                      Checkbox
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
      <Formik initialValues={{ ...initialValues }} onSubmit={console.log}>
        {({ values }) => (
          <Row>
            <Col span={12}>
              <Title level={2}>{`<Formik> + <Field>`}</Title>
              <Tag color="red">non functional</Tag>
              <Tag color="red">high effort</Tag>
              <Paragraph>
                This is slightly more convenient than the fully controlled way,
                but still requires a lot of manual handling. Labels and errors
                are manually handled. Several components simply aren&apos;t
                compatible with Field out of the box.
              </Paragraph>
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
                    <label htmlFor="select">Select</label>
                    <div>
                      <Field
                        as={Select}
                        allowClear
                        id="select"
                        name="select"
                        className="w-full"
                        status="error"
                      >
                        <option value="1">Option 1</option>
                        <option value="2">Option 2</option>
                      </Field>
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
                      >
                        <option value="1">Option 1</option>
                        <option value="2">Option 2</option>
                      </Field>
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
                      >
                        <option value="1">Option 1</option>
                        <option value="2">Option 2</option>
                      </Field>
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
                      <Field
                        as={DatePicker}
                        id="date"
                        name="date"
                        status="error"
                      />
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
      <Divider />
      <Formik initialValues={{ ...initialValues }} onSubmit={console.log}>
        {({ values }) => (
          <Row>
            <Col span={12}>
              <Title level={2}>{`<Formik> + <Form> + {...field}`}</Title>
              <Tag color="red">non functional</Tag>
              <Tag color="red">high effort</Tag>
              <Paragraph>
                This doesn&apos;t offer much more than the previous example.
                Causes Typescript headaches that will need to be dealt with.
                Labels and errors are manually handled.
              </Paragraph>
              <Form>
                <Flex vertical gap={16}>
                  <div>
                    <label htmlFor="input">Input</label>
                    <div>
                      <Field name="input">
                        {({ field }) => (
                          <Input {...field} id="input" type="text" />
                        )}
                      </Field>
                    </div>
                  </div>
                  <div>
                    <Field name="radio">
                      {({ field }) => (
                        <Radio.Group {...field}>
                          <Radio value="1">Radio 1</Radio>
                          <Radio value="2">Radio 2</Radio>
                        </Radio.Group>
                      )}
                    </Field>
                  </div>
                  <div>
                    <Field name="checkbox">
                      {({ field }) => (
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
                    <label htmlFor="select">Select</label>
                    <div>
                      <Field name="select">
                        {({ field }) => (
                          <Select
                            allowClear
                            id="select"
                            className="w-full"
                            defaultValue={values.select}
                            status="error"
                            {...field}
                          >
                            <option value="1">Option 1</option>
                            <option value="2">Option 2</option>
                          </Select>
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
                        {({ field }) => (
                          <Select
                            mode="multiple"
                            allowClear
                            id="multiselect"
                            className="w-full"
                            defaultValue={values.multiselect}
                            status="error"
                            {...field}
                          >
                            <option value="1">Option 1</option>
                            <option value="2">Option 2</option>
                          </Select>
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
                        {({ field }) => (
                          <Select
                            mode="tags"
                            allowClear
                            id="tags"
                            className="w-full"
                            defaultValue={values.tags}
                            status="error"
                            {...field}
                          >
                            <option value="1">Option 1</option>
                            <option value="2">Option 2</option>
                          </Select>
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
                        {({ field }) => (
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
                        {({ field }) => (
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
      <Divider />
    </Content>
  );
};

export default FormsPOC;
