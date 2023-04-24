import React from "react";
import { CellProps } from "react-table";

import { EnableCell, MapCell } from "~/features/common/table/";
import { FIELD_TYPE_MAP } from "~/features/custom-fields/constants";
import { useUpdateCustomFieldDefinitionMutation } from "~/features/plus/plus.slice";
import { CustomFieldDefinition } from "~/types/api";

export const FieldTypeCell = (
  cellProps: CellProps<typeof FIELD_TYPE_MAP, string>
) => <MapCell map={FIELD_TYPE_MAP} {...cellProps} />;

export const EnableCustomFieldCell = (
  cellProps: CellProps<CustomFieldDefinition, boolean>
) => {
  const [updateCustomFieldDefinitionTrigger] =
    useUpdateCustomFieldDefinitionMutation();
  const { row } = cellProps;

  const onToggle = async (toggle: boolean) => {
    await updateCustomFieldDefinitionTrigger({
      ...row.original,
      active: toggle,
    });
  };

  return (
    <EnableCell<CustomFieldDefinition>
      {...cellProps}
      onToggle={onToggle}
      title="Disable custom field"
      message="Are you sure you want to disable this custom field?"
    />
  );
};
