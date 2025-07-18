import {
  getCoreRowModel,
  getExpandedRowModel,
  getGroupedRowModel,
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
  AntButton as Button,
  ChevronDownIcon,
  Flex,
  Menu,
  MenuButton,
  MenuItem,
  MenuItemOption,
  MenuList,
  MoreIcon,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik, FormikState } from "formik";
import { debounce } from "lodash";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { CustomReportColumn } from "~/features/common/custom-reports/types";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { DownloadLightIcon } from "~/features/common/Icon";
import { useHasPermission } from "~/features/common/Restrict";
import { getQueryParamsFromArray } from "~/features/common/utils";
import { ExportFormat } from "~/features/datamap/constants";
import {
  useExportMinimalDatamapReportMutation,
  useGetMinimalDatamapReportQuery,
} from "~/features/datamap/datamap.slice";
import DatamapDrawer from "~/features/datamap/datamap-drawer/DatamapDrawer";
import ReportExportModal from "~/features/datamap/modals/ReportExportModal";
import { DatamapReportFilterModal } from "~/features/datamap/reporting/DatamapReportFilterModal";
import {
  selectAllCustomFieldDefinitions,
  useGetAllCustomFieldDefinitionsQuery,
  useGetHealthQuery,
} from "~/features/plus/plus.slice";
import {
  CustomReportResponse,
  DATAMAP_GROUPING,
  Page_DatamapReport_,
  ReportType,
  ScopeRegistryEnum,
} from "~/types/api";

import { CustomReportTemplates } from "../../common/custom-reports/CustomReportTemplates";
import { DATAMAP_LOCAL_STORAGE_KEYS, DEFAULT_COLUMN_NAMES } from "./constants";
import { DatamapReportWithCustomFields as DatamapReport } from "./datamap-report";
import {
  DEFAULT_COLUMN_FILTERS,
  DEFAULT_COLUMN_VISIBILITY,
  useDatamapReport,
} from "./datamap-report-context";
import {
  getDatamapReportColumns,
  getDefaultColumn,
} from "./DatamapReportTableColumns";
import { RenameColumnsButtons } from "./RenameColumnsButtons";
import { getColumnOrder, getGrouping, getPrefixColumns } from "./utils";

const emptyMinimalDatamapReportResponse: Page_DatamapReport_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

