/* eslint-disable react/no-unstable-nested-components */
import {
  Button,
  ChevronDownIcon,
  Flex,
  Menu,
  MenuButton,
  MenuItemOption,
  MenuList,
} from "@fidesui/react";
import {
  createColumnHelper,
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  GroupCountBadgeCell,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import { useEffect, useMemo, useState } from "react";

import { getQueryParamsFromList } from "~/features/common/modals/FilterModal";
import { useGetMininimalDatamapReportQuery } from "~/features/datamap/datamap.slice";
import {
  DatamapReportFilterModal,
  useDatamapReportFilters,
} from "~/features/datamap/reporting/DatamapReportFilterModal";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import {
  DATAMAP_GROUPING,
  DatamapReport,
  Page_DatamapReport_,
} from "~/types/api";

const columnHelper = createColumnHelper<DatamapReport>();

const emptyMinimalDatamapReportResponse: Page_DatamapReport_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

enum COLUMN_IDS {
  SYSTEM_NAME = "system_name",
  DATA_USE = "data_use",
  DATA_CATEGORY = "data_categories",
  DATA_SUBJECT = "data_subjects",
  LEGAL_NAME = "legal_name",
  DPO = "dpo",
  LEGAL_BASIS_FOR_PROCESSING = "legal_basis_for_processing",
}

const getGrouping = (groupBy: DATAMAP_GROUPING) => {
  let grouping: string[] = [];
  switch (groupBy) {
    case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
      grouping = [COLUMN_IDS.SYSTEM_NAME];
      break;
    }
    case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
      grouping = [COLUMN_IDS.DATA_USE];
      break;
    }
    case DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM: {
      grouping = [COLUMN_IDS.DATA_CATEGORY];
      break;
    }
    default:
      grouping = [COLUMN_IDS.SYSTEM_NAME];
  }
  return grouping;
};
const getColumnOrder = (groupBy: DATAMAP_GROUPING) => {
  let columnOrder: string[] = [];
  if (DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy) {
    columnOrder = [
      COLUMN_IDS.SYSTEM_NAME,
      COLUMN_IDS.DATA_USE,
      COLUMN_IDS.DATA_CATEGORY,
      COLUMN_IDS.DATA_SUBJECT,
    ];
  }
  if (DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy) {
    columnOrder = [
      COLUMN_IDS.DATA_USE,
      COLUMN_IDS.SYSTEM_NAME,
      COLUMN_IDS.DATA_CATEGORY,
      COLUMN_IDS.DATA_SUBJECT,
    ];
  }
  if (DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy) {
    columnOrder = [
      COLUMN_IDS.DATA_CATEGORY,
      COLUMN_IDS.SYSTEM_NAME,
      COLUMN_IDS.DATA_USE,
      COLUMN_IDS.DATA_SUBJECT,
    ];
  }
  return columnOrder;
};

