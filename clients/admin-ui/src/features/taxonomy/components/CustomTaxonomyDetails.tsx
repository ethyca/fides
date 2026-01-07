import {
  Button,
  Descriptions,
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
import useCreateOrUpdateCustomField from "~/features/custom-fields/useCreateOrUpdateCustomField";
import useCustomFieldValueTypeOptions from "~/features/custom-fields/useCustomFieldValueTypeOptions";
import { useDeleteCustomFieldDefinitionMutation } from "~/features/plus/plus.slice";
import { CustomFieldDefinitionWithId, ScopeRegistryEnum } from "~/types/api";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";
import { isErrorResult } from "~/types/errors";

interface CustomTaxonomyDetailsProps {
  taxonomy?: TaxonomyResponse | null;
  onSubmit: (values: TaxonomyUpdate) => void;
  formId: string;
  customFields: CustomFieldDefinitionWithId[];
}

const CustomTaxonomyDetails = ({
  taxonomy,
  onSubmit,
  formId,
  customFields,
}: CustomTaxonomyDetailsProps) => {
  const { fides_key: fidesKey, ...initialValues } = taxonomy ?? {};

  const [isAdding, setIsAdding] = useState(false);

  const { valueTypeOptions } = useCustomFieldValueTypeOptions();

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

    const result = await createOrUpdate(
      {
        name: (taxonomyType.label as string) ?? taxonomyType.value,
        value_type: taxonomyType.value as string,
        resource_type: fidesKey as string,
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
      <Descriptions>
        <Descriptions.Item label="Fides key">{fidesKey}</Descriptions.Item>
      </Descriptions>
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
      {isAdding && (
        <Select
          options={valueTypeOptions}
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
        {customFields.map((field) => (
          <List.Item
            key={field.id!}
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
        ))}
      </List>
    </Flex>
  );
};

export default CustomTaxonomyDetails;
