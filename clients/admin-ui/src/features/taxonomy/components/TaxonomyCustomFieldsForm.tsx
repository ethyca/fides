import { AntForm, AntFormInstance, AntInput, AntSelect } from "fidesui";
import { isEmpty } from "lodash";

import { useCustomFields } from "~/features/common/custom-fields";
import FidesSpinner from "~/features/common/FidesSpinner";
import { AllowedTypes } from "~/types/api";

interface TaxonomyCustomFieldsFormProps {
  customFields: ReturnType<typeof useCustomFields>;
  formId: string;
  form: AntFormInstance;
}

export const customFieldsFormBaseName = "customFieldValues";

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
    <AntForm
      form={form}
      name={formId}
      initialValues={customFields.customFieldValues}
      layout="vertical"
    >
      <h3 className="mb-3 font-semibold text-gray-700">Custom fields</h3>
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
                    <AntForm.Item
                      key={definitionId}
                      name={id}
                      label={name}
                      tooltip={description}
                    >
                      <AntInput />
                    </AntForm.Item>
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
                  <AntForm.Item
                    key={definitionId}
                    name={id}
                    label={name}
                    tooltip={description}
                  >
                    <AntSelect
                      mode={fieldType !== "string" ? "multiple" : undefined}
                      allowClear
                      options={options}
                    />
                  </AntForm.Item>
                );
              })}
            </div>
          )}
        </div>
      )}
    </AntForm>
  );
};
export default TaxonomyCustomFieldsForm;
