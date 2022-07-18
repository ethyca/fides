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
import { useMemo } from "react";

import { ArrowDownLineIcon } from "~/features/common/Icon";

import { ColumnMetadata } from "./types";

interface Props {
  allColumns: ColumnMetadata[];
  selectedColumns: ColumnMetadata[];
  onChange: (columns: ColumnMetadata[]) => void;
}
const ColumnDropdown = ({ allColumns, selectedColumns, onChange }: Props) => {
  const nameToColumnInfo = useMemo(() => {
    const info = new Map<string, boolean>();
    allColumns.forEach((c) => info.set(c.name, true));
    return info;
  }, [allColumns]);

  const handleClear = () => {
    nameToColumnInfo.forEach((value, key) => nameToColumnInfo.set(key, false));
    onChange([]);
  };

  const handleChange = (column: ColumnMetadata) => {
    // Toggle the column
    const prevInfo = nameToColumnInfo.get(column.name) ?? false;
    nameToColumnInfo.set(column.name, !prevInfo);
    onChange(allColumns.filter((c) => nameToColumnInfo.get(c.name)));
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
            data-testid="column-dropdown"
          >
            Columns
          </MenuButton>
          <MenuList>
            <Box px={2}>
              <Box display="flex" justifyContent="space-between" mb={2}>
                <Button
                  variant="outline"
                  size="xs"
                  onClick={handleClear}
                  data-testid="column-clear-btn"
                >
                  Clear
                </Button>
                <Button
                  size="xs"
                  colorScheme="primary"
                  onClick={onClose}
                  data-testid="column-done-btn"
                >
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
                        data-testid={`checkbox-${column.name}`}
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
