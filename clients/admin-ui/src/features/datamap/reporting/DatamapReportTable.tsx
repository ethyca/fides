import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  Button,
  CheckOutlined,
  Dropdown,
  Flex,
  Form,
  Icons,
  Table,
  useChakraDisclosure as useDisclosure,
  useMessage,
} from "fidesui";
import { useCallback, useEffect } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { ColumnSettingsModal } from "~/features/common/table/column-settings/ColumnSettingsModal";
import { ExportFormat } from "~/features/datamap/constants";
import DatamapDrawer from "~/features/datamap/datamap-drawer/DatamapDrawer";
import ReportExportModal from "~/features/datamap/modals/ReportExportModal";
import { DatamapReportFilterModal } from "~/features/datamap/reporting/DatamapReportFilterModal";
import {
  CustomReportResponse,
  DATAMAP_GROUPING,
  ReportType,
} from "~/types/api";

import { CustomReportTemplates } from "../../common/custom-reports/CustomReportTemplates";
import { COLUMN_IDS } from "./constants";
import {
  DEFAULT_COLUMN_FILTERS,
  DEFAULT_COLUMN_VISIBILITY,
} from "./datamap-report-context";
import { useDatamapReportTable } from "./hooks/useDatamapReportTable";
import { RenameColumnsButtons } from "./RenameColumnsButtons";
import { getPrefixColumns } from "./utils";

const checkIcon = (isSelected: boolean) => (
  <CheckOutlined style={{ visibility: isSelected ? "visible" : "hidden" }} />
);

