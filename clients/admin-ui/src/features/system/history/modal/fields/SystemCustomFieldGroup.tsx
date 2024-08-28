import React from "react";

import { useCustomFields } from "~/features/common/custom-fields/hooks";
import { ResourceTypes } from "~/types/api";

import SystemDataGroup from "../SystemDataGroup";
import SystemDataTags from "./SystemDataTags";
import SystemDataTextField from "./SystemDataTextField";

interface SystemCustomFieldGroupProps {
  customFields?: Record<string, any>;
  resourceType: ResourceTypes;
}

const SystemCustomFieldGroup = ({
  customFields = {},
  resourceType,
}: SystemCustomFieldGroupProps) => {
  const { idToCustomFieldDefinition } = useCustomFields({
    resourceType,
  });

  /** Used to determine if a custom field should be rendered as a text field or data tags.
   * The presence of an allow_list_id indicates either a single or multi-value select
   */
  const isMultivalued = (name: string): boolean =>
    Array.from(idToCustomFieldDefinition.values()).some(
      (value) => value.name === name && !!value.allow_list_id,
    );

  const prefix =
    resourceType === ResourceTypes.SYSTEM
      ? "custom_fields"
      : "privacy_declarations[0].custom_fields";

  // to ensure the order in the diff lists is the same
  const sortedFieldNames = Object.keys(customFields).sort();

  return (
    <SystemDataGroup heading="Custom fields">
      {sortedFieldNames.map((fieldName) =>
        isMultivalued(fieldName) ? (
          <SystemDataTags
            key={fieldName}
            label={fieldName}
            name={`${prefix}.${fieldName}`}
          />
        ) : (
          <SystemDataTextField
            key={fieldName}
            label={fieldName}
            name={`${prefix}.${fieldName}`}
          />
        ),
      )}
    </SystemDataGroup>
  );
};

export default SystemCustomFieldGroup;
