import {
  Box,
  Button,
  Checkbox,
  CheckboxGroup,
  Menu,
  MenuButton,
  MenuList,
  Stack,
} from "@fidesui/react";

import { ArrowDownLineIcon } from "~/features/common/Icon";

import { ColumnMetadata } from "./types";

interface Props {
  allColumns: ColumnMetadata[];
  selectedColumns: ColumnMetadata[];
  onChange: (columns: ColumnMetadata[]) => void;
}
const ColumnDropdown = ({ allColumns, selectedColumns, onChange }: Props) => {
  const handleClear = () => {
    onChange([]);
  };

  const handleChange = (column: ColumnMetadata) => {
    let newColumns: ColumnMetadata[] = [];
    if (selectedColumns.filter((col) => col.name === column.name).length > 0) {
      // remove from selected columns
      newColumns = selectedColumns.filter((col) => col.name !== column.name);
    } else {
      newColumns = [...selectedColumns, column];
    }

    // we want to keep the sort order the same based off of all columns, so that the
    // table columns don't go jumping around
    const allColumnNames = allColumns.map((c) => c.name);
    const sortedSelected = newColumns
      .slice()
      .sort(
        (a, b) =>
          allColumnNames.indexOf(a.name) - allColumnNames.indexOf(b.name)
      );
    onChange(sortedSelected);
  };

  return (
    <Menu>
      {({ onClose }) => (
        <>
          <MenuButton
            as={Button}
            rightIcon={<ArrowDownLineIcon />}
            variant="outline"
            fontWeight="normal"
          >
            Columns
          </MenuButton>
          <MenuList>
            <Box px={2}>
              <Box display="flex" justifyContent="space-between" mb={2}>
                <Button variant="outline" size="xs" onClick={handleClear}>
                  Clear
                </Button>
                <Button size="xs" colorScheme="primary" onClick={onClose}>
                  Done
                </Button>
              </Box>
              <CheckboxGroup colorScheme="complimentary">
                <Stack>
                  {allColumns.map((column) => {
                    const isChecked =
                      selectedColumns.filter(
                        (selected) => selected.name === column.name
                      ).length > 0;
                    return (
                      <Checkbox
                        id={column.name}
                        key={column.name}
                        _hover={{ bg: "gray.100" }}
                        isChecked={isChecked}
                        onChange={() => handleChange(column)}
                      >
                        {column.name}
                      </Checkbox>
                    );
                  })}
                </Stack>
              </CheckboxGroup>
            </Box>
          </MenuList>
        </>
      )}
    </Menu>
  );
};

export default ColumnDropdown;
