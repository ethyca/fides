import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntMenuProps as MenuProps,
  Icons,
} from "fidesui";
import React from "react";

interface BulkActionsDropdownProps {
  selectedIds: React.Key[];
  menuItems: MenuProps["items"];
}

export const BulkActionsDropdown = ({
  selectedIds,
  menuItems,
}: BulkActionsDropdownProps) => {
  const hasSelections = selectedIds.length > 0;

  return (
    <Dropdown menu={{ items: menuItems }} disabled={!hasSelections}>
      <Button data-testid="bulk-actions-btn" disabled={!hasSelections}>
        Actions
        <Icons.ChevronDown />
      </Button>
    </Dropdown>
  );
};
