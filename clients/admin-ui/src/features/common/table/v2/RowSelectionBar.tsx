import { Button, HStack, Td, Text, Tr } from "@fidesui/react";
import { Table as TableInstance } from "@tanstack/react-table";

type RowSelectionBarProps<T> = {
  tableInstance: TableInstance<T>;
  selectedRows: number;
};

export const RowSelectionBar = <T,>({
  tableInstance,
  selectedRows,
}: RowSelectionBarProps<T>) => {
  const isOpen = selectedRows !== 0;

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
          <Text fontSize="xs">{selectedRows} row(s) selected.</Text>
          {!tableInstance.getIsAllRowsSelected() ? (
            <Button
              onClick={() => {
                tableInstance.toggleAllRowsSelected();
              }}
              variant="link"
              color="black"
              fontSize="xs"
              fontWeight="400"
              textDecoration="underline"
            >
              Select all {tableInstance.getFilteredRowModel().rows.length} rows.
            </Button>
          ) : null}
        </HStack>
      </Td>
    </Tr>
  );
};
