import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntMenuProps as MenuProps,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import React from "react";

const { Text } = Typography;

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
    <Flex gap={8} align="center">
      {hasSelections && (
        <Text type="secondary">{selectedIds.length} selected</Text>
      )}
      <Dropdown menu={{ items: menuItems }} disabled={!hasSelections}>
        <Button disabled={!hasSelections}>
          Bulk actions
          <Icons.ChevronDown />
        </Button>
      </Dropdown>
    </Flex>
  );
};