export const DatamapReportTable = () => {
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
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

  const {
    isOpen,
    onClose,
    onOpen,
    resetFilters,
    dataUseOptions,
    onDataUseChange,
    dataCategoriesOptions,
    onDataCategoriesChange,
    dataSubjectOptions,
    onDataSubjectChange,
  } = useDatamapReportFilters();

  const selectedDataUseFilters = useMemo(
    () => getQueryParamsFromList(dataUseOptions, "data_uses"),
    [dataUseOptions]
  );

  const selectedDataCategoriesFilters = useMemo(
    () => getQueryParamsFromList(dataCategoriesOptions, "data_categories"),
    [dataCategoriesOptions]
  );

  const selectedDataSubjectFilters = useMemo(
    () => getQueryParamsFromList(dataSubjectOptions, "data_subjects"),
    [dataSubjectOptions]
  );

  const [groupChangeStarted, setGroupChangeStarted] = useState<boolean>(false);
  const [globalFilter, setGlobalFilter] = useState<string>("");
  const updateGlobalFilter = (searchTerm: string) => {
    resetPageIndexToDefault();
    setGlobalFilter(searchTerm);
  };

  const [groupBy, setGroupBy] = useState<DATAMAP_GROUPING>(
    DATAMAP_GROUPING.SYSTEM_DATA_USE
  );

  const onGroupChange = (group: DATAMAP_GROUPING) => {
    setGroupBy(group);
    setGroupChangeStarted(true);
    resetPageIndexToDefault();
  };

  const {
    data: datamapReport,
    isLoading: isReportLoading,
    isFetching: isReportFetching,
  } = useGetMininimalDatamapReportQuery({
    pageIndex,
    pageSize,
    groupBy,
    search: globalFilter,
    dataUses: selectedDataUseFilters,
    dataSubjects: selectedDataSubjectFilters,
    dataCategories: selectedDataCategoriesFilters,
  });

  const {
    items: data,
    total: totalRows,
    pages: totalPages,
    grouping,
    columnOrder,
  } = useMemo(() => {
    const report = datamapReport || emptyMinimalDatamapReportResponse;
    if (groupChangeStarted) {
      setGroupChangeStarted(false);
    }

    /*
      It's important that `grouping` and `columnOrder` are updated
      in this `useMemo`. It makes it so grouping and column order 
      updates are synced up with when the data changes. Otherwise
      the table will update the grouping and column order before 
      the correct data loads.
    */
    return {
      ...report,
      grouping: getGrouping(groupBy),
      columnOrder: getColumnOrder(groupBy),
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datamapReport]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  const cellWidth = "270px";

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.system_name, {
        enableGrouping: true,
        id: COLUMN_IDS.SYSTEM_NAME,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="System" {...props} />,
        meta: {
          width: cellWidth,
        },
      }),
      columnHelper.accessor((row) => row.data_uses, {
        id: COLUMN_IDS.DATA_USE,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data uses"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => <DefaultHeaderCell value="Data use" {...props} />,
        meta: {
          width: cellWidth,
        },
      }),
      columnHelper.accessor((row) => row.data_categories, {
        id: COLUMN_IDS.DATA_CATEGORY,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data categories"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data categories" {...props} />
        ),
        meta: {
          width: cellWidth,
        },
      }),
      columnHelper.accessor((row) => row.data_subjects, {
        id: COLUMN_IDS.DATA_SUBJECT,
        cell: (props) => (
          <GroupCountBadgeCell
            suffix="data subjects"
            expand={false}
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data subject" {...props} />
        ),
        meta: {
          width: cellWidth,
        },
      }),
      columnHelper.accessor((row) => row.legal_name, {
        id: COLUMN_IDS.LEGAL_NAME,
        cell: (props) => (
          <DefaultCell expand={false} value={props.getValue()} />
        ),
        header: (props) => <DefaultHeaderCell value="Legal Name" {...props} />,
        meta: {
          width: cellWidth,
        },
      }),
      columnHelper.accessor((row) => row.dpo, {
        id: COLUMN_IDS.DPO,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Data privacy officer" {...props} />
        ),
        meta: {
          width: cellWidth,
        },
      }),
      columnHelper.accessor((row) => row.legal_basis_for_processing, {
        id: COLUMN_IDS.LEGAL_BASIS_FOR_PROCESSING,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Legal basis for processing" {...props} />
        ),
        meta: {
          width: cellWidth,
        },
      }),
    ],
    []
  );

  const tableInstance = useReactTable<MinimalDatamapReport>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: tcfColumns,
    manualPagination: true,
    data,
    state: {
      expanded: true,
      grouping,
      columnOrder,
    },
  });

  const getMenuDisplayValue = () => {
    switch (groupBy) {
      case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
        return "system";
      }
      case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
        return "data use";
      }
      case DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM: {
        return "data category";
      }
      default: {
        return "system";
      }
    }
  };

  if (isReportLoading || isLoadingHealthCheck) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <DatamapReportFilterModal
        isOpen={isOpen}
        onClose={onClose}
        resetFilters={resetFilters}
        dataUseOptions={dataUseOptions}
        onDataUseChange={onDataUseChange}
        dataCategoriesOptions={dataCategoriesOptions}
        onDataCategoriesChange={onDataCategoriesChange}
        dataSubjectOptions={dataSubjectOptions}
        onDataSubjectChange={onDataSubjectChange}
      />
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={updateGlobalFilter}
          placeholder="Search"
        />
        <Flex alignItems="center">
          <Menu>
            <MenuButton
              as={Button}
              size="xs"
              variant="outline"
              mr={2}
              rightIcon={<ChevronDownIcon />}
              spinnerPlacement="end"
              isLoading={groupChangeStarted}
              loadingText={`Group by ${getMenuDisplayValue()}`}
            >
              Group by {getMenuDisplayValue()}
            </MenuButton>
            <MenuList zIndex={11}>
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.SYSTEM_DATA_USE);
                }}
                isChecked={DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy}
                value={DATAMAP_GROUPING.SYSTEM_DATA_USE}
              >
                System
              </MenuItemOption>
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.DATA_USE_SYSTEM);
                }}
                isChecked={DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy}
                value={DATAMAP_GROUPING.DATA_USE_SYSTEM}
              >
                Data use
              </MenuItemOption>
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM);
                }}
                isChecked={DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy}
                value={DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM}
              >
                Data category
              </MenuItemOption>
            </MenuList>
          </Menu>
          <Button
            data-testid="filter-multiple-systems-btn"
            size="xs"
            variant="outline"
            onClick={onOpen}
          >
            Filter
          </Button>
        </Flex>
      </TableActionBar>

      <FidesTableV2<MinimalDatamapReport> tableInstance={tableInstance} />
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
