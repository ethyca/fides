/* eslint-disable jsx-a11y/control-has-associated-label */
import {
  AntAutoComplete as AutoComplete,
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  AntSkeleton as Skeleton,
  AntTypography as Typography,
  Icons,
  useAntModal,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";

import { LegacyResourceTypes } from "~/features/common/custom-fields";
import { getErrorMessage } from "~/features/common/helpers";
import { CUSTOM_FIELDS_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import {
  FIELD_TYPE_OPTIONS,
  FieldTypes,
  RESOURCE_TYPE_MAP,
} from "~/features/custom-fields/constants";
import { CustomFieldsFormValues } from "~/features/custom-fields/CustomFieldFormValues";
import useCreateOrUpdateCustomField from "~/features/custom-fields/useCreateOrUpdateCustomField";
import useCustomFieldValueTypeOptions from "~/features/custom-fields/useCustomFieldValueTypeOptions";
import { getCustomFieldType } from "~/features/custom-fields/utils";
import {
  useDeleteCustomFieldDefinitionMutation,
  useGetAllowListQuery,
  useGetCustomFieldLocationsQuery,
} from "~/features/plus/plus.slice";
import {
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  ScopeRegistryEnum,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

export const SkeletonCustomFieldForm = () => {
  return (
    <Skeleton active>
      <Skeleton.Input />
      <Skeleton.Input />
      <Skeleton.Input />
      <Skeleton.Input />
      <Skeleton.Button />
    </Skeleton>
  );
};

const parseResourceType = (resourceType: string): string => {
  if (RESOURCE_TYPE_MAP.has(resourceType as LegacyResourceTypes)) {
    return RESOURCE_TYPE_MAP.get(resourceType as LegacyResourceTypes) as string;
  }
  if (
    resourceType.startsWith("taxonomy:") ||
    resourceType.startsWith("system:")
  ) {
    return resourceType;
  }
  // otherwise, type is a custom taxonomy
  return `taxonomy:${resourceType}`;
};

const CustomFieldForm = ({
  initialField,
  isLoading,
}: {
  initialField?: CustomFieldDefinitionWithId;
  isLoading?: boolean;
}) => {
  const [form] = Form.useForm<CustomFieldsFormValues>();
  const valueType = Form.useWatch("value_type", form);
  const name = Form.useWatch("name", form);
  const router = useRouter();
  const { resource_type: queryResourceType } = router.query;

  const messageApi = useMessage();
  const modalApi = useAntModal();

  const { createOrUpdate } = useCreateOrUpdateCustomField();

  const { data: allowList, isLoading: isAllowListLoading } =
    useGetAllowListQuery(initialField?.allow_list_id as string, {
      skip: !initialField?.allow_list_id,
    });

  const [deleteCustomField, { isLoading: deleteIsLoading }] =
    useDeleteCustomFieldDefinitionMutation();
  const { data: locations, isLoading: isLocationsLoading } =
    useGetCustomFieldLocationsQuery();

  const { valueTypeOptions } = useCustomFieldValueTypeOptions();

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

  const confirmDelete = () => {
    modalApi.confirm({
      title: "Delete custom field?",
      content: (
        <Typography.Paragraph>
          Are you sure you want to delete <strong>{initialField?.name}</strong>{" "}
          This action cannot be undone.
        </Typography.Paragraph>
      ),
      onOk: handleDelete,
      okType: "primary",
      okText: "Delete",
      centered: true,
    });
  };

  const onSubmit = async (values: CustomFieldsFormValues) => {
    const result = await createOrUpdate(values, initialField, allowList);
    if (!result) {
      messageApi.error("An unexpected error occurred");
      return;
    }
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success(
      `Custom field ${initialField ? "updated" : "created"} successfully`,
    );
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
      value_type: field.field_type,
      field_type: getCustomFieldType(field),
      resource_type: parseResourceType(field.resource_type),
      options: allowList?.allowed_values ?? [],
    };
  };

  const defaultInitialValues = parseFieldToFormValues(initialField);

  const initialValues = queryResourceType
    ? {
        ...defaultInitialValues,
        resource_type: `taxonomy:${queryResourceType}`,
      }
    : defaultInitialValues;

  if (isLoading || isAllowListLoading || isLocationsLoading) {
    return <SkeletonCustomFieldForm />;
  }

  const isTaxonomyType = valueTypeOptions.some(
    (option) => option.value === valueType,
  );

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues || {}}
      validateTrigger={["onBlur", "onChange"]}
      onFinish={onSubmit}
    >
      <Form.Item
        label="Name"
        name="name"
        rules={[{ required: true, message: "Please enter a name" }]}
      >
        <AutoComplete
          options={valueTypeOptions}
          onSelect={(_, option) => {
            form.setFieldsValue({
              name: option.label as string,
              value_type: option.value as string,
            });
          }}
          disabled={isTaxonomyType}
          data-testid="input-name-autocomplete"
        >
          <Input
            data-testid="input-name"
            suffix={
              isTaxonomyType ? (
                <Button
                  size="small"
                  type="text"
                  icon={<Icons.Close />}
                  onClick={() => {
                    form.setFieldsValue({
                      name: undefined,
                      value_type: undefined,
                    });
                  }}
                />
              ) : undefined
            }
          />
        </AutoComplete>
      </Form.Item>

      <Form.Item label="Type" name="value_type" hidden>
        <Select
          options={valueTypeOptions}
          getPopupContainer={(trigger) =>
            trigger.parentElement || document.body
          }
          data-testid="select-value-type"
        />
      </Form.Item>

      {!!name && !isTaxonomyType && (
        <>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} data-testid="input-description" />
          </Form.Item>

          <Form.Item
            label="Field type"
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
                  <Form.List
                    name="options"
                    rules={[
                      {
                        validator: async (_, options) => {
                          if (!options || options.length < 1) {
                            return Promise.reject(
                              new Error(
                                "At least one option is required for selects",
                              ),
                            );
                          }
                          return Promise.resolve();
                        },
                      },
                    ]}
                  >
                    {(fields, { add, remove }, { errors }) => (
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
                        <Form.ErrorList
                          errors={errors}
                          className="-mt-4 mb-4"
                        />
                      </>
                    )}
                  </Form.List>
                )
              );
            }}
          </Form.Item>
        </>
      )}

      <Form.Item
        label="Applies to"
        name="resource_type"
        rules={[{ required: true, message: "Please select a location" }]}
        tooltip="Choose where this field applies, including taxonomies"
      >
        <Select
          options={
            locations?.map((loc: string) => ({
              label: loc,
              value: loc,
            })) ?? []
          }
          getPopupContainer={(trigger) =>
            trigger.parentElement || document.body
          }
          disabled={!!initialField}
          data-testid="select-resource-type"
        />
      </Form.Item>

      <Flex justify="space-between">
        {showDeleteButton && (
          <>
            <Button
              danger
              onClick={confirmDelete}
              loading={deleteIsLoading}
              data-testid="delete-btn"
            >
              Delete
            </Button>
          </>
        )}
        <Button type="primary" htmlType="submit" data-testid="save-btn">
          Save
        </Button>
      </Flex>
    </Form>
  );
};

export default CustomFieldForm;
