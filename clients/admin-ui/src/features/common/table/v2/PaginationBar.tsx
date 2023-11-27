import {
  Button,
  ChevronLeftIcon,
  ChevronRightIcon,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
} from "@fidesui/react";
import { Table as TableInstance } from "@tanstack/react-table";

export const PAGE_SIZES = [25, 50, 100];

type PaginationBarProps<T> = {
  pageSizes: number[];
  tableInstance: TableInstance<T>;
};

export const PaginationBar = <T,>({
  tableInstance,
  pageSizes,
}: PaginationBarProps<T>) => {
  const totalRows = tableInstance.getFilteredRowModel().rows.length;
  const { pageIndex } = tableInstance.getState().pagination;
  const { pageSize } = tableInstance.getState().pagination;
  const startRange = pageIndex * pageSize;
  const endRange = pageIndex * pageSize + pageSize;

  return (
    <HStack ml={1} mt={3} mb={1}>
      <Menu>
        <MenuButton
          as={Button}
          size="xs"
          variant="ghost"
          data-testid="pagination-btn"
        >
          <Text
            fontSize="xs"
            lineHeight={4}
            fontWeight="semibold"
            userSelect="none"
            style={{
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {startRange.toLocaleString("en")}-
            {endRange <= totalRows
              ? endRange.toLocaleString("en")
              : totalRows.toLocaleString("en")}{" "}
            of {totalRows.toLocaleString("en")}
          </Text>
        </MenuButton>
        <MenuList minWidth="0">
          {pageSizes.map((size) => (
            <MenuItem
              onClick={() => {
                tableInstance.setPageSize(size);
              }}
              key={size}
              data-testid={`pageSize-${size}`}
              fontSize="xs"
            >
              {size} per view
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
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
