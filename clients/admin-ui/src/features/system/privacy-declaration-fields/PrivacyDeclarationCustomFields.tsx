import { Card, Form, Input, Select, Spin } from "fidesui";

import { useCustomFields } from "~/features/common/custom-fields";
import {
  LegacyAllowedTypes,
  LegacyResourceTypes,
} from "~/features/common/custom-fields/types";

interface PrivacyDeclarationCustomFieldsProps {
  privacyDeclarationId?: string;
}

/**
 * antd Form-aware renderer for privacy-declaration custom fields. Mirrors the
 * Formik-based `CustomFieldsList` but uses `Form.Item` with nested name paths
 * (`["customFieldValues", definitionId]`) so values land under the
 * `customFieldValues` namespace in the parent antd form.
 *
 * Returns `null` when custom fields are disabled or no definitions exist.
 */
export const PrivacyDeclarationCustomFields = ({
  privacyDeclarationId,
}: PrivacyDeclarationCustomFieldsProps) => {
  const {
    idToAllowListWithOptions,
    idToCustomFieldDefinition,
    isEnabled,
    isLoading,
    sortedCustomFieldDefinitionIds,
  } = useCustomFields({
    resourceType: LegacyResourceTypes.PRIVACY_DECLARATION,
    resourceFidesKey: privacyDeclarationId,
  });

  if (!isEnabled || sortedCustomFieldDefinitionIds.length === 0) {
    return null;
  }

  return (
    <Card size="small" title="Custom fields">
      {isLoading ? (
        <Spin />
      ) : (
        sortedCustomFieldDefinitionIds.map((definitionId) => {
          const definition = idToCustomFieldDefinition.get(definitionId);
          if (!definition) {
            return null;
          }
          const fieldName = ["customFieldValues", definition.id];
          const isFreeText =
            !definition.allow_list_id &&
            definition.field_type === LegacyAllowedTypes.STRING;

          if (isFreeText) {
            return (
              <Form.Item
                key={definitionId}
                name={fieldName}
                label={definition.name}
                tooltip={definition.description}
              >
                <Input aria-label={definition.name} />
              </Form.Item>
            );
          }

          const allowList = idToAllowListWithOptions.get(
            definition.allow_list_id!,
          );
          if (!allowList) {
            return null;
          }

          const isMulti = definition.field_type !== LegacyAllowedTypes.STRING;

          return (
            <Form.Item
              key={definitionId}
              name={fieldName}
              label={definition.name}
              tooltip={definition.description}
            >
              <Select
                aria-label={definition.name}
                allowClear
                mode={isMulti ? "multiple" : undefined}
                options={allowList.options}
                className="w-full"
              />
            </Form.Item>
          );
        })
      )}
    </Card>
  );
};
