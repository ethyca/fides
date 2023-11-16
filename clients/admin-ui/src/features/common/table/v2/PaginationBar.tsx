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
import { Table as TableInstance, Updater } from "@tanstack/react-table";

export const PAGE_SIZES = [25, 50, 100];

export const useClientSidePagination = <T,>(
  tableInstance: TableInstance<T>
) => {
  const totalRows = tableInstance.getFilteredRowModel().rows.length;
  const { pageIndex } = tableInstance.getState().pagination;
  const { pageSize } = tableInstance.getState().pagination;
  const onPreviousPageClick = tableInstance.previousPage;
  const isPreviousPageDisabled = !tableInstance.getCanPreviousPage();
  const onNextPageClick = tableInstance.nextPage;
  const isNextPageDisabled = !tableInstance.getCanNextPage();
  const setPageSize = tableInstance.setPageSize;

  return {
    pageIndex,
    pageSize,
    totalRows,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    setPageSize,
  };
};

export const useServerSidePagination = () => {
  const totalRows = tableInstance.getFilteredRowModel().rows.length;
  const { pageIndex } = tableInstance.getState().pagination;
  const { pageSize } = tableInstance.getState().pagination;
  const onPreviousPageClick = tableInstance.previousPage;
  const isPreviousPageDisabled = !tableInstance.getCanPreviousPage();
  const onNextPageClick = tableInstance.nextPage;
  const isNextPageDisabled = !tableInstance.getCanNextPage();
  const setPageSize = tableInstance.setPageSize;

  return {
    pageIndex,
    pageSize,
    totalRows,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    setPageSize,
  };
};

type PaginationBarProps<T> = {
  pageSizes: number[];
  tableInstance: TableInstance<T>;
  pageIndex: number;
  pageSize: number;
  totalRows: number;
  onPreviousPageClick: () => void;
  isPreviousPageDisabled: boolean;
  onNextPageClick: () => void;
  isNextPageDisabled: boolean;
  setPageSize: (update: Updater<number>) => void;
};

export const PaginationBar = <T,>({
  tableInstance,
  pageSizes,
  pageIndex,
  pageSize,
  totalRows,
  onPreviousPageClick,
  isPreviousPageDisabled,
  onNextPageClick,
  isNextPageDisabled,
  setPageSize,
}: PaginationBarProps<T>) => {
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
            {startRange}-{endRange <= totalRows ? endRange : totalRows} of{" "}
            {totalRows}
          </Text>
        </MenuButton>
        <MenuList minWidth="0">
          {pageSizes.map((size) => (
            <MenuItem
              onClick={() => {
                setPageSize(size);
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
          onPreviousPageClick();
        }}
        isDisabled={isPreviousPageDisabled}
      >
        previous
      </IconButton>
      <IconButton
        icon={<ChevronRightIcon />}
        size="xs"
        variant="outline"
        aria-label="next page"
        onClick={() => {
          onNextPageClick();
        }}
        isDisabled={isNextPageDisabled}
      >
        next
      </IconButton>
    </HStack>
  );
};
