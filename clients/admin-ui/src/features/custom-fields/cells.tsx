import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
} from "@fidesui/react";
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

const MENU_ITEM_PROPS = { _hover: { color: "complimentary.500" } };

export const MoreActionsCell = (cellProps: CellProps<any, any>) => {
  // Need to stopPropagation on all button calls here since the table row itself
  // also has a click handler. We want the buttons in this cell to take precedence
  // over the row handler
  const handleDelete = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e.stopPropagation();
    console.log("delete");
  };
  const handleEdit = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e.stopPropagation();
    console.log("edit");
  };
  return (
    <Menu size="sm">
      <MenuButton
        as={Button}
        variant="outline"
        data-testid="more-actions-btn"
        size="xs"
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <MoreIcon />
      </MenuButton>
      <MenuList>
        <MenuItem {...MENU_ITEM_PROPS} onClick={handleDelete}>
          Delete
        </MenuItem>
        <MenuItem {...MENU_ITEM_PROPS} onClick={handleEdit}>
          Edit
        </MenuItem>
      </MenuList>
    </Menu>
  );
};
