import React from "react";

import { useCustomFields } from "~/features/common/custom-fields/hooks";
import { ResourceTypes } from "~/types/api";

import SystemDataGroup from "../SystemDataGroup";
import SystemDataTags from "./SystemDataTags";
import SystemDataTextField from "./SystemDataTextField";

interface SystemCustomFieldGroupProps {
  customFields?: Record<string, any>;
}

const SystemCustomFieldGroup: React.FC<SystemCustomFieldGroupProps> = ({
  customFields = {},
}) => {
  const { idToCustomFieldDefinition } = useCustomFields({
    resourceType: ResourceTypes.SYSTEM,
  });

  /** Used to determine if a custom field should be rendered as a text field or data tags.
   * The presence of an allow_list_id indicates either a single or multi-value select
   */
  const isMultivalued = (name: string): boolean =>
    Array.from(idToCustomFieldDefinition.values()).some(
      (value) => value.name === name && !!value.allow_list_id
    );

  return (
    <SystemDataGroup heading="Custom fields">
      {Object.keys(customFields).map((fieldName) =>
        isMultivalued(fieldName) ? (
          <SystemDataTags
            key={fieldName}
            label={fieldName}
            name={`custom_fields.${fieldName}`}
          />
        ) : (
          <SystemDataTextField
            key={fieldName}
            label={fieldName}
            name={`custom_fields.${fieldName}`}
          />
        )
      )}
    </SystemDataGroup>
  );
};

export default SystemCustomFieldGroup;
