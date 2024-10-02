import {
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
  TableState,
  useReactTable,
} from "@tanstack/react-table";
import {
  ColumnSettingsModal,
  FidesTableV2,
  GlobalFilterV2,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
  useServerSidePagination,
} from "common/table/v2";
import {
  Button,
  ChevronDownIcon,
  Flex,
  IconButton,
  Menu,
  MenuButton,
  MenuItemOption,
  MenuList,
  useDisclosure,
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { DownloadLightIcon } from "~/features/common/Icon";
import { getQueryParamsFromArray } from "~/features/common/utils";
import {
  DATAMAP_LOCAL_STORAGE_KEYS,
  ExportFormat,
} from "~/features/datamap/constants";
import {
  useExportMinimalDatamapReportMutation,
  useGetMinimalDatamapReportQuery,
} from "~/features/datamap/datamap.slice";
import DatamapDrawer from "~/features/datamap/datamap-drawer/DatamapDrawer";
import ReportExportModal from "~/features/datamap/modals/ReportExportModal";
import {
  DatamapReportFilterModal,
  DatamapReportFilterSelections,
} from "~/features/datamap/reporting/DatamapReportFilterModal";
import {
  selectAllCustomFieldDefinitions,
  useGetAllCustomFieldDefinitionsQuery,
  useGetHealthQuery,
} from "~/features/plus/plus.slice";
import { DATAMAP_GROUPING, Page_DatamapReport_ } from "~/types/api";

import { CustomReportTemplates } from "./CustomReportTemplates";
import { DatamapReportWithCustomFields as DatamapReport } from "./datamap-report";
import {
  COLUMN_IDS,
  getDatamapReportColumns,
} from "./DatamapReportTableColumns";
import { getColumnOrder, getGrouping, getPrefixColumns } from "./utils";

const emptyMinimalDatamapReportResponse: Page_DatamapReport_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

export const DatamapReportTable = () => {
  const [tableState, setTableState] = useLocalStorage<TableState | undefined>(
    DATAMAP_LOCAL_STORAGE_KEYS.TABLE_STATE,
    undefined,
  );
  const storedTableState = useMemo(
    // snag the stored table state from local storage if it exists and use it to initialize the tableInstance.
    // memoize this so we don't get stuck in a loop as the tableState gets updated during the session.
    () => tableState,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
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
    isOpen: isFilterModalOpen,
    onClose: onFilterModalClose,
    onOpen: onFilterModalOpen,
  } = useDisclosure();

  const {
    getDataUseDisplayName,
    getDataCategoryDisplayName,
    getDataSubjectDisplayName,
    isLoading: isLoadingFidesLang,
  } = useTaxonomies();

  const [selectedDataUseFilters, setSelectedDataUseFilters] =
    useState<string>();
  const [selectedDataCategoriesFilters, setSelectedDataCategoriesFilters] =
    useState<string>();
  const [selectedDataSubjectFilters, setSelectedDataSubjectFilters] =
    useState<string>();
  const [selectedSystemId, setSelectedSystemId] = useState<string>();

  const [groupChangeStarted, setGroupChangeStarted] = useState<boolean>(false);
  const [globalFilter, setGlobalFilter] = useState<string>("");
  const updateGlobalFilter = useCallback(
    (searchTerm: string) => {
      resetPageIndexToDefault();
      setGlobalFilter(searchTerm);
    },
    [resetPageIndexToDefault, setGlobalFilter],
  );

  const [groupBy, setGroupBy] = useLocalStorage<DATAMAP_GROUPING>(
    DATAMAP_LOCAL_STORAGE_KEYS.GROUP_BY,
    DATAMAP_GROUPING.SYSTEM_DATA_USE,
  );

  const [columnOrder, setColumnOrder] = useLocalStorage<string[]>(
    DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_ORDER,
    getColumnOrder(groupBy),
  );

  const [grouping, setGrouping] = useLocalStorage<string[]>(
    DATAMAP_LOCAL_STORAGE_KEYS.TABLE_GROUPING,
    getGrouping(groupBy),
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
  } = useGetMinimalDatamapReportQuery({
    pageIndex,
    pageSize,
    groupBy,
    search: globalFilter,
    dataUses: selectedDataUseFilters,
    dataSubjects: selectedDataSubjectFilters,
    dataCategories: selectedDataCategoriesFilters,
  });

  const [
    exportMinimalDatamapReport,
    { isLoading: isExportingReport, isSuccess: isExportReportSuccess },
  ] = useExportMinimalDatamapReportMutation();

  const { data, totalRows } = useMemo(() => {
    const report = datamapReport || emptyMinimalDatamapReportResponse;
    // Type workaround since extending BaseDatamapReport with custom fields causes some trouble
    const items = report.items as DatamapReport[];
    if (groupChangeStarted) {
      setGroupChangeStarted(false);
    }

    setTotalPages(report.pages);

    return {
      totalRows: report.total,
      data: items,
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datamapReport]);

  useEffect(() => {
    // changing the groupBy should wait until the data is loaded to update the grouping
    const newGrouping = getGrouping(groupBy);
    if (datamapReport) {
      setGrouping(newGrouping);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datamapReport]);

  // Get custom fields
  useGetAllCustomFieldDefinitionsQuery();
  const customFields = useAppSelector(selectAllCustomFieldDefinitions);

  const columns = useMemo(
    () =>
      getDatamapReportColumns({
        onSelectRow: (row) => setSelectedSystemId(row.fides_key),
        getDataUseDisplayName,
        getDataCategoryDisplayName,
        getDataSubjectDisplayName,
        datamapReport,
        customFields,
      }),
    [
      getDataUseDisplayName,
      getDataSubjectDisplayName,
      getDataCategoryDisplayName,
      datamapReport,
      customFields,
    ],
  );

  const {
    isOpen: isColumnSettingsOpen,
    onOpen: onColumnSettingsOpen,
    onClose: onColumnSettingsClose,
  } = useDisclosure();

  const {
    isOpen: isExportReportOpen,
    onOpen: onExportReportOpen,
    onClose: onExportReportClose,
  } = useDisclosure();

  const onExport = (downloadType: ExportFormat) => {
    exportMinimalDatamapReport({
      pageIndex,
      pageSize,
      groupBy,
      search: globalFilter,
      dataUses: selectedDataUseFilters,
      dataSubjects: selectedDataSubjectFilters,
      dataCategories: selectedDataCategoriesFilters,
      format: downloadType,
    }).then(() => {
      if (isExportReportSuccess) {
        onExportReportClose();
      }
    });
  };

  const tableInstance = useReactTable<DatamapReport>({
    getCoreRowModel: getCoreRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    columns,
    manualPagination: true,
    data,
    initialState: {
      columnVisibility: {
        [COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES]: false,
        [COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES]: false,
      },
      ...storedTableState,
    },
    state: {
      expanded: true,
      grouping,
      columnOrder,
    },
    columnResizeMode: "onChange",
    enableColumnResizing: true,
    onStateChange: (updater) => {
      const valueToStore =
        updater instanceof Function
          ? updater(tableInstance.getState())
          : updater;
      setTableState(valueToStore);
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
      default: {
        return "system";
      }
    }
  };

  if (isReportLoading || isLoadingHealthCheck || isLoadingFidesLang) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  const handleFilterChange = (newFilters: DatamapReportFilterSelections) => {
    setSelectedDataUseFilters(
      getQueryParamsFromArray(newFilters.dataUses, "data_uses"),
    );
    setSelectedDataCategoriesFilters(
      getQueryParamsFromArray(newFilters.dataCategories, "data_categories"),
    );
    setSelectedDataSubjectFilters(
      getQueryParamsFromArray(newFilters.dataSubjects, "data_subjects"),
    );
  };

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <DatamapReportFilterModal
        isOpen={isFilterModalOpen}
        onClose={onFilterModalClose}
        onFilterChange={handleFilterChange}
      />
      <ColumnSettingsModal<DatamapReport>
        isOpen={isColumnSettingsOpen}
        onClose={onColumnSettingsClose}
        headerText="Data map settings"
        prefixColumns={getPrefixColumns(groupBy)}
        tableInstance={tableInstance}
        onColumnOrderChange={(newColumnOrder) => {
          setColumnOrder(newColumnOrder);
        }}
      />
      <ReportExportModal
        isOpen={isExportReportOpen}
        onClose={onExportReportClose}
        onConfirm={onExport}
        isLoading={isExportingReport}
      />
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={updateGlobalFilter}
          placeholder="System name, Fides key, or ID"
        />
        <Flex alignItems="center" gap={2}>
          <CustomReportTemplates
            currentTableState={tableState}
            currentColumnMap={undefined}
            onTemplateApplied={(newState) => {
              tableInstance.setState((old) => {
                return {
                  ...old,
                  ...newState.config.table_state,
                };
              });
            }}
          />
          <Menu>
            <MenuButton
              as={Button}
              size="xs"
              variant="outline"
              rightIcon={<ChevronDownIcon />}
              spinnerPlacement="end"
              isLoading={groupChangeStarted}
              loadingText={`Group by ${getMenuDisplayValue()}`}
              data-testid="group-by-menu"
            >
              Group by {getMenuDisplayValue()}
            </MenuButton>
            <MenuList zIndex={11} data-testid="group-by-menu-list">
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.SYSTEM_DATA_USE);
                }}
                isChecked={DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy}
                value={DATAMAP_GROUPING.SYSTEM_DATA_USE}
                data-testid="group-by-system-data-use"
              >
                System
              </MenuItemOption>
              <MenuItemOption
                onClick={() => {
                  onGroupChange(DATAMAP_GROUPING.DATA_USE_SYSTEM);
                }}
                isChecked={DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy}
                value={DATAMAP_GROUPING.DATA_USE_SYSTEM}
                data-testid="group-by-data-use-system"
              >
                Data use
              </MenuItemOption>
            </MenuList>
          </Menu>
          <Button
            data-testid="edit-columns-btn"
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
            onClick={onFilterModalOpen}
          >
            Filter
          </Button>
          <IconButton
            aria-label="Export report"
            data-testid="export-btn"
            size="xs"
            variant="outline"
            onClick={onExportReportOpen}
            icon={<DownloadLightIcon />}
          />
        </Flex>
      </TableActionBar>

      <FidesTableV2<DatamapReport>
        tableInstance={tableInstance}
        columnExpandStorageKey={
          DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_EXPANSION_STATE
        }
        columnWrapStorageKey={DATAMAP_LOCAL_STORAGE_KEYS.WRAPPING_COLUMNS}
      />
      <PaginationBar
        totalRows={totalRows || 0}
        pageSizes={PAGE_SIZES}
        setPageSize={setPageSize}
        onPreviousPageClick={onPreviousPageClick}
        isPreviousPageDisabled={isPreviousPageDisabled || isReportFetching}
        onNextPageClick={onNextPageClick}
        isNextPageDisabled={isNextPageDisabled || isReportFetching}
        startRange={startRange}
        endRange={endRange}
      />

      <DatamapDrawer
        selectedSystemId={selectedSystemId}
        resetSelectedSystemId={() => setSelectedSystemId(undefined)}
      />
    </Flex>
  );
};
