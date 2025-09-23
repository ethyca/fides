import {
  AntButton as Button,
  AntFlex as Flex,
  AntTable as Table,
} from "fidesui";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import useCustomFieldsTable from "~/features/custom-fields/useCustomFieldsTable";

export const CustomFieldsTable = () => {
  const { tableProps, columns, searchQuery, updateSearch, onAddClick } =
    useCustomFieldsTable();

  return (
    <Flex vertical gap="middle">
      <Flex justify="space-between">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search custom fields..."
        />
        <Button
          onClick={onAddClick}
          type="primary"
          data-testid="add-custom-field-btn"
        >
          Add custom field
        </Button>
      </Flex>
      <Table {...tableProps} columns={columns} />
    </Flex>
  );
};
