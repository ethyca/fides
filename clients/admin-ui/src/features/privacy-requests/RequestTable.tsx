import {
  ColumnSort,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Box,
  BoxProps,
  Button,
  FormLabel,
  HStack,
  IconButton,
  Portal,
  Switch,
  useDisclosure,
  useToast,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { selectToken } from "~/features/auth";
import { DownloadLightIcon } from "~/features/common/Icon";
import {
  FidesTableV2,
  GlobalFilterV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "~/features/common/table/v2";
import {
  clearSortFields,
  requestCSVDownload,
  selectPrivacyRequestFilters,
  setRequestId,
  setSortDirection,
  setSortField,
  useGetAllPrivacyRequestsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { getRequestTableColumns } from "~/features/privacy-requests/RequestTableColumns";
import { RequestTableFilterModal } from "~/features/privacy-requests/RequestTableFilterModal";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

export const RequestTable = ({ ...props }: BoxProps): JSX.Element => {
  const [requestIdFilter, setRequestIdFilter] = useState<string>();
  const [revealPII, setRevealPII] = useState<boolean>(false);
  const filters = useSelector(selectPrivacyRequestFilters);
  const token = useSelector(selectToken);
  const toast = useToast();
  const router = useRouter();
  const dispatch = useDispatch();
  const {
    PAGE_SIZES,
    pageSize,
    setPageSize,
    onPreviousPageClick,
    isPreviousPageDisabled,
    onNextPageClick,
    isNextPageDisabled,
    startRange,
    endRange,
    pageIndex,
    setTotalPages,
    resetPageIndexToDefault,
  } = useServerSidePagination();

  const { isOpen, onOpen, onClose } = useDisclosure();

  const { data, isLoading, isFetching } = useGetAllPrivacyRequestsQuery({
    ...filters,
    page: pageIndex,
    size: pageSize,
  });
  const { items: requests, total: totalRows } = useMemo(() => {
    const results = data || { items: [], total: 0, pages: 0 };
    setTotalPages(results.pages);
    return results;
  }, [data, setTotalPages]);

  const handleSearch = (searchTerm: string) => {
    dispatch(setRequestId(searchTerm));
    setRequestIdFilter(searchTerm);
    resetPageIndexToDefault();
  };

  const handleExport = async () => {
    let message;
    try {
      await requestCSVDownload({ ...filters, token });
    } catch (error) {
      if (error instanceof Error) {
        message = error.message;
      } else {
        message = "Unknown error occurred";
      }
    }
    if (message) {
      toast({
        description: `${message}`,
        duration: 5000,
        status: "error",
      });
    }
  };

  const handleViewDetails = (id: string) => {
    const url = `/privacy-requests/${id}`;
    router.push(url);
  };

  const handleSort = (columnSort: ColumnSort) => {
    if (!columnSort) {
      dispatch(clearSortFields());
      resetPageIndexToDefault();
      return;
    }
    const { id, desc } = columnSort;
    dispatch(setSortField(id));
    dispatch(setSortDirection(desc ? "desc" : "asc"));
    resetPageIndexToDefault();
  };

  const tableInstance = useReactTable<PrivacyRequestEntity>({
    getCoreRowModel: getCoreRowModel(),
    data: requests,
    columns: useMemo(() => getRequestTableColumns(revealPII), [revealPII]),
    getRowId: (row) => `${row.status}-${row.id}`,
    manualPagination: true,
  });

  return (
    <Box {...props}>
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={requestIdFilter}
          setGlobalFilter={handleSearch}
          placeholder="Search by request ID"
        />
        <HStack alignItems="center" spacing={4}>
          <HStack alignItems="center">
            <FormLabel htmlFor="reveal-pii" fontSize="xs" m={0}>
              Reveal PII
            </FormLabel>
            <Switch
              data-testid="pii-toggle"
              colorScheme="secondary"
              size="sm"
              isChecked={revealPII}
              onChange={() => setRevealPII(!revealPII)}
              id="reveal-pii"
            />
          </HStack>
          <Button
            data-testid="filter-btn"
            size="xs"
            variant="outline"
            onClick={onOpen}
          >
            Filter
          </Button>
          <IconButton
            aria-label="Export report"
            data-testid="export-btn"
            size="xs"
            variant="outline"
            icon={<DownloadLightIcon />}
            onClick={handleExport}
          />
        </HStack>
        <Portal>
          <RequestTableFilterModal
            isOpen={isOpen}
            onClose={onClose}
            onFilterChange={resetPageIndexToDefault}
          />
        </Portal>
      </TableActionBar>
      {isLoading ? (
        <Box p={2} borderWidth={1}>
          <TableSkeletonLoader rowHeight={26} numRows={10} />
        </Box>
      ) : (
        <>
          <FidesTableV2<PrivacyRequestEntity>
            tableInstance={tableInstance}
            onRowClick={(row) => handleViewDetails(row.id)}
            onSort={handleSort}
          />
          <PaginationBar
            totalRows={totalRows || 0}
            pageSizes={PAGE_SIZES}
            setPageSize={setPageSize}
            onPreviousPageClick={onPreviousPageClick}
            isPreviousPageDisabled={isPreviousPageDisabled || isFetching}
            onNextPageClick={onNextPageClick}
            isNextPageDisabled={isNextPageDisabled || isFetching}
            startRange={startRange}
            endRange={endRange}
          />
        </>
      )}
    </Box>
  );
};
