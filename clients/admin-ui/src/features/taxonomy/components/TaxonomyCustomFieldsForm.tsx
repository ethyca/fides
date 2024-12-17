import {
  AntForm as Form,
  AntFormInstance as FormInstance,
  AntInput as Input,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";
import { isEmpty } from "lodash";

import { useCustomFields } from "~/features/common/custom-fields";
import FidesSpinner from "~/features/common/FidesSpinner";
import { AllowedTypes } from "~/types/api";

interface TaxonomyCustomFieldsFormProps {
  customFields: ReturnType<typeof useCustomFields>;
  formId: string;
  form: FormInstance;
}

const TaxonomyCustomFieldsForm = ({
  customFields,
  formId,
  form,
}: TaxonomyCustomFieldsFormProps) => {
  const {
    idToAllowListWithOptions,
    idToCustomFieldDefinition,
    isEnabled,
    isLoading,
    sortedCustomFieldDefinitionIds,
  } = customFields;

  if (!isEnabled || sortedCustomFieldDefinitionIds.length === 0) {
    return null;
  }

  return (
    <Form
      form={form}
      name={formId}
      initialValues={customFields.customFieldValues}
      layout="vertical"
      data-testid="custom-fields-form"
    >
      <Typography.Title level={5}>Custom fields</Typography.Title>

      {isLoading ? (
        <FidesSpinner />
      ) : (
        <div>
          {!isEmpty(sortedCustomFieldDefinitionIds) && (
            <div>
              {sortedCustomFieldDefinitionIds.map((definitionId) => {
                const customFieldDefinition =
                  idToCustomFieldDefinition.get(definitionId);
                if (!customFieldDefinition) {
                  // This should never happen.
                  return null;
                }

                const {
                  id,
                  name,
                  description,
                  allow_list_id: allowListId,
                  field_type: fieldType,
                } = customFieldDefinition;

                if (!allowListId && fieldType === AllowedTypes.STRING) {
                  return (
                    <Form.Item
                      key={definitionId}
                      name={id}
                      label={name}
                      tooltip={description}
                    >
                      <Input />
                    </Form.Item>
                  );
                }

                const allowList = idToAllowListWithOptions.get(
                  customFieldDefinition.allow_list_id!,
                );
                if (!allowList) {
                  // This would only happen if the field definitions load before
                  // the allow list data.
                  return null;
                }

                const { options } = allowList;
                return (
                  <Form.Item
                    key={definitionId}
                    name={id}
                    label={name}
                    tooltip={description}
                  >
                    <Select
                      mode={fieldType !== "string" ? "multiple" : undefined}
                      allowClear
                      options={options}
                    />
                  </Form.Item>
                );
              })}
            </div>
          )}
        </div>
      )}
    </Form>
  );
};
export default TaxonomyCustomFieldsForm;
