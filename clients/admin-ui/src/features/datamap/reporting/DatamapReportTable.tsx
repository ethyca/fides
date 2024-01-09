/* eslint-disable react/no-unstable-nested-components */
import {
  Button,
  ChevronDownIcon,
  Flex,
  Menu,
  MenuButton,
  MenuItemOption,
  MenuList,
  useDisclosure,
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
  ColumnSettingsModal,
  TableSkeletonLoader,
  useServerSidePagination,
  DraggableColumn,
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

// eslint-disable-next-line @typescript-eslint/naming-convention
enum COLUMN_IDS {
  SYSTEM_NAME = "system_name",
  DATA_USE = "data_use",
  DATA_CATEGORY = "data_categories",
  DATA_SUBJECT = "data_subjects",
  LEGAL_NAME = "legal_name",
  DPO = "dpo",
  LEGAL_BASIS_FOR_PROCESSING = "legal_basis_for_processing",
  ADMINISTRATING_DEPARTMENT = "adminstrating_department",
  COOKIE_MAX_AGE_SECONDS = "cookie_max_age_seconds",
  PRIVACY_POLICY = "privacy_policy",
  LEGAL_ADDRESS = "legal_address",
  COOKIE_REFRESH = "cookie_refresh",
  DATA_SECURITY_PRACTICES = "data_security_practices",
  DATA_SHARED_WITH_THIRD_PARTIES = "DATA_SHARED_WITH_THIRD_PARTIES",
  DATA_STEWARDS = "data_stewards",
  DECLARATION_NAME = "declaration_name",
  DESCRIPTION = "description",
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

const getPrefixColumns = (groupBy: DATAMAP_GROUPING) => {
  let columnOrder: string[] = [];
  if (DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy) {
    columnOrder = [COLUMN_IDS.SYSTEM_NAME, COLUMN_IDS.DATA_USE];
  }
  if (DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy) {
    columnOrder = [COLUMN_IDS.DATA_USE, COLUMN_IDS.SYSTEM_NAME];
  }
  if (DATAMAP_GROUPING.DATA_CATEGORY_SYSTEM === groupBy) {
    columnOrder = [COLUMN_IDS.DATA_CATEGORY, COLUMN_IDS.SYSTEM_NAME];
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
          minWidth: cellWidth,
          displayText: "System",
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
          minWidth: cellWidth,
          displayText: "Data use",
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
          displayText: "Data categories",
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
          displayText: "Data subject",
        },
      }),
      columnHelper.accessor((row) => row.legal_name, {
        id: COLUMN_IDS.LEGAL_NAME,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => <DefaultHeaderCell value="Legal name" {...props} />,
        meta: {
          width: cellWidth,
          displayText: "Legal name",
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
          displayText: "Data privacy officer",
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
          displayText: "Legal basis for processing",
        },
      }),
      columnHelper.accessor((row) => row.administrating_department, {
        id: COLUMN_IDS.ADMINISTRATING_DEPARTMENT,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Administrating department" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Administrating department",
        },
      }),
      columnHelper.accessor((row) => row.cookie_max_age_seconds, {
        id: COLUMN_IDS.COOKIE_MAX_AGE_SECONDS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Cookie max age seconds" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Cookie max age seconds",
        },
      }),
      columnHelper.accessor((row) => row.privacy_policy, {
        id: COLUMN_IDS.PRIVACY_POLICY,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Privacy policy" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Privacy policy",
        },
      }),
      columnHelper.accessor((row) => row.legal_address, {
        id: COLUMN_IDS.LEGAL_ADDRESS,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Legal address" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Legal address",
        },
      }),
      columnHelper.accessor((row) => row.cookie_refresh, {
        id: COLUMN_IDS.COOKIE_REFRESH,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Cookie refresh"
            table={props.table}
            header={props.header}
            column={props.column}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Cookie refresh",
        },
      }),
      columnHelper.accessor((row) => row.data_security_practices, {
        id: COLUMN_IDS.DATA_SECURITY_PRACTICES,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Data security practices" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data security practices",
        },
      }),
      columnHelper.accessor((row) => row.data_shared_with_third_parties, {
        id: COLUMN_IDS.DATA_SHARED_WITH_THIRD_PARTIES,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell
            value="Data shared with third parties"
            {...props}
          />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data shared with third parties",
        },
      }),
      columnHelper.accessor((row) => row.data_stewards, {
        id: COLUMN_IDS.DATA_STEWARDS,
        cell: (props) => (
          <GroupCountBadgeCell
            expand={false}
            suffix="data stewards"
            value={props.getValue()}
          />
        ),
        header: (props) => (
          <DefaultHeaderCell value="Data stewards" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Data stewards",
        },
      }),
      columnHelper.accessor((row) => row.declaration_name, {
        id: COLUMN_IDS.DECLARATION_NAME,
        cell: (props) => <DefaultCell value={props.getValue()} />,
        header: (props) => (
          <DefaultHeaderCell value="Declaration name" {...props} />
        ),
        meta: {
          width: cellWidth,
          displayText: "Declaration name",
        },
      }),
    ],
    []
  );

  const {
    isOpen: isColumnSettingsOpen,
    onOpen: onColumnSettingsOpen,
    onClose: onColumnSettingsClose,
  } = useDisclosure();

  const tableInstance = useReactTable<DatamapReport>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns: tcfColumns,
    manualPagination: true,
    data,
    initialState: {
      columnOrder,
    },
    state: {
      expanded: true,
      grouping,
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
      <ColumnSettingsModal<DatamapReport>
        isOpen={isColumnSettingsOpen}
        onClose={onColumnSettingsClose}
        prefixColumns={getPrefixColumns(groupBy)}
        onSave={(e) => {
          tableInstance.setColumnOrder([
            ...getPrefixColumns(groupBy),
            ...e.map((e) => e.id),
          ]);
          tableInstance.setColumnVisibility(
            e.reduce(
              (acc: Record<string, boolean>, current: DraggableColumn) => {
                acc[current.id] = current.isVisible;
                return acc;
              },
              {}
            )
          );
        }}
        tableInstance={tableInstance}
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
            </MenuList>
          </Menu>
          <Button
            data-testid="filter-multiple-systems-btn"
            size="xs"
            variant="outline"
            onClick={onColumnSettingsOpen}
          >
            Edit columns
          </Button>
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

      <FidesTableV2<DatamapReport> tableInstance={tableInstance} />
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
