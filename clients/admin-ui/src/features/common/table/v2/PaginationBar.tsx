import { Table as TableInstance, Updater } from "@tanstack/react-table";
import {
  AntButton as Button,
  ChevronLeftIcon,
  ChevronRightIcon,
  HStack,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
} from "fidesui";
import { useCallback, useMemo, useState } from "react";

export const PAGE_SIZES = [25, 50, 100];

export const useClientSidePagination = <T,>(
  tableInstance: TableInstance<T>,
) => {
  const totalRows = tableInstance.getFilteredRowModel().rows.length;
  const { pageIndex } = tableInstance.getState().pagination;
  const { pageSize } = tableInstance.getState().pagination;
  const onPreviousPageClick = tableInstance.previousPage;
  const isPreviousPageDisabled = !tableInstance.getCanPreviousPage();
  const onNextPageClick = tableInstance.nextPage;
  const isNextPageDisabled = !tableInstance.getCanNextPage();
  const { setPageSize } = tableInstance;
  const startRange = pageIndex * pageSize === 0 ? 1 : pageIndex * pageSize;
  const endRange = pageIndex * pageSize + pageSize;

  return {
    totalRows,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    setPageSize,
    startRange,
    endRange,
  };
};

export const useServerSidePagination = () => {
  const defaultPageIndex = 1;
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0]);
  const [pageIndex, setPageIndex] = useState<number>(defaultPageIndex);
  const [totalPages, setTotalPages] = useState<number | null>();
  const onPreviousPageClick = useCallback(() => {
    setPageIndex((prev) => prev - 1);
  }, [setPageIndex]);
  const isPreviousPageDisabled = useMemo(() => pageIndex === 1, [pageIndex]);
  const onNextPageClick = useCallback(() => {
    setPageIndex((prev) => prev + 1);
  }, [setPageIndex]);
  const isNextPageDisabled = useMemo(
    () => pageIndex === totalPages,
    [pageIndex, totalPages],
  );

  const startRange =
    (pageIndex - 1) * pageSize === 0 ? 1 : (pageIndex - 1) * pageSize;
  const endRange = (pageIndex - 1) * pageSize + pageSize;

  const resetPageIndexToDefault = useCallback(() => {
    setPageIndex(defaultPageIndex);
  }, []);

  const updatePageSize = (newPageSize: Updater<number>) => {
    setPageSize(newPageSize);
    resetPageIndexToDefault();
  };

  return {
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    pageSize,
    setPageSize: updatePageSize,
    PAGE_SIZES,
    startRange,
    endRange,
    pageIndex,
    resetPageIndexToDefault,
    setTotalPages,
  };
};

type PaginationBarProps = {
  pageSizes: number[];
  totalRows: number;
  onPreviousPageClick: () => void;
  isPreviousPageDisabled: boolean;
  onNextPageClick: () => void;
  isNextPageDisabled: boolean;
  setPageSize: (update: Updater<number>) => void;
  startRange: number;
  endRange: number;
};

export const PaginationBar = ({
  pageSizes,
  totalRows,
  onPreviousPageClick,
  isPreviousPageDisabled,
  onNextPageClick,
  isNextPageDisabled,
  setPageSize,
  startRange,
  endRange,
}: PaginationBarProps) => (
  <HStack ml={1} mt={3} mb={1}>
    <Menu>
      <MenuButton as={Button} size="small" data-testid="pagination-btn">
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
    <Button
      icon={<ChevronLeftIcon />}
      size="small"
      aria-label="previous page"
      onClick={onPreviousPageClick}
      disabled={isPreviousPageDisabled}
    />
    <Button
      icon={<ChevronRightIcon />}
      size="small"
      aria-label="next page"
      onClick={onNextPageClick}
      disabled={isNextPageDisabled}
    />
  </HStack>
);
