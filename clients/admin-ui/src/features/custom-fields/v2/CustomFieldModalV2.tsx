import {
  AntForm as Form,
  AntInput as Input,
  AntModal as Modal,
  AntModalProps as ModalProps,
  AntSelect as Select,
  AntButton as Button,
  AntFlex as Flex,
  Icons,
  AntMessage as message,
} from "fidesui";

import {
  FIELD_TYPE_OPTIONS_NEW,
  RESOURCE_TYPE_OPTIONS,
  FieldTypes,
} from "~/features/common/custom-fields/constants";
import {
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
} from "~/types/api";
import useCreateOrUpdateCustomField from "~/features/custom-fields/v2/useCreateOrUpdateCustomField";
import { useGetAllowListQuery } from "~/features/plus/plus.slice";
import { getCustomFieldType } from "~/features/custom-fields/constants";
import { useEffect } from "react";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";

interface CustomFieldModalV2Props extends ModalProps {
  initialField?: CustomFieldDefinitionWithId;
  onClose?: () => void;
}

export interface CustomFieldsFormValues
  extends Omit<CustomFieldDefinition, "field_type"> {
  options?: string[];
  field_type: FieldTypes;
}

const CustomFieldModalV2 = ({
  initialField,
  onClose,
  ...props
}: CustomFieldModalV2Props) => {
  const [form] = Form.useForm<CustomFieldsFormValues>();

  const [messageApi, messageContext] = message.useMessage();

  const handleCancel = () => {
    if (onClose) {
      onClose();
    }
    form.resetFields();
  };

  const { createOrUpdate, isLoading } = useCreateOrUpdateCustomField();

  const onSubmit = async (values: CustomFieldsFormValues) => {
    const result = await createOrUpdate(values, initialField, allowList);
    if (!result) {
      return;
    }
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(
        `Custom field ${initialField ? "updated" : "created"} successfully`,
      );
    }
    handleCancel();
  };

  const { data: allowList, error } = useGetAllowListQuery(
    initialField?.allow_list_id as string,
    {
      skip: !initialField?.allow_list_id,
    },
  );
  // handle errors for this

  const parseFieldToFormValues = (
    field: CustomFieldDefinition | undefined,
  ): CustomFieldsFormValues | undefined => {
    if (!field) {
      return undefined;
    }
    return {
      ...field,
      field_type: getCustomFieldType(field),
      options: allowList?.allowed_values ?? [],
    };
  };

  const initialValues = parseFieldToFormValues(initialField);

  // TODO: this is still busted
  // needed to prevent showing stale initial values in the form when the passed in field changes
  useEffect(() => {
    form.setFieldsValue(initialValues || {});
  }, [initialValues]);
  return (
    <Modal
      {...props}
      title={initialField ? `Edit ${initialField.name}` : "Add custom field"}
      onCancel={handleCancel}
      onOk={() => onSubmit(form.getFieldsValue())}
      confirmLoading={isLoading}
    >
      {messageContext}
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues || {}}
        validateTrigger={["onBlur", "onChange"]}
      >
        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: "Please enter a name" }]}
        >
          <Input />
        </Form.Item>

        <Form.Item label="Description" name="description">
          <Input.TextArea rows={2} />
        </Form.Item>

        <Form.Item
          label="Location"
          name="resource_type"
          rules={[{ required: true, message: "Please select a resource type" }]}
        >
          <Select
            options={RESOURCE_TYPE_OPTIONS}
            getPopupContainer={(trigger) =>
              trigger.parentElement || document.body
            }
          />
        </Form.Item>

        <Form.Item
          label="Field Type"
          name="field_type"
          rules={[{ required: true, message: "Please select a field type" }]}
        >
          <Select
            options={FIELD_TYPE_OPTIONS_NEW}
            getPopupContainer={(trigger) =>
              trigger.parentElement || document.body
            }
          />
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) =>
            prevValues.field_type !== currentValues.field_type
          }
        >
          {({ getFieldValue }) => {
            const fieldType = getFieldValue("field_type");
            const isSelectType =
              fieldType === FieldTypes.SINGLE_SELECT ||
              fieldType === FieldTypes.MULTIPLE_SELECT;

            return (
              isSelectType && (
                <>
                  <Form.List name="options">
                    {(fields, { add, remove }) => (
                      <>
                        {fields.map((field, index) => (
                          <Form.Item
                            required={false}
                            key={field.key}
                            label={index === 0 ? "Options" : ""}
                          >
                            <Flex gap="middle">
                              <Form.Item
                                {...field}
                                validateTrigger={["onChange", "onBlur"]}
                                rules={[
                                  {
                                    required: true,
                                    whitespace: true,
                                    message: "Options cannot be empty",
                                  },
                                  ({ getFieldValue }) => ({
                                    validator(_, value) {
                                      const duplicateCount = getFieldValue(
                                        "options",
                                      ).filter(
                                        (opt: string) => opt === value,
                                      ).length;
                                      if (duplicateCount > 1) {
                                        return Promise.reject(
                                          new Error(
                                            "Option values must be unique",
                                          ),
                                        );
                                      }
                                      return Promise.resolve();
                                    },
                                  }),
                                ]}
                                noStyle
                              >
                                <Input placeholder="Enter option value" />
                              </Form.Item>
                              {fields.length > 1 && (
                                <Button
                                  icon={<Icons.TrashCan />}
                                  onClick={() => remove(field.name)}
                                  aria-label="Remove option"
                                />
                              )}
                            </Flex>
                          </Form.Item>
                        ))}
                        <Form.Item>
                          <Button
                            type="dashed"
                            onClick={() => add()}
                            icon={<Icons.Add />}
                          >
                            Add option
                          </Button>
                        </Form.Item>
                      </>
                    )}
                  </Form.List>
                </>
              )
            );
          }}
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CustomFieldModalV2;
