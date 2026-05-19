import { Form, Input, Select, Spin } from "fidesui";

import {
  LegacyAllowedTypes,
  LegacyResourceTypes,
} from "~/features/common/custom-fields/types";
import SystemFormInputGroup from "~/features/system/SystemFormInputGroup";

import { useCustomFields } from "./hooks";

type CustomFieldsListProps = {
  resourceFidesKey?: string;
  resourceType: LegacyResourceTypes;
};

export const CustomFieldsList = ({
  resourceFidesKey,
  resourceType,
}: CustomFieldsListProps) => {
  const {
    idToAllowListWithOptions,
    idToCustomFieldDefinition,
    isEnabled,
    isLoading,
    sortedCustomFieldDefinitionIds,
  } = useCustomFields({
    resourceFidesKey,
    resourceType,
  });

  if (!isEnabled || sortedCustomFieldDefinitionIds.length === 0) {
    return null;
  }

  return (
    <SystemFormInputGroup heading="Custom fields">
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

          const testNameSegment = `customFieldValues.${definition.id}`;

          if (isFreeText) {
            return (
              <Form.Item
                key={definitionId}
                name={fieldName}
                label={definition.name}
                tooltip={definition.description}
              >
                <Input
                  aria-label={definition.name}
                  data-testid={`input-${testNameSegment}`}
                />
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
                data-testid={`controlled-select-${testNameSegment}`}
              />
            </Form.Item>
          );
        })
      )}
    </SystemFormInputGroup>
  );
};
