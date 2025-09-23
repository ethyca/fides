import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  AntSelect as Select,
  AntTypography as Typography,
  ConfirmationModal,
  Icons,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import {
  FIELD_TYPE_OPTIONS,
  FieldTypes,
  RESOURCE_TYPE_OPTIONS,
} from "~/features/custom-fields/constants";
import { CustomFieldsFormValues } from "~/features/custom-fields/v2/CustomFieldFormValues";
import useCreateOrUpdateCustomField from "~/features/custom-fields/v2/useCreateOrUpdateCustomField";
import { getCustomFieldType } from "~/features/custom-fields/v2/utils";
import {
  useDeleteCustomFieldDefinitionMutation,
  useGetAllowListQuery,
} from "~/features/plus/plus.slice";
import {
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  ScopeRegistryEnum,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const CustomFieldFormV2 = ({
  initialField,
}: {
  initialField?: CustomFieldDefinitionWithId;
}) => {
  const [form] = Form.useForm<CustomFieldsFormValues>();
  const router = useRouter();

  const [messageApi, messageContext] = message.useMessage();

  const { createOrUpdate } = useCreateOrUpdateCustomField();

  const { data: allowList } = useGetAllowListQuery(
    initialField?.allow_list_id as string,
    {
      skip: !initialField?.allow_list_id,
    },
  );

  const [deleteCustomField, { isLoading: deleteIsLoading }] =
    useDeleteCustomFieldDefinitionMutation();

  const showDeleteButton =
    useHasPermission([ScopeRegistryEnum.CUSTOM_FIELD_DELETE]) && !!initialField;

  const handleDelete = async () => {
    const result = await deleteCustomField({ id: initialField?.id as string });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    // navigate to main page after success toast is shown
    messageApi.success("Custom field deleted successfully", undefined, () => {
      router.push(CUSTOM_FIELDS_ROUTE);
    });
  };

  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);

  const onSubmit = async (values: CustomFieldsFormValues) => {
    const result = await createOrUpdate(values, initialField, allowList);
    if (!result) {
      messageApi.error("An unexpected error occurred");
      return;
    }
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(
        `Custom field ${initialField ? "updated" : "created"} successfully`,
      );
    }
    router.push(CUSTOM_FIELDS_ROUTE);
  };

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

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues || {}}
      validateTrigger={["onBlur", "onChange"]}
      onFinish={onSubmit}
    >
      {messageContext}
      <Form.Item
        label="Name"
        name="name"
        rules={[{ required: true, message: "Please enter a name" }]}
      >
        <Input data-testid="input-name" />
      </Form.Item>

      <Form.Item label="Description" name="description">
        <Input.TextArea rows={2} data-testid="input-description" />
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
          disabled={!!initialField}
          data-testid="select-resource-type"
        />
      </Form.Item>

      <Form.Item
        label="Field Type"
        name="field_type"
        rules={[{ required: true, message: "Please select a field type" }]}
      >
        <Select
          options={FIELD_TYPE_OPTIONS}
          getPopupContainer={(trigger) =>
            trigger.parentElement || document.body
          }
          data-testid="select-field-type"
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
              <Form.List name="options">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map((field, index) => (
                      <Form.Item
                        required={false}
                        key={field.key}
                        label={index === 0 ? "Options" : ""}
                        data-testid="options-form-item"
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
                              () => ({
                                validator(_, value) {
                                  const duplicateCount = getFieldValue(
                                    "options",
                                  ).filter(
                                    (opt: string) => opt === value,
                                  ).length;
                                  if (duplicateCount > 1) {
                                    return Promise.reject(
                                      new Error("Option values must be unique"),
                                    );
                                  }
                                  return Promise.resolve();
                                },
                              }),
                            ]}
                            noStyle
                          >
                            <Input
                              placeholder="Enter option value"
                              data-testid={`input-option-${index}`}
                            />
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
                        data-testid="add-option-btn"
                      >
                        Add select option
                      </Button>
                    </Form.Item>
                  </>
                )}
              </Form.List>
            )
          );
        }}
      </Form.Item>
      <Flex justify="space-between">
        {showDeleteButton && (
          <>
            <Button
              danger
              onClick={() => setDeleteModalIsOpen(true)}
              loading={deleteIsLoading}
              data-testid="delete-btn"
            >
              Delete
            </Button>
            <ConfirmationModal
              isOpen={deleteModalIsOpen}
              onClose={() => setDeleteModalIsOpen(false)}
              onConfirm={handleDelete}
              title="Delete custom field"
              message={
                <Typography.Paragraph>
                  Are you sure you want to delete{" "}
                  <strong>{initialField?.name}</strong>? This action cannot be
                  undone.
                </Typography.Paragraph>
              }
              isCentered
              data-testid="delete-modal"
            />
          </>
        )}
        <Button type="primary" htmlType="submit" data-testid="save-btn">
          Save
        </Button>
      </Flex>
    </Form>
  );
};

export default CustomFieldFormV2;
