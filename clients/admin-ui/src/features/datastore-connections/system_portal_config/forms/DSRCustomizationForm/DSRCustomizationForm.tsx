import {
  Button,
  Col,
  Flex,
  Form,
  Icons,
  Input,
  Row,
  Select,
  useMessage,
} from "fidesui";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy";
import { selectDataCategories } from "~/features/taxonomy/data-category.slice";

import { Field } from "./types";

type DSRCustomizationFormProps = {
  data: Field[];
  isSubmitting: boolean;
  onSaveClick: (values: any, actions: any) => void;
  onCancel: () => void;
};

export const DSRCustomizationForm = ({
  data = [],
  isSubmitting = false,
  onSaveClick,
  onCancel,
}: DSRCustomizationFormProps) => {
  const { isLoading: isLoadingDataCategories } = useGetAllDataCategoriesQuery();
  const allDataCategories = useAppSelector(selectDataCategories);

  const message = useMessage();
  const [form] = Form.useForm();

  const handleFinish = (values: { fields: Field[] }) => {
    const uniqueValues = new Set(values.fields.map((f: Field) => f.pii_field));
    if (uniqueValues.size < values.fields.length) {
      message.error("PII Field must be unique");
      return;
    }
    onSaveClick(values, { setSubmitting: () => {} });
  };

  if (isLoadingDataCategories) {
    return null;
  }

  const initialValues = {
    fields:
      data.length > 0
        ? data
        : ([
            {
              pii_field: "",
              dsr_package_label: "",
              data_categories: [],
            },
          ] as Field[]),
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={handleFinish}
      key={JSON.stringify(data)}
      style={{ marginTop: 0 }}
      validateTrigger={[]}
    >
      <Flex vertical>
        <Form.List name="fields">
          {(formFields, { add, remove }) => (
            <>
              {/* Column headers */}
              <Row gutter={16} className="mb-1.5 font-semibold">
                <Col span={8}>PII Field</Col>
                <Col span={8}>DSR Package Label</Col>
                <Col span={7}>Data Categories</Col>
                <Col span={1} className="invisible">
                  <Icons.TrashCan />
                </Col>
              </Row>
              {formFields.map((formField, index) => (
                <Row
                  key={formField.key}
                  gutter={16}
                  className={index > 0 ? "mt-3" : undefined}
                >
                  <Col span={8}>
                    <Form.Item
                      className="!m-0"
                      {...formField}
                      name={[formField.name, "pii_field"]}
                      rules={[
                        {
                          required: true,
                          message: "PII Field is required",
                        },
                        {
                          min: 1,
                          message: "PII Field must have at least one character",
                        },
                        {
                          max: 200,
                          message: "PII Field has a maximum of 200 characters",
                        },
                      ]}
                    >
                      <Input autoFocus={index === 0} />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item
                      className="!m-0"
                      {...formField}
                      name={[formField.name, "dsr_package_label"]}
                      rules={[
                        {
                          required: true,
                          message: "DSR Package Label is required",
                        },
                        {
                          min: 1,
                          message:
                            "DSR Package Label must have at least one character",
                        },
                        {
                          max: 200,
                          message:
                            "DSR Package Label has a maximum of 200 characters",
                        },
                      ]}
                    >
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={7}>
                    <Form.Item
                      className="!m-0"
                      {...formField}
                      name={[formField.name, "data_categories"]}
                    >
                      <Select
                        aria-label="Data Categories"
                        mode="multiple"
                        options={allDataCategories.map((data_category) => ({
                          value: data_category.fides_key,
                          label: data_category.fides_key,
                        }))}
                      />
                    </Form.Item>
                  </Col>
                  <Col
                    span={1}
                    style={{
                      visibility: index > 0 ? "visible" : "hidden",
                    }}
                  >
                    <Icons.TrashCan
                      onClick={() => remove(formField.name)}
                      className="cursor-pointer"
                    />
                  </Col>
                </Row>
              ))}
              <Button
                className="my-6"
                onClick={() => {
                  add({
                    pii_field: "",
                    dsr_package_label: "",
                    data_categories: [],
                  });
                }}
              >
                Add new PII field
              </Button>
              <Flex gap="small" justify="end">
                <Button onClick={onCancel}>Cancel</Button>
                <Button
                  type="primary"
                  disabled={isSubmitting}
                  loading={isSubmitting}
                  htmlType="submit"
                >
                  Save
                </Button>
              </Flex>
            </>
          )}
        </Form.List>
      </Flex>
    </Form>
  );
};
