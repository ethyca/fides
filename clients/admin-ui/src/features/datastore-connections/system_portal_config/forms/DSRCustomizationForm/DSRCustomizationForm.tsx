import { Button, Flex, Form, Icons, Input, Select, useMessage } from "fidesui";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy";
import { selectDataCategories } from "~/features/taxonomy/data-category.slice";

import { ButtonGroup as ManualButtonGroup } from "./ButtonGroup";
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
              <Flex gap={24} className="mb-1.5 font-semibold">
                <div className="w-[416px]">PII Field</div>
                <div className="w-[416px]">DSR Package Label</div>
                <div className="w-[416px]">Data Categories</div>
                <div className="invisible">
                  <Icons.TrashCan />
                </div>
              </Flex>
              <div>
                {formFields.map((formField, index) => (
                  <Flex
                    key={formField.key}
                    gap={24}
                    align="flex-start"
                    className={index > 0 ? "mt-3" : undefined}
                  >
                    <div className="min-h-[57px] w-[416px]">
                      <Form.Item
                        {...formField}
                        name={[formField.name, "pii_field"]}
                        rules={[
                          {
                            required: true,
                            message: "PII Field is required",
                          },
                          {
                            min: 1,
                            message:
                              "PII Field must have at least one character",
                          },
                          {
                            max: 200,
                            message:
                              "PII Field has a maximum of 200 characters",
                          },
                        ]}
                      >
                        <Input autoFocus={index === 0} />
                      </Form.Item>
                    </div>
                    <div className="min-h-[57px] w-[416px]">
                      <Form.Item
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
                    </div>
                    <div className="min-h-[57px] w-[416px]">
                      <Form.Item
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
                    </div>
                    <div
                      className="h-[57px]"
                      style={{
                        visibility: index > 0 ? "visible" : "hidden",
                      }}
                    >
                      <Icons.TrashCan
                        onClick={() => remove(formField.name)}
                        className="cursor-pointer"
                      />
                    </div>
                  </Flex>
                ))}
              </div>
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
              <ManualButtonGroup
                isSubmitting={isSubmitting}
                onCancelClick={onCancel}
              />
            </>
          )}
        </Form.List>
      </Flex>
    </Form>
  );
};
