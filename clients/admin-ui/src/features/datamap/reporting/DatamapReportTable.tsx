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
import { get } from "lodash";
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

  const [selectedSystemId, setSelectedSystemId] = useState<string>();

  /* Local storage: preserve table states between sessions */
  const [groupBy, setGroupBy] = useLocalStorage<DATAMAP_GROUPING>(
    DATAMAP_LOCAL_STORAGE_KEYS.GROUP_BY,
    DATAMAP_GROUPING.SYSTEM_DATA_USE,
  );
  const [columnOrder, setColumnOrder] = useLocalStorage<string[]>(
    DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_ORDER,
    getColumnOrder(groupBy),
  );
  const [columnVisibility, setColumnVisibility] = useLocalStorage<
    Record<string, boolean>
  >(DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_VISIBILITY, {
    [COLUMN_IDS.SYSTEM_UNDECLARED_DATA_CATEGORIES]: false,
    [COLUMN_IDS.DATA_USE_UNDECLARED_DATA_CATEGORIES]: false,
  });
  const [columnSizing, setColumnSizing] = useLocalStorage<
    Record<string, number>
  >(DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_SIZING, {});
  const [selectedFilters, setSelectedFilters] =
    useLocalStorage<DatamapReportFilterSelections>(
      DATAMAP_LOCAL_STORAGE_KEYS.FILTERS,
      {
        dataUses: [],
        dataSubjects: [],
        dataCategories: [],
      },
    );
  /* End Local storage */

  const [groupChangeStarted, setGroupChangeStarted] = useState<boolean>(false);
  const onGroupChange = (group: DATAMAP_GROUPING) => {
    setGroupBy(group);
    setGroupChangeStarted(true);
    resetPageIndexToDefault();
  };

  const [globalFilter, setGlobalFilter] = useState<string>("");
  const updateGlobalFilter = useCallback(
    (searchTerm: string) => {
      resetPageIndexToDefault();
      setGlobalFilter(searchTerm);
    },
    [resetPageIndexToDefault, setGlobalFilter],
  );

  const reportQuery = {
    pageIndex,
    pageSize,
    groupBy,
    search: globalFilter,
    dataUses: getQueryParamsFromArray(selectedFilters.dataUses, "data_uses"),
    dataSubjects: getQueryParamsFromArray(
      selectedFilters.dataSubjects,
      "data_subjects",
    ),
    dataCategories: getQueryParamsFromArray(
      selectedFilters.dataCategories,
      "data_categories",
    ),
  };

  const {
    data: datamapReport,
    isLoading: isReportLoading,
    isFetching: isReportFetching,
  } = useGetMinimalDatamapReportQuery(reportQuery);

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
      ...reportQuery,
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
    manualPagination: true,
    enableColumnResizing: true,
    columnResizeMode: "onChange",
    columns,
    data,
    initialState: {
      expanded: true,
      columnSizing,
      columnOrder,
      columnVisibility,
      grouping: getGrouping(groupBy),
    },
  });

  useEffect(() => {
    // changing the groupBy should wait until the data is loaded to update the grouping
    const newGrouping = getGrouping(groupBy);
    if (datamapReport) {
      tableInstance.setGrouping(newGrouping);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datamapReport]);

  useEffect(() => {
    // update stored column sizing when it changes
    const colSizing = tableInstance.getState().columnSizing;
    if (colSizing) {
      setColumnSizing(colSizing);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableInstance.getState().columnSizing]);

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

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <DatamapReportFilterModal
        selectedFilters={selectedFilters}
        isOpen={isFilterModalOpen}
        onClose={onFilterModalClose}
        onFilterChange={setSelectedFilters}
      />
      <ColumnSettingsModal<DatamapReport>
        isOpen={isColumnSettingsOpen}
        onClose={onColumnSettingsClose}
        headerText="Data map settings"
        prefixColumns={getPrefixColumns(groupBy)}
        tableInstance={tableInstance}
        onColumnOrderChange={(newColumnOrder) => {
          tableInstance.setColumnOrder(newColumnOrder);
          setColumnOrder(newColumnOrder);
        }}
        onColumnVisibilityChange={(newColumnVisibility) => {
          tableInstance.setColumnVisibility(newColumnVisibility);
          setColumnVisibility(newColumnVisibility);
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
          {/* <CustomReportTemplates
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
          /> */}
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
