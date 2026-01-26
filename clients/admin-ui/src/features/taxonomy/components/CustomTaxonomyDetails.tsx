import {
  Button,
  Descriptions,
  EnterExitList,
  Flex,
  Form,
  Icons,
  Input,
  List,
  Modal,
  Select,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import { VALUE_TYPE_RESOURCE_TYPE_MAP } from "~/features/custom-fields/constants";
import useCreateOrUpdateCustomField from "~/features/custom-fields/useCreateOrUpdateCustomField";
import useCustomFieldValueTypeOptions from "~/features/custom-fields/useCustomFieldValueTypeOptions";
import { useDeleteCustomFieldDefinitionMutation } from "~/features/plus/plus.slice";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import { CustomFieldDefinitionWithId, ScopeRegistryEnum } from "~/types/api";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";
import { isErrorResult } from "~/types/errors";

interface CustomTaxonomyDetailsProps {
  taxonomy?: TaxonomyResponse | null;
  onSubmit: (values: TaxonomyUpdate) => void;
  formId: string;
  customFields: CustomFieldDefinitionWithId[];
  isCustom?: boolean;
}

const CustomTaxonomyDetails = ({
  taxonomy,
  onSubmit,
  formId,
  customFields,
  isCustom = false,
}: CustomTaxonomyDetailsProps) => {
  const { fides_key: fidesKey, ...initialValues } = taxonomy ?? {};

  const [isAdding, setIsAdding] = useState(false);

  const { valueTypeOptions } = useCustomFieldValueTypeOptions();
  const filteredValueTypeOptions = valueTypeOptions.filter(
    (option) => option.value !== fidesKey,
  );

  const canDeleteCustomFieldDefinition = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_DELETE,
  ]);

  const [modalApi, modalContext] = Modal.useModal();
  const messageApi = useMessage();

  const [deleteMutationTrigger] = useDeleteCustomFieldDefinitionMutation();
  const { createOrUpdate } = useCreateOrUpdateCustomField();

  const removeCustomField = async (field: CustomFieldDefinitionWithId) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { id, resource_type, field_type } = field;
    const result = await deleteMutationTrigger({
      id: id!,
      resource_type,
      field_type,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Attribute removed successfully");
  };

  const handleRemoveClicked = (field: CustomFieldDefinitionWithId) => {
    modalApi.confirm({
      title: "Remove attribute",
      content: "Are you sure you want to remove this attribute?",
      onOk: () => removeCustomField(field),
      okText: "Remove",
      centered: true,
    });
  };

  const handleAddCustomFieldDefinition = async (fieldType: string) => {
    const taxonomyType = valueTypeOptions?.find((t) => t.value === fieldType);
    if (!taxonomyType || !fidesKey) {
      messageApi.error("Taxonomy type not found");
      return;
    }

    const resourceType =
      VALUE_TYPE_RESOURCE_TYPE_MAP[fidesKey as TaxonomyTypeEnum] ?? fidesKey;

    const result = await createOrUpdate(
      {
        name: (taxonomyType.label as string) ?? taxonomyType.value,
        value_type: taxonomyType.value as string,
        resource_type: resourceType,
      },
      undefined,
      undefined,
    );
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Attribute added successfully");
    setIsAdding(false);
  };

  return (
    <Flex vertical gap="large">
      {modalContext}
      <Descriptions column={1}>
        <Descriptions.Item label="Fides key">{fidesKey}</Descriptions.Item>
        {!isCustom && (
          <>
            <Descriptions.Item label="Name">
              {taxonomy?.name ?? ""}
            </Descriptions.Item>
            {taxonomy?.description && (
              <Descriptions.Item label="Description">
                {taxonomy?.description ?? ""}
              </Descriptions.Item>
            )}
          </>
        )}
      </Descriptions>
      {isCustom && (
        <Form
          id={formId}
          layout="vertical"
          initialValues={initialValues}
          onFinish={onSubmit}
        >
          <Form.Item
            label="Name"
            name="name"
            rules={[{ required: true, message: "Name is required" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea />
          </Form.Item>
        </Form>
      )}
      {isAdding && (
        <Select
          options={filteredValueTypeOptions}
          defaultOpen
          aria-label="Attribute type"
          onSelect={handleAddCustomFieldDefinition}
        />
      )}
      {!isAdding && (
        <Button onClick={() => setIsAdding(true)} icon={<Icons.Add />}>
          Add attribute
        </Button>
      )}
      <List>
        <EnterExitList
          dataSource={customFields}
          itemKey={(field) => field.id!}
          renderItem={(field) => (
            <List.Item
              actions={
                canDeleteCustomFieldDefinition
                  ? [
                      <Button
                        key="remove"
                        type="link"
                        onClick={() => handleRemoveClicked(field)}
                      >
                        Remove
                      </Button>,
                    ]
                  : undefined
              }
            >
              <List.Item.Meta
                title={field.name}
                description={field.description}
              />
            </List.Item>
          )}
          className="flex-col"
          itemClassName="w-full"
        />
      </List>
    </Flex>
  );
};

export default CustomTaxonomyDetails;
