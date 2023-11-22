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
  BadgeCell,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import { useEffect, useMemo, useState } from "react";
import {
  ConsentManagementFilterModal,
  useConsentManagementFilters,
  Option,
} from "~/features/configure-consent/ConsentManagementFilterModal";

import {
  useGetHealthQuery,
  useGetVendorReportQuery,
  VendorReport,
  VendorReportResponse,
} from "~/features/plus/plus.slice";
import { useLazyGetSystemByFidesKeyQuery } from "~/features/system/system.slice";
import AddVendor from "~/features/configure-consent/AddVendor";

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
  // const isTcfEnabled = false;
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const [globalFilter, setGlobalFilter] = useState();
  const [systemToEdit, setSystemToEdit] = useState();
  const [getSystemByFidesKey] = useLazyGetSystemByFidesKeyQuery();

  const {
    isOpen: isFilterOpen,
    onOpen: onOpenFilter,
    onClose: onCloseFilter,
    resetFilters,
    purposeOptions,
    onPurposeChange,
    dataUseOptions,
    onDataUseChange,
    legalBasisOptions,
    onLegalBasisChange,
  } = useConsentManagementFilters();

  const getQueryParamsFromList = (optionList: Option[], queryParam: string) => {
    const checkedOptions = optionList.filter((option) => option.isChecked);
    return checkedOptions.length > 0
      ? `${queryParam}=` +
          checkedOptions.map((option) => option.value).join(`&${queryParam}=`)
      : undefined;
  };
  const selectedDataUseFilters = useMemo(
    () => getQueryParamsFromList(dataUseOptions, "data_uses"),
    [dataUseOptions]
  );

  const selectedLegalBasisFilters = useMemo(
    () => getQueryParamsFromList(legalBasisOptions, "legal_bases"),
    [legalBasisOptions]
  );
  const selectedPurposeFilters = useMemo(
    () => getQueryParamsFromList(purposeOptions, "purposes"),
    [purposeOptions]
  );

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
    legalBasis: selectedLegalBasisFilters,
    purposes: selectedPurposeFilters,
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
        meta: {
          // width: "100%",
          maxWidth: "350px",
        },
      }),
      columnHelper.accessor((row) => row.data_uses, {
        id: "tcf_purpose",
        cell: (props) => (
          <BadgeCell suffix="Purposes" value={props.getValue()} />
        ),
        header: (props) => <DefaultHeaderCell value="TCF purpose" {...props} />,
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.data_uses, {
        id: "data_uses",
        cell: (props) => (
          <BadgeCell suffix="Data uses" value={props.getValue()} />
        ),
        header: (props) => <DefaultHeaderCell value="Data Uses" {...props} />,
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.legal_bases, {
        id: "legal_bases",
        cell: (props) => <BadgeCell suffix="Bases" value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Legal Bases" {...props} />,
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.consent_categories, {
        id: "consent_categories",
        cell: (props) => (
          <BadgeCell suffix="Categories" value={props.getValue()} />
        ),
        header: (props) => <DefaultHeaderCell value="Categories" {...props} />,
        meta: {
          width: "175px",
        },
      }),
      columnHelper.accessor((row) => row.cookies, {
        id: "cookies",
        cell: (props) => (
          <BadgeCell suffix="Cookies" value={props.getValue()} />
        ),
        header: (props) => <DefaultHeaderCell value="Cookies" {...props} />,
        meta: {
          width: "175px",
        },
      }),
    ],
    []
  );

  const tableInstance = useReactTable<VendorReport>({
    columns: tcfColumns,
    data,
    state: {
      columnVisibility: {
        tcf_purpose: isTcfEnabled,
        data_uses: isTcfEnabled,
        legal_basis: isTcfEnabled,
        consent_categories: !isTcfEnabled,
        cookies: !isTcfEnabled,
      },
    },
    getCoreRowModel: getCoreRowModel(),
  });

  const onRowClick = async (row: VendorReport) => {
    console.log(row);
    const result = await getSystemByFidesKey(row.fides_key);
    console.log(result);
    setSystemToEdit(result.data);
  };

  if (isReportLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }
  return (
    <Flex flex={1} direction="column" overflow="auto">
      <AddVendor
        passedInSystem={systemToEdit}
        onCloseModal={() => setSystemToEdit(undefined)}
        showButtons={false}
        disableFields
      />
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
          purposeOptions={purposeOptions}
          onPurposeChange={onPurposeChange}
          dataUseOptions={dataUseOptions}
          onDataUseChange={onDataUseChange}
          legalBasisOptions={legalBasisOptions}
          onLegalBasisChange={onLegalBasisChange}
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
      <FidesTableV2 tableInstance={tableInstance} onRowClick={onRowClick} />
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
