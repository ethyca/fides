import {
  AntButton as Button,
  AntFlex as Flex,
  AntTable as Table,
} from "fidesui";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import useCustomFieldsTable from "~/features/custom-fields/useCustomFieldsTable";

const CustomFieldsTable = () => {
  const { tableProps, columns, searchQuery, updateSearch, onAddClick } =
    useCustomFieldsTable();

  return (
    <Flex vertical gap="middle" data-testid="custom-fields-management">
      <Flex
        justify="space-between"
        className="sticky -top-6 z-10 bg-white py-4"
      >
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
      <Table {...tableProps} columns={columns} className="-mt-4" />
    </Flex>
  );
};

export default CustomFieldsTable;
