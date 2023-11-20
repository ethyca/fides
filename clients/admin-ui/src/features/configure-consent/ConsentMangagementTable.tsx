import { Flex, Button, useDisclosure } from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useFeatures } from "common/features";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import { useEffect, useMemo, useState } from "react";
import {
  ConsentManagementFilterModal,
  useConsentManagementFilters,
} from "~/features/configure-consent/ConsentManagementFilterModal";

import {
  useGetHealthQuery,
  useGetVendorReportQuery,
  VendorReport,
  VendorReportResponse,
} from "~/features/plus/plus.slice";

const columnHelper = createColumnHelper<VendorReport>();

const emptyVendorReportResponse: VendorReportResponse = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};
export const ConsentManagementTable = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const [globalFilter, setGlobalFilter] = useState();

  const {
    isOpen: isFilterOpen,
    onOpen: onOpenFilter,
    onClose: onCloseFilter,
    resetFilters,
    dataUseOptions,
    onCheckboxChange,
  } = useConsentManagementFilters();

  const selectedDataUseFilters = useMemo(() => {
    const checkedOptions = dataUseOptions.filter((option) => option.isChecked);
    return checkedOptions.length > 0
      ? "data_uses=" +
          checkedOptions.map((option) => option.value).join("&data_uses=")
      : undefined;
  }, [dataUseOptions]);

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
  } = useServerSidePagination();

  const {
    isFetching: isReportFetching,
    isLoading: isReportLoading,
    data: vendorReport,
  } = useGetVendorReportQuery({
    pageIndex,
    pageSize,
    dataUses: selectedDataUseFilters,
    search: globalFilter,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => vendorReport || emptyVendorReportResponse, [vendorReport]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages]);

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Vendor" {...props} />,
      }),
      columnHelper.accessor((row) => row.data_uses, {
        id: "Data Uses",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Data Uses" {...props} />,
      }),
      columnHelper.accessor((row) => row.legal_bases, {
        id: "legal_bases",
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Legal Bases" {...props} />,
      }),
    ],
    []
  );

  const tableInstance = useReactTable<VendorReport>({
    columns: tcfColumns,
    data,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isReportLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }
  return (
    <Flex flex={1} direction="column" overflow="auto">
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={setGlobalFilter}
          placeholder="Search"
        />
        <ConsentManagementFilterModal
          isOpen={isFilterOpen}
          onClose={onCloseFilter}
          resetFilters={resetFilters}
          dataUseOptions={dataUseOptions}
          onCheckboxChange={onCheckboxChange}
        />
        <Flex alignItems="center">
          {isTcfEnabled ? (
            // Wrap in a span so it is consistent height with the add button, whose
            // Tooltip wraps a span
            <span>
              <Button
                onClick={onOpenFilter}
                data-testid="filter-multiple-systems-btn"
                size="xs"
                variant="outline"
              >
                Filter
              </Button>
            </span>
          ) : null}
        </Flex>
      </TableActionBar>
      <FidesTableV2 tableInstance={tableInstance} />
      <PaginationBar
        totalRows={totalRows}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isReportFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isReportFetching}
        startRange={startRange}
        endRange={endRange}
      />
    </Flex>
  );
};
