import { Table as TableInstance } from "@tanstack/react-table";
import {
  Button,
  HStack,
  Text,
  ChevronLeftIcon,
  ChevronRightIcon,
  IconButton,
} from "@fidesui/react";

type PaginationBarProps<T> = {
  tableInstance: TableInstance<T>;
};

export const PaginationBar = <T,>({ tableInstance }: PaginationBarProps<T>) => {
  const totalRows = tableInstance.getFilteredRowModel().rows.length;
  const pageIndex = tableInstance.getState().pagination.pageIndex;
  const pageSize = tableInstance.getState().pagination.pageSize;
  const startRange = pageIndex * pageSize;
  const endRange = pageIndex * pageSize + pageSize;

  return (
    <HStack mt={3}>
      <Text fontSize="xs" lineHeight={4} fontWeight="semibold">
        {startRange}
        {"-"}
        {endRange <= totalRows ? endRange : totalRows} of {totalRows}
      </Text>
      <IconButton
        icon={<ChevronLeftIcon />}
        size="xs"
        variant="outline"
        aria-label="previous page"
        onClick={() => {
          tableInstance.previousPage();
        }}
        isDisabled={!tableInstance.getCanPreviousPage()}
      >
        previous
      </IconButton>
      <IconButton
        icon={<ChevronRightIcon />}
        size="xs"
        variant="outline"
        aria-label="next page"
        onClick={() => {
          tableInstance.nextPage();
        }}
        isDisabled={!tableInstance.getCanNextPage()}
      >
        next
      </IconButton>
    </HStack>
  );
};