export const DatamapReportTable = ({
  onError,
}: {
  onError: (error: FetchBaseQueryError | SerializedError) => void;
}) => {
  const {
    form,
    tableProps,
    columns,
    reportError,
    searchQuery,
    updateSearch,
    groupBy,
    onGroupChange,
    groupChangeStarted,
    selectedFilters,
    setSelectedFilters,
    columnOrder,
    setColumnOrder,
    columnVisibility,
    setColumnVisibility,
    columnNameMap,
    columnNameMapOverrides,
    setColumnNameMapOverrides,
    columnDescriptors,
    isRenamingColumns,
    setIsRenamingColumns,
    handleColumnRenaming,
    onExport,
    isExportingReport,
    selectedSystemId,
    setSelectedSystemId,
    savedCustomReportId,
    setSavedCustomReportId,
    userCanSeeReports,
    setGroupBy,
  } = useDatamapReportTable();

  const message = useMessage();

  const {
    isOpen: isFilterModalOpen,
    onClose: onFilterModalClose,
    onOpen: onFilterModalOpen,
  } = useDisclosure();

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

  // Report error handling
  useEffect(() => {
    if (reportError) {
      onError(reportError);
    }
  }, [reportError, onError]);

  // Sync Ant Form with external columnNameMapOverrides changes
  useEffect(() => {
    form.setFieldsValue(columnNameMapOverrides);
  }, [form, columnNameMapOverrides]);

  const handleExport = useCallback(
    (downloadType: ExportFormat) => {
      onExport(downloadType).then((result) => {
        if (!("error" in result)) {
          onExportReportClose();
        }
      });
    },
    [onExport, onExportReportClose],
  );

  // System group option name for dropdown
  const getSystemGroupOptionName = useCallback(() => {
    const customSystemGroupName =
      columnNameMapOverrides[COLUMN_IDS.SYSTEM_GROUP];
    if (customSystemGroupName) {
      return customSystemGroupName;
    }
    return "System group";
  }, [columnNameMapOverrides]);

  const getMenuDisplayValue = useCallback(() => {
    switch (groupBy) {
      case DATAMAP_GROUPING.SYSTEM_DATA_USE:
        return "system";
      case DATAMAP_GROUPING.DATA_USE_SYSTEM:
        return "data use";
      case DATAMAP_GROUPING.SYSTEM_GROUP: {
        const systemGroupName = getSystemGroupOptionName();
        return (
          systemGroupName.charAt(0).toLowerCase() + systemGroupName.slice(1)
        );
      }
      default:
        return "system";
    }
  }, [groupBy, getSystemGroupOptionName]);

  const handleSavedReport = useCallback(
    (savedReport: CustomReportResponse | null) => {
      if (!savedReport && !savedCustomReportId) {
        return;
      }
      if (!savedReport) {
        try {
          setSavedCustomReportId("");
          setColumnVisibility(DEFAULT_COLUMN_VISIBILITY);
          setColumnOrder([]);
          setGroupBy(DATAMAP_GROUPING.SYSTEM_DATA_USE);
          setSelectedFilters(DEFAULT_COLUMN_FILTERS);
          setColumnNameMapOverrides({});
          form.resetFields();
        } catch (error: unknown) {
          message.error("There was a problem resetting the report.");
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
            setGroupBy(savedGroupBy);
          }
          if (savedFilters) {
            setSelectedFilters(savedFilters);
          }
          if (savedColumnOrder) {
            setColumnOrder(savedColumnOrder);
          }
          if (Object.keys(savedColumnVisibility).length > 0) {
            setColumnVisibility(savedColumnVisibility);
          }
        }
        if (savedReport.config?.column_map) {
          const columnNameOverrides: Record<string, string> = {};
          Object.entries(savedReport.config.column_map ?? {}).forEach(
            ([key, value]) => {
              if (value.label) {
                columnNameOverrides[key] = value.label;
              }
            },
          );
          setColumnNameMapOverrides(columnNameOverrides);
          form.setFieldsValue(columnNameOverrides);
        }
        setSavedCustomReportId(savedReport.id);
        message.success("Report applied successfully.");
      } catch (error: unknown) {
        message.error("There was a problem applying report.");
      }
    },
    [
      savedCustomReportId,
      setSavedCustomReportId,
      setColumnVisibility,
      setColumnOrder,
      setGroupBy,
      setSelectedFilters,
      setColumnNameMapOverrides,
      form,
      message,
    ],
  );

  return (
    <>
      <Form
        form={form}
        initialValues={columnNameMapOverrides}
        onFinish={handleColumnRenaming}
      >
        <Flex className="sticky -top-6 z-[100] bg-white py-4">
          <Flex className="flex-1 items-center justify-between py-2">
            <DebouncedSearchInput
              value={searchQuery}
              onChange={updateSearch}
              placeholder="System name, Fides key, or ID"
            />
            <Flex className="items-center gap-2">
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
                  onCustomReportSaved={handleSavedReport}
                  onSavedReportDeleted={() => {
                    setSavedCustomReportId("");
                  }}
                />
              )}
              <Dropdown
                menu={{
                  items: [
                    {
                      key: DATAMAP_GROUPING.SYSTEM_DATA_USE,
                      label: "System",
                      icon: checkIcon(
                        DATAMAP_GROUPING.SYSTEM_DATA_USE === groupBy,
                      ),
                      onClick: () =>
                        onGroupChange(DATAMAP_GROUPING.SYSTEM_DATA_USE),
                    },
                    {
                      key: DATAMAP_GROUPING.DATA_USE_SYSTEM,
                      label: "Data use",
                      icon: checkIcon(
                        DATAMAP_GROUPING.DATA_USE_SYSTEM === groupBy,
                      ),
                      onClick: () =>
                        onGroupChange(DATAMAP_GROUPING.DATA_USE_SYSTEM),
                    },
                    {
                      key: DATAMAP_GROUPING.SYSTEM_GROUP,
                      label: getSystemGroupOptionName(),
                      icon: checkIcon(
                        DATAMAP_GROUPING.SYSTEM_GROUP === groupBy,
                      ),
                      onClick: () =>
                        onGroupChange(DATAMAP_GROUPING.SYSTEM_GROUP),
                    },
                  ],
                }}
                overlayClassName="group-by-menu-list"
              >
                <Button
                  icon={<Icons.ChevronDown size={14} />}
                  iconPosition="end"
                  loading={groupChangeStarted}
                  data-testid="group-by-menu"
                >
                  Group by {getMenuDisplayValue()}
                </Button>
              </Dropdown>
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
                icon={<Icons.Download />}
              />
              <Dropdown
                menu={{
                  items: [
                    {
                      key: "edit-columns",
                      label: (
                        <span data-testid="edit-columns-btn">Edit columns</span>
                      ),
                      onClick: onColumnSettingsOpen,
                    },
                    {
                      key: "rename-columns",
                      label: "Rename columns",
                      onClick: () => setIsRenamingColumns(true),
                    },
                  ],
                }}
                placement="bottomRight"
                overlayClassName="more-menu-list"
              >
                <Button
                  icon={<Icons.OverflowMenuVertical />}
                  data-testid="more-menu"
                  aria-label="More options"
                  className="w-6 gap-0"
                />
              </Dropdown>
              {isRenamingColumns && (
                <RenameColumnsButtons
                  columnNameMapOverrides={columnNameMapOverrides}
                  setColumnNameMapOverrides={setColumnNameMapOverrides}
                  setSavedCustomReportId={setSavedCustomReportId}
                  setIsRenamingColumns={setIsRenamingColumns}
                />
              )}
            </Flex>
          </Flex>
        </Flex>

        <Table
          key={groupBy}
          {...tableProps}
          columns={columns}
          data-testid="fidesTable"
        />
      </Form>

      <DatamapReportFilterModal
        columnNameMap={columnNameMap}
        selectedFilters={selectedFilters}
        isOpen={isFilterModalOpen}
        onClose={onFilterModalClose}
        onFilterChange={(newFilters) => {
          setSavedCustomReportId("");
          setSelectedFilters(newFilters);
        }}
      />
      <ColumnSettingsModal
        isOpen={isColumnSettingsOpen}
        onClose={onColumnSettingsClose}
        headerText="Columns"
        columnNameMap={columnNameMap}
        prefixColumns={getPrefixColumns(groupBy)}
        columns={columnDescriptors}
        savedCustomReportId={savedCustomReportId}
        onColumnOrderChange={(newColumnOrder) => {
          setSavedCustomReportId("");
          setColumnOrder(newColumnOrder);
        }}
        onColumnVisibilityChange={(newColumnVisibility) => {
          setSavedCustomReportId("");
          setColumnVisibility(newColumnVisibility);
        }}
      />
      <ReportExportModal
        isOpen={isExportReportOpen}
        onClose={onExportReportClose}
        onConfirm={handleExport}
        isLoading={isExportingReport}
      />
      <DatamapDrawer
        selectedSystemId={selectedSystemId}
        resetSelectedSystemId={() => setSelectedSystemId(undefined)}
      />
    </>
  );
};
