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
  MinimalDatamapReport,
  Page_MinimalDatamapReport_,
} from "~/types/api";

const columnHelper = createColumnHelper<MinimalDatamapReport>();

const emptyMinimalDatamapReportResponse: Page_MinimalDatamapReport_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

const SYSTEM_NAME_COLUMN_ID = "system_name";
const DATA_USE_COLUMN_ID = "data_use";
const DATA_CATEGORY_COLUMN_ID = "data_categories";
const DATA_SUBJECT_COLUMN_ID = "data_subjects";

const getGrouping = (groupBy: DATAMAP_GROUPING) => {
  let grouping = [];
  switch (groupBy) {
    case DATAMAP_GROUPING.SYSTEM_DATA_USE: {
      grouping = [SYSTEM_NAME_COLUMN_ID];
      break;
    }
    case DATAMAP_GROUPING.DATA_USE_SYSTEM: {
      grouping = [DATA_USE_COLUMN_ID];
      break;
    }
    case DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM: {
      grouping = [DATA_CATEGORY_COLUMN_ID];
      break;
    }
    default:
      grouping = [SYSTEM_NAME_COLUMN_ID];
  }
  return grouping;
};
const getColumnOrder = (groupBy: DATAMAP_GROUPING) => {
  let columnOrder = [];
  if (DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy) {
    columnOrder = [
      SYSTEM_NAME_COLUMN_ID,
      DATA_USE_COLUMN_ID,
      DATA_CATEGORY_COLUMN_ID,
      DATA_SUBJECT_COLUMN_ID,
    ];
  }
  if (DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy) {
    columnOrder = [
      DATA_USE_COLUMN_ID,
      SYSTEM_NAME_COLUMN_ID,
      DATA_CATEGORY_COLUMN_ID,
      DATA_SUBJECT_COLUMN_ID,
    ];
  }
  if (DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy) {
    columnOrder = [
      DATA_CATEGORY_COLUMN_ID,
      SYSTEM_NAME_COLUMN_ID,
      DATA_USE_COLUMN_ID,
      DATA_SUBJECT_COLUMN_ID,
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

  const cellWidth = "25%";

  const tcfColumns = useMemo(
    () => [
      columnHelper.accessor((row) => row.system_name, {
        enableGrouping: true,
        id: SYSTEM_NAME_COLUMN_ID,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Vendor" {...props} />,
        meta: {
          width: cellWidth,
        },
      }),
      columnHelper.accessor((row) => row.data_use, {
        id: DATA_USE_COLUMN_ID,
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
      columnHelper.accessor((row) => row.data_category, {
        id: DATA_CATEGORY_COLUMN_ID,
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
      columnHelper.accessor((row) => row.data_subject, {
        id: DATA_SUBJECT_COLUMN_ID,
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
        resetFilter={resetFilters}
        dataUseOptions={dataUseOptions}
        onDataUseChange={onDataUseChange}
        dataCategoriesOptions={dataCategoriesOptions}
        onDataCategoriesChange={onDataCategoriesChange}
        dataSubjectOptions={dataSubjectOptions}
        onDataSubjectChange={onDataSubjectChange}
      />
      <TableActionBar>
        <GlobalFilterV2
          globalFilter=""
          setGlobalFilter={() => {}}
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