export const DatamapReportTable = () => {
  const userCanSeeReports = useHasPermission([
    ScopeRegistryEnum.CUSTOM_REPORT_READ,
  ]);
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
  const toast = useToast({ id: "datamap-report-toast" });

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

  const [selectedSystemId, setSelectedSystemId] = useState<string>(); // for opening the drawer

  const {
    savedCustomReportId,
    setSavedCustomReportId,
    groupBy,
    setGroupBy,
    selectedFilters,
    setSelectedFilters,
    columnOrder,
    setColumnOrder,
    columnVisibility,
    setColumnVisibility,
    columnSizing,
    setColumnSizing,
    columnNameMapOverrides,
    setColumnNameMapOverrides,
  } = useDatamapReport();

  const [groupChangeStarted, setGroupChangeStarted] = useState<boolean>(false);
  const onGroupChange = (group: DATAMAP_GROUPING) => {
    setSavedCustomReportId("");
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
    { isLoading: isExportingReport, isError: isExportReportError },
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

  // Column renaming
  const [isRenamingColumns, setIsRenamingColumns] = useState(false);
  const handleColumnRenaming = (values: Record<string, string>) => {
    setSavedCustomReportId("");
    setColumnNameMapOverrides(values);
    setIsRenamingColumns(false);
  };

  const columns = useMemo(
    () =>
      datamapReport
        ? getDatamapReportColumns({
            onSelectRow: (row) => setSelectedSystemId(row.fides_key),
            getDataUseDisplayName,
            getDataCategoryDisplayName,
            getDataSubjectDisplayName,
            datamapReport,
            customFields,
            isRenaming: isRenamingColumns,
          })
        : [],
    [
      getDataUseDisplayName,
      getDataSubjectDisplayName,
      getDataCategoryDisplayName,
      datamapReport,
      customFields,
      isRenamingColumns,
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
    const columnMap: Record<string, CustomReportColumn> = {};
    Object.entries(columnVisibility).forEach(([key, isVisible]) => {
      columnMap[key] = {
        enabled: isVisible,
      };
    });

    Object.entries(columnNameMapOverrides).forEach(([key, label]) => {
      if (columnMap[key]) {
        columnMap[key].label = label;
      } else {
        columnMap[key] = {
          label,
          enabled: columnVisibility[key] ?? true,
        };
      }
    });
    exportMinimalDatamapReport({
      ...reportQuery,
      format: downloadType,
      report_id: savedCustomReportId,
      report: {
        name: "",
        type: "datamap",
        config: {
          column_map: columnMap,
          table_state: {
            groupBy,
            filters: selectedFilters,
            columnOrder,
          },
        },
      },
    }).then(() => {
      if (!isExportReportError) {
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
    defaultColumn: getDefaultColumn(
      { ...DEFAULT_COLUMN_NAMES, ...columnNameMapOverrides },
      isRenamingColumns,
    ),
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
    if (groupBy && !!tableInstance && !!datamapReport) {
      if (tableInstance.getState().columnOrder.length === 0) {
        const tableColumnIds = tableInstance.getAllColumns().map((c) => c.id);
        setColumnOrder(getColumnOrder(groupBy, tableColumnIds));
      } else {
        setColumnOrder(
          getColumnOrder(groupBy, tableInstance.getState().columnOrder),
        );
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupBy, tableInstance, datamapReport]);

  useEffect(() => {
    // changing the groupBy should wait until the data is loaded to update the grouping
    const newGrouping = getGrouping(groupBy);
    if (datamapReport) {
      tableInstance.setGrouping(newGrouping);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datamapReport]);

  const debouncedSetColumnSizing = useMemo(
    () => debounce(setColumnSizing, 300),
    [setColumnSizing],
  );

  useEffect(() => {
    // update stored column sizing when it changes
    const colSizing = tableInstance.getState().columnSizing;
    if (colSizing) {
      debouncedSetColumnSizing(colSizing);
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

  const handleSavedReport = (
    savedReport: CustomReportResponse | null,
    resetColumnNameForm: (
      nextState?: Partial<FormikState<Record<string, string>>> | undefined,
    ) => void,
  ) => {
    if (!savedReport && !savedCustomReportId) {
      return;
    }
    if (!savedReport) {
      try {
        setSavedCustomReportId("");

        /* NOTE: we can't just use tableInstance.reset() here because it will reset the table to the initial state, which is likely to include report settings that were saved in the user's local storage. Instead, we need to reset each individual setting to its default value. */

        // reset column visibility (must happen before updating order)
        setColumnVisibility(DEFAULT_COLUMN_VISIBILITY);
        tableInstance.toggleAllColumnsVisible(true);
        tableInstance.setColumnVisibility(DEFAULT_COLUMN_VISIBILITY);

        // reset column order (must happen prior to updating groupBy)
        setColumnOrder([]);
        tableInstance.setColumnOrder([]);

        // reset groupBy and filters (will automatically update the tableinstance)
        setGroupBy(DATAMAP_GROUPING.SYSTEM_DATA_USE);
        setSelectedFilters(DEFAULT_COLUMN_FILTERS);

        // reset column names
        setColumnNameMapOverrides({});
        resetColumnNameForm({ values: {} });
      } catch (error: any) {
        toast({
          status: "error",
          description: "There was a problem resetting the report.",
        });
      }
      return;
    }
    try {
      if (savedReport.config?.table_state) {
        const {
          groupBy: savedGroupBy,
          filters: savedFilters,
          columnOrder: savedColumnOrder,
        } = savedReport.config.table_state;
        const savedColumnVisibility: Record<string, boolean> = {};

        Object.entries(savedReport.config.column_map ?? {}).forEach(
          ([key, value]) => {
            savedColumnVisibility[key] = value.enabled || false;
          },
        );

        if (savedGroupBy) {
          // No need to manually update the tableInstance here; setting the groupBy will trigger the useEffect to update the grouping.
          setGroupBy(savedGroupBy);
        }
        if (savedFilters) {
          setSelectedFilters(savedFilters);
        }
        if (savedColumnOrder) {
          setColumnOrder(savedColumnOrder);
          tableInstance.setColumnOrder(savedColumnOrder);
        }
        if (savedColumnVisibility) {
          setColumnVisibility(savedColumnVisibility);
          tableInstance.setColumnVisibility(savedColumnVisibility);
        }
      }
      if (savedReport.config?.column_map) {
        const columnNameMap: Record<string, string> = {};
        Object.entries(savedReport.config.column_map ?? {}).forEach(
          ([key, value]) => {
            if (value.label) {
              columnNameMap[key] = value.label;
            }
          },
        );
        setColumnNameMapOverrides(columnNameMap);
        resetColumnNameForm({ values: columnNameMap });
      }
      setSavedCustomReportId(savedReport.id);
      toast({
        status: "success",
        description: "Report applied successfully.",
      });
    } catch (error: any) {
      toast({
        status: "error",
        description: "There was a problem applying report.",
      });
    }
  };

  if (isReportLoading || isLoadingHealthCheck || isLoadingFidesLang) {
    return <TableSkeletonLoader rowHeight={36} numRows={15} />;
  }

  return (
    <Flex flex={1} direction="column" overflow="auto">
      <DatamapReportFilterModal
        columnNameMap={{ ...DEFAULT_COLUMN_NAMES, ...columnNameMapOverrides }}
        selectedFilters={selectedFilters}
        isOpen={isFilterModalOpen}
        onClose={onFilterModalClose}
        onFilterChange={(newFilters) => {
          setSavedCustomReportId("");
          setSelectedFilters(newFilters);
        }}
      />
      <ColumnSettingsModal<DatamapReport>
        isOpen={isColumnSettingsOpen}
        onClose={onColumnSettingsClose}
        headerText="Columns"
        columnNameMap={{ ...DEFAULT_COLUMN_NAMES, ...columnNameMapOverrides }}
        prefixColumns={getPrefixColumns(groupBy)}
        tableInstance={tableInstance}
        savedCustomReportId={savedCustomReportId}
        onColumnOrderChange={(newColumnOrder) => {
          setSavedCustomReportId("");
          tableInstance.setColumnOrder(newColumnOrder);
          setColumnOrder(newColumnOrder);
        }}
        onColumnVisibilityChange={(newColumnVisibility) => {
          setSavedCustomReportId("");
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

      <Formik
        initialValues={columnNameMapOverrides}
        onSubmit={handleColumnRenaming}
      >
        <>
          <TableActionBar>
            <GlobalFilterV2
              globalFilter={globalFilter}
              setGlobalFilter={updateGlobalFilter}
              placeholder="System name, Fides key, or ID"
            />
            <Flex alignItems="center" gap={2}>
              {userCanSeeReports && (
                <CustomReportTemplates
                  reportType={ReportType.DATAMAP}
                  savedReportId={savedCustomReportId}
                  tableStateToSave={{
                    groupBy,
                    filters: selectedFilters,
                    columnOrder,
                    columnVisibility,
                  }}
                  currentColumnMap={columnNameMapOverrides}
                  onCustomReportSaved={(customReport, resetForm) =>
                    handleSavedReport(customReport, resetForm)
                  }
                  onSavedReportDeleted={() => {
                    setSavedCustomReportId("");
                  }}
                />
              )}
              <Menu>
                <MenuButton
                  as={Button}
                  icon={<ChevronDownIcon />}
                  iconPosition="end"
                  loading={groupChangeStarted}
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
                data-testid="filter-multiple-systems-btn"
                onClick={onFilterModalOpen}
              >
                Filter
              </Button>
              <Button
                aria-label="Export report"
                data-testid="export-btn"
                onClick={onExportReportOpen}
                icon={<DownloadLightIcon ml="1.5px" />}
              />
              <Menu placement="bottom-end">
                <MenuButton
                  as={Button}
                  icon={<MoreIcon className="rotate-90" />}
                  data-testid="more-menu"
                  aria-label="More options"
                  className="w-6 gap-0"
                />
                <MenuList data-testid="more-menu-list">
                  <MenuItem
                    onClick={onColumnSettingsOpen}
                    data-testid="edit-columns-btn"
                  >
                    Edit columns
                  </MenuItem>
                  <MenuItem
                    onClick={() => setIsRenamingColumns(true)}
                    data-testid="rename-columns-btn"
                  >
                    Rename columns
                  </MenuItem>
                </MenuList>
              </Menu>
              {isRenamingColumns && (
                <RenameColumnsButtons
                  columnNameMapOverrides={columnNameMapOverrides}
                  setColumnNameMapOverrides={setColumnNameMapOverrides}
                  setSavedCustomReportId={setSavedCustomReportId}
                  setIsRenamingColumns={setIsRenamingColumns}
                />
              )}
            </Flex>
          </TableActionBar>
          <Form>
            <FidesTableV2<DatamapReport>
              tableInstance={tableInstance}
              columnExpandStorageKey={
                DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_EXPANSION_STATE
              }
              columnWrapStorageKey={DATAMAP_LOCAL_STORAGE_KEYS.WRAPPING_COLUMNS}
            />
          </Form>
        </>
      </Formik>

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
