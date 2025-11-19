import {
  AntButton as Button,
  AntDescriptions as Descriptions,
  AntDivider as Divider,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntList as List,
  AntModal as Modal,
  AntSelect as Select,
  Icons,
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

  const { valueTypeOptions, customTaxonomies } =
    useCustomFieldValueTypeOptions();

  const canDeleteCustomFieldDefinition = useHasPermission([
    ScopeRegistryEnum.CUSTOM_FIELD_DELETE,
  ]);

  const [modalApi, modalContext] = Modal.useModal();
  const messageApi = useMessage();

  const [deleteMutationTrigger] = useDeleteCustomFieldDefinitionMutation();
  const { createOrUpdate } = useCreateOrUpdateCustomField();

  const removeCustomField = async (fieldId: string) => {
    const result = await deleteMutationTrigger({ id: fieldId });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Attribute removed successfully");
  };

  const handleRemoveClicked = (fieldId: string) => {
    modalApi.confirm({
      title: "Remove attribute",
      content: "Are you sure you want to remove this attribute?",
      onOk: () => removeCustomField(fieldId),
      okText: "Remove",
      centered: true,
    });
  };

  const handleAddCustomFieldDefinition = async (fieldType: string) => {
    const taxonomyType = customTaxonomies?.find(
      (t) => t.fides_key === fieldType,
    );
    if (!taxonomyType || !fidesKey) {
      messageApi.error("Taxonomy type not found");
      return;
    }
    const result = await createOrUpdate(
      {
        name: taxonomyType.name,
        value_type: taxonomyType.fides_key,
        resource_type: fidesKey,
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

  const handleSelectAttributeType = (value: string) => {
    if (value === "custom") {
      console.log("custom attribute type selected");
    } else {
      handleAddCustomFieldDefinition(value);
    }
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
      <Divider />
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
                      onClick={() => handleRemoveClicked(field.id!)}
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
      {isAdding && (
        <Select
          options={valueTypeOptions}
          aria-label="Attribute type"
          onSelect={handleSelectAttributeType}
        />
      )}
      {!isAdding && (
        <Button onClick={() => setIsAdding(true)} icon={<Icons.Add />}>
          Add attribute
        </Button>
      )}
    </Flex>
  );
};

export default CustomTaxonomyDetails;
