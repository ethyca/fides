import { FC } from "react";
import { Td, Tr, Button, Text, HStack } from "@fidesui/react";
import { Table as TableInstance } from "@tanstack/react-table";

type RowSelectionBarProps<T> = {
  tableInstance: TableInstance<T>;
};

export const RowSelectionBar = <T,>({
  tableInstance,
}: RowSelectionBarProps<T>) => {
  const isOpen = tableInstance.getSelectedRowModel().rows.length > 0;

  if (!isOpen) {
    return null;
  }

  return (
    <Tr backgroundColor="purple.100" height="36px" p={0}>
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
          <Text fontSize="xs">
            {tableInstance.getSelectedRowModel().rows.length} row(s) selected.
          </Text>
          <Button
            onClick={tableInstance.toggleAllRowsSelected}
            variant="link"
            color="black"
            fontSize="xs"
            fontWeight="400"
            textDecoration="underline"
          >
            Select all {} rows.
          </Button>
        </HStack>
      </Td>
    </Tr>
  );
};
