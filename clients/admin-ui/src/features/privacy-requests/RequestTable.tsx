import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import {
  Box,
  BoxProps,
  Button,
  FormLabel,
  HStack,
  IconButton,
  Switch,
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
  requestCSVDownload,
  selectPrivacyRequestFilters,
  setRequestId,
  useGetAllPrivacyRequestsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";
import { getRequestTableColumns } from "~/features/privacy-requests/RequestTableColumns";
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
    // resetPageIndexToDefault,
  } = useServerSidePagination();

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

  const tableInstance = useReactTable<PrivacyRequestEntity>({
    getCoreRowModel: getCoreRowModel(),
    data: requests,
    columns: useMemo(() => getRequestTableColumns(revealPII), [revealPII]),
    manualPagination: true,
  });

  /**
   TASK: handle filters
   * Don’t build in reviewed by filter yet - Fides doesn’t support this
   * Request type - Support three options: Access, Erasure, Consent
   * If the API supports it - include the “Days Left” filter
   */

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
          <Button data-testid="filter-btn" size="xs" variant="outline">
            Filter
          </Button>
          {/* TASK: create filter modal */}
          <IconButton
            aria-label="Export report"
            data-testid="export-btn"
            size="xs"
            variant="outline"
            icon={<DownloadLightIcon />}
            onClick={handleExport}
          />
        </HStack>
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
          />
          <PaginationBar
            totalRows={totalRows}
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
