// eslint-disable react/destructuring-assignment
import { CellContext } from "@tanstack/react-table";
import React from "react";

import {
  BadgeCell,
  DefaultCell,
  EnableCell,
} from "~/features/common/table/v2/cells";
import {
  FIELD_TYPE_MAP,
  RESOURCE_TYPE_MAP,
} from "~/features/custom-fields/constants";
import { useUpdateCustomFieldDefinitionMutation } from "~/features/plus/plus.slice";
import { CustomFieldDefinitionWithId, ResourceTypes } from "~/types/api";

export const ResourceTypeCell = (
  cellProps: CellContext<CustomFieldDefinitionWithId, ResourceTypes>,
) => {
  const mappedValue =
    // eslint-disable-next-line react/destructuring-assignment
    RESOURCE_TYPE_MAP.get(cellProps.getValue()) ?? cellProps.getValue();
  return <DefaultCell {...cellProps} value={mappedValue} />;
};

export const FieldTypeCell = ({
  row,
  getValue,
}: CellContext<CustomFieldDefinitionWithId, string>) => {
  /*
  This value re-assign is here because the `field_type` enum values
  are `string` and `string[]`. When custom fields were first created,
  the select and multi-select fields were tied to `string` and `string[]`.
  Since `open-text` is technically a `string` value the only way to
  differentiate between the two is to check if the `allow_list_id` is
  null or not. If it is null, then it is an `open-text` field.

  When more fields are added a dedicated enum with each field type will
  be created and this hack will be removed.
   */
  const value = row.original.allow_list_id ? getValue() : "open-text";
  const innerText = FIELD_TYPE_MAP.get(value) || value;
  return <BadgeCell value={innerText} />;
};

export const EnableCustomFieldCell = ({
  row,
  getValue,
  isDisabled,
}: CellContext<CustomFieldDefinitionWithId, boolean | undefined> & {
  isDisabled?: boolean;
}) => {
  const isActive = !!getValue();
  const [updateCustomFieldDefinitionTrigger] =
    useUpdateCustomFieldDefinitionMutation();

  const onToggle = async (toggle: boolean) =>
    updateCustomFieldDefinitionTrigger({
      ...row.original,
      active: toggle,
    });

  return (
    <EnableCell
      enabled={isActive}
      onToggle={onToggle}
      title="Disable custom field"
      message="Are you sure you want to disable this custom field?"
      isDisabled={isDisabled}
      aria-label={isActive ? "Disable custom field" : "Enable custom field"}
    />
  );
};
