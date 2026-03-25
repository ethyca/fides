import {
  Button,
  ChakraBox as Box,
  ChakraCheckbox as Checkbox,
  ChakraCheckboxGroup as CheckboxGroup,
  ChakraStack as Stack,
  Icons,
  Popover,
} from "fidesui";
import React, { useMemo, useState } from "react";

export interface ColumnMetadata<T = Record<string, unknown>> {
  name: string;
  attribute: keyof T;
}

interface Props<T> {
  allColumns: ColumnMetadata<T>[];
  selectedColumns: ColumnMetadata<T>[];
  onChange: (columns: ColumnMetadata<T>[]) => void;
}
const ColumnDropdown = <T extends Record<string, unknown>>({
  allColumns,
  selectedColumns,
  onChange,
}: Props<T>) => {
  const [open, setOpen] = useState(false);

  const nameToColumnInfo = useMemo(() => {
    const info = new Map<string, boolean>();
    allColumns.forEach((c) =>
      info.set(
        c.name,
        !!selectedColumns.find((selected) => selected.name === c.name),
      ),
    );
    return info;
  }, [allColumns, selectedColumns]);

  const handleClear = () => {
    nameToColumnInfo.forEach((value, key) => nameToColumnInfo.set(key, false));
    onChange([]);
  };

  const handleChange = (column: ColumnMetadata<T>) => {
    // Toggle the column
    const prevInfo = nameToColumnInfo.get(column.name) ?? false;
    nameToColumnInfo.set(column.name, !prevInfo);
    onChange(allColumns.filter((c) => nameToColumnInfo.get(c.name)));
  };

  const content = (
    <Box px={2}>
      <Box display="flex" justifyContent="space-between" mb={2}>
        <Button
          size="small"
          onClick={handleClear}
          data-testid="column-clear-btn"
        >
          Clear
        </Button>
        <Button
          type="primary"
          size="small"
          onClick={() => setOpen(false)}
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
                (selected) => selected.name === column.name,
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
  );

  return (
    <Popover
      content={content}
      trigger="click"
      open={open}
      onOpenChange={setOpen}
      styles={{ body: { padding: 0 } }}
    >
      <Button
        icon={<Icons.ChevronDown />}
        className="!font-normal"
        data-testid="column-dropdown"
      >
        Columns
      </Button>
    </Popover>
  );
};

export default ColumnDropdown;
