import {
  Button,
  ChevronDownIcon,
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

export const PageSizes = [25, 50, 100];

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
    <HStack mt={3} mb={1}>
      <Text
        fontSize="xs"
        lineHeight={4}
        fontWeight="semibold"
        userSelect="none"
        style={{
          fontVariantNumeric: "tabular-nums",
        }}
        minWidth="122px"
      >
        {startRange}-{endRange <= totalRows ? endRange : totalRows} of{" "}
        {totalRows}
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

      <Menu>
        <MenuButton
          as={Button}
          size="sm"
          rightIcon={<ChevronDownIcon />}
          data-testid="pagination-btn"
        >
          {pageSize}
        </MenuButton>
        <MenuList>
          {pageSizes.map((size) => (
            <MenuItem
              onClick={() => {
                tableInstance.setPageSize(size);
              }}
              key={size}
              data-testid={`pageSize-${size}`}
            >
              {size}
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
    </HStack>
  );
};
