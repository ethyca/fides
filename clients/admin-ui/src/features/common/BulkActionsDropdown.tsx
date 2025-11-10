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
  totalResults?: number;
}

export const BulkActionsDropdown = ({
  selectedIds,
  menuItems,
  totalResults,
}: BulkActionsDropdownProps) => {
  const hasSelections = selectedIds.length > 0;

  return (
    <Flex gap={8} align="center">
      {hasSelections && (
        <>
          <Text strong data-testid="selected-count">
            {selectedIds.length} selected
          </Text>
          {totalResults !== undefined && <Text type="secondary"> / </Text>}
        </>
      )}
      {totalResults !== undefined && (
        <Text type="secondary" data-testid="total-results">
          {totalResults} results
        </Text>
      )}
      <Dropdown menu={{ items: menuItems }} disabled={!hasSelections}>
        <Button data-testid="bulk-actions-btn" disabled={!hasSelections}>
          Actions
          <Icons.ChevronDown />
        </Button>
      </Dropdown>
    </Flex>
  );
};
