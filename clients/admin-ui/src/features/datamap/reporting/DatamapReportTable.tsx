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
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
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
} from "~/types/api";

import { CustomReportTemplates } from "../../common/custom-reports/CustomReportTemplates";
import { DatamapReportWithCustomFields as DatamapReport } from "./datamap-report";
import { useDatamapReport } from "./datamap-report-context";
import { getDatamapReportColumns } from "./DatamapReportTableColumns";
import { getGrouping, getPrefixColumns } from "./utils";

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
      report_id: savedCustomReportId,
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

  const handleSavedReport = (savedReport: CustomReportResponse | null) => {
    if (!savedReport) {
      setSavedCustomReportId("");
      return;
    }
    try {
      if (savedReport.config?.table_state) {
        const {
          groupBy: savedGroupBy,
          filters: savedFilters,
          columnOrder: savedColumnOrder,
          columnVisibility: savedColumnVisibility,
        } = savedReport.config.table_state;
        if (savedGroupBy) {
          setGroupBy(savedGroupBy);
          tableInstance.setGrouping(getGrouping(savedGroupBy));
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
        headerText="Data map settings"
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
      <TableActionBar>
        <GlobalFilterV2
          globalFilter={globalFilter}
          setGlobalFilter={updateGlobalFilter}
          placeholder="System name, Fides key, or ID"
        />
        <Flex alignItems="center" gap={2}>
          <CustomReportTemplates
            reportType={ReportType.DATAMAP}
            savedReportId={savedCustomReportId}
            tableStateToSave={{
              groupBy,
              filters: selectedFilters,
              columnOrder,
              columnVisibility,
            }}
            onCustomReportSaved={handleSavedReport}
            onSavedReportDeleted={() => {
              setSavedCustomReportId("");
            }}
          />
          <Menu>
            <MenuButton
              as={Button}
              size="small"
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
            size="small"
            onClick={onFilterModalOpen}
          >
            Filter
          </Button>
          <Button
            aria-label="Export report"
            data-testid="export-btn"
            size="small"
            onClick={onExportReportOpen}
            icon={<DownloadLightIcon />}
          />
          <Menu placement="bottom-end">
            <MenuButton
              as={Button}
              size="small"
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
            </MenuList>
          </Menu>
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
