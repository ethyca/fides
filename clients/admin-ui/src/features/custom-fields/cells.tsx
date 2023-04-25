import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  Text,
  useDisclosure,
  WarningIcon,
} from "@fidesui/react";
import React from "react";
import { CellProps } from "react-table";

import ConfirmationModal from "~/features/common/ConfirmationModal";
import Restrict from "~/features/common/Restrict";
import { EnableCell, MapCell, WrappedCell } from "~/features/common/table/";
import {
  FIELD_TYPE_MAP,
  RESOURCE_TYPE_MAP,
} from "~/features/custom-fields/constants";
import { useUpdateCustomFieldDefinitionMutation } from "~/features/plus/plus.slice";
import {
  CustomFieldDefinition,
  ScopeRegistryEnum,
  ResourceTypes,
} from "~/types/api";

export const ResourceTypeCell = (
  cellProps: CellProps<typeof RESOURCE_TYPE_MAP, string>
) => {
  const mappedValue =
    // eslint-disable-next-line react/destructuring-assignment
    RESOURCE_TYPE_MAP.get(cellProps.value as ResourceTypes) ?? cellProps.value;
  return <WrappedCell {...cellProps} value={mappedValue} />;
};

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

export const MoreActionsCell = ({ row, column }: CellProps<any, any>) => {
  const modal = useDisclosure();
  // Need to stopPropagation on all button calls here since the table row itself
  // also has a click handler. We want the buttons in this cell to take precedence
  // over the row handler
  const handleDelete = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e.stopPropagation();
    modal.onOpen();
  };

  const handleEdit = (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e.stopPropagation();
    // @ts-ignore revisit with react-table v8
    column.onEdit(row.original);
  };

  return (
    <>
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
          <Restrict scopes={[ScopeRegistryEnum.CUSTOM_FIELD_DELETE]}>
            <MenuItem {...MENU_ITEM_PROPS} onClick={handleDelete}>
              Delete
            </MenuItem>
          </Restrict>
          <Restrict scopes={[ScopeRegistryEnum.CUSTOM_FIELD_UPDATE]}>
            <MenuItem {...MENU_ITEM_PROPS} onClick={handleEdit}>
              Edit
            </MenuItem>
          </Restrict>
        </MenuList>
      </Menu>
      <ConfirmationModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        onConfirm={() => {
          // @ts-ignore revisit with react-table v8
          column.onDelete(row.original);
          modal.onClose();
        }}
        title="Delete custom field"
        message={
          <Text color="gray.500">
            Are you sure you want to delete this custom field? This will remove
            the custom field and all stored values and this action can&apos;t be
            undone.
          </Text>
        }
        continueButtonText="Confirm"
        isCentered
        icon={<WarningIcon />}
      />
    </>
  );
};
