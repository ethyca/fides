import { Table as TableInstance } from "@tanstack/react-table";
import { AntButton, HStack, Td, Text, Tr } from "fidesui";

type RowSelectionBarProps<T> = {
  tableInstance: TableInstance<T>;
  selectedRows: number;
  isOpen: boolean;
};

export const RowSelectionBar = <T,>({
  tableInstance,
  selectedRows,
  isOpen,
}: RowSelectionBarProps<T>) => {
  if (!isOpen) {
    return null;
  }

  return (
    <Tr
      position="sticky"
      zIndex="10"
      top="36px"
      backgroundColor="purple.100"
      height="36px"
      p={0}
      boxShadow="0px 4px 6px -1px rgba(0, 0, 0, 0.05)"
    >
      <Td
        borderWidth="1px"
        borderColor="gray.200"
        height="inherit"
        pl={4}
        pr={2}
        py={0}
        colSpan={tableInstance.getAllColumns().length}
      >
        <HStack>
          <Text data-testid="selected-row-count" fontSize="xs">
            {selectedRows.toLocaleString("en")} row(s) selected.
          </Text>
          {!tableInstance.getIsAllRowsSelected() ? (
            <AntButton
              data-testid="select-all-rows-btn"
              onClick={() => {
                tableInstance.toggleAllRowsSelected();
              }}
              type="link"
              size="small"
              className="text-xs font-normal text-black underline"
            >
              Select all {tableInstance.getFilteredRowModel().rows.length} rows.
            </AntButton>
          ) : null}
        </HStack>
      </Td>
    </Tr>
  );
};
