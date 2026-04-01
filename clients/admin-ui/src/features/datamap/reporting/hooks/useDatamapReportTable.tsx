import { ColumnsType, Form } from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { CustomReportColumn } from "~/features/common/custom-reports/types";
import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { useHasPermission } from "~/features/common/Restrict";
import { useAntTable } from "~/features/common/table/hooks/useAntTable";
import { useTableState } from "~/features/common/table/hooks/useTableState";
import { getQueryParamsFromArray } from "~/features/common/utils";
import { ExportFormat } from "~/features/datamap/constants";
import {
  useExportMinimalDatamapReportMutation,
  useGetMinimalDatamapReportQuery,
} from "~/features/datamap/datamap.slice";
import {
  selectAllCustomFieldDefinitions,
  useGetAllCustomFieldDefinitionsQuery,
  useGetHealthQuery,
} from "~/features/plus/plus.slice";
import { useGetAllSystemGroupsQuery } from "~/features/system/system-groups.slice";
import {
  DATAMAP_GROUPING,
  Page_DatamapReport_,
  ScopeRegistryEnum,
} from "~/types/api";

import { DATAMAP_LOCAL_STORAGE_KEYS, DEFAULT_COLUMN_NAMES } from "../constants";
import { useDatamapReport } from "../datamap-report-context";
import { getDatamapReportColumns } from "../DatamapReportTableColumns";
import { DatamapReportRow, groupDatamapRows } from "../groupDatamapRows";
import { getColKey, getColumnOrder, getPrefixColumns } from "../utils";

const emptyResponse: Page_DatamapReport_ = {
  items: [],
  total: 0,
  page: 1,
  size: 25,
  pages: 1,
};

export const useDatamapReportTable = () => {
  const [form] = Form.useForm();
  const userCanSeeReports = useHasPermission([
    ScopeRegistryEnum.CUSTOM_REPORT_READ,
  ]);
  const { isLoading: isLoadingHealthCheck } = useGetHealthQuery();
  const { data: systemGroups } = useGetAllSystemGroupsQuery();

  const {
    getDataUseDisplayName,
    getDataCategoryDisplayName,
    getDataSubjectDisplayName,
    isLoading: isLoadingFidesLang,
  } = useTaxonomies();

  // Table state (pagination + search, no URL sync)
  const tableState = useTableState({
    disableUrlState: true,
    pagination: { defaultPageSize: 25 },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;

  // Context: persisted state in localStorage
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
    columnNameMapOverrides,
    setColumnNameMapOverrides,
  } = useDatamapReport();

  // Group change state
  const [groupChangeStarted, setGroupChangeStarted] = useState(false);
  const onGroupChange = useCallback(
    (group: DATAMAP_GROUPING) => {
      setSavedCustomReportId("");
      setGroupBy(group);
      setGroupChangeStarted(true);
      tableState.resetState();
    },
    [setSavedCustomReportId, setGroupBy, tableState],
  );

  // System drawer
  const [selectedSystemId, setSelectedSystemId] = useState<string>();

  // Column renaming
  const [isRenamingColumns, setIsRenamingColumns] = useState(false);

  // Expanded column state (for header menu expand/collapse all) - persisted in localStorage
  const [expandedColumns, setExpandedColumns] = useLocalStorage<
    Record<string, boolean>
  >(DATAMAP_LOCAL_STORAGE_KEYS.COLUMN_EXPANSION_STATE, {});
  const onToggleColumnExpand = useCallback(
    (columnId: string, expanded: boolean) => {
      setExpandedColumns((prev) => ({ ...prev, [columnId]: expanded }));
    },
    [setExpandedColumns],
  );

  // Build query
  const reportQuery = useMemo(
    () => ({
      pageIndex,
      pageSize,
      groupBy,
      search: searchQuery || "",
      dataUses: getQueryParamsFromArray(selectedFilters.dataUses, "data_uses"),
      dataSubjects: getQueryParamsFromArray(
        selectedFilters.dataSubjects,
        "data_subjects",
      ),
      dataCategories: getQueryParamsFromArray(
        selectedFilters.dataCategories,
        "data_categories",
      ),
    }),
    [pageIndex, pageSize, groupBy, searchQuery, selectedFilters],
  );

  // Fetch data
  const {
    data: datamapReport,
    isLoading: isReportLoading,
    isFetching: isReportFetching,
    error: reportError,
  } = useGetMinimalDatamapReportQuery(reportQuery);

  // Export mutation
  const [exportMinimalDatamapReport, { isLoading: isExportingReport }] =
    useExportMinimalDatamapReportMutation();

  // Process data
  const { dataSource, totalRows } = useMemo(() => {
    const report = datamapReport || emptyResponse;
    const { items } = report;
    return {
      totalRows: report.total ?? 0,
      dataSource: groupDatamapRows(items, groupBy),
    };
  }, [datamapReport, groupBy]);

  // Reset groupChangeStarted once new data arrives after a group change
  useEffect(() => {
    if (groupChangeStarted && datamapReport) {
      setGroupChangeStarted(false);
    }
  }, [datamapReport, groupChangeStarted]);

  // Custom fields
  useGetAllCustomFieldDefinitionsQuery();
  const customFields = useAppSelector(selectAllCustomFieldDefinitions);

  // Column name map
  const columnNameMap: Record<string, string> = useMemo(
    () => ({
      ...(DEFAULT_COLUMN_NAMES as Record<string, string>),
      ...columnNameMapOverrides,
    }),
    [columnNameMapOverrides],
  );

  // Ant table integration
  const { tableProps } = useAntTable<DatamapReportRow>(tableState, {
    dataSource,
    totalRows,
    isLoading: isReportLoading || isLoadingHealthCheck || isLoadingFidesLang,
    isFetching: isReportFetching,
    getRowKey: (record) => record.rowKey,
  });

  // Column definitions
  const columns: ColumnsType<DatamapReportRow> = useMemo(() => {
    if (!datamapReport) {
      return [];
    }
    return getDatamapReportColumns({
      onOpenSystemDrawer: (row) => setSelectedSystemId(row.fides_key),
      getDataUseDisplayName,
      getDataCategoryDisplayName,
      getDataSubjectDisplayName,
      datamapReport,
      customFields,
      systemGroups,
      isRenaming: isRenamingColumns,
      groupBy,
      columnNameMap,
      form,
      expandedColumns,
      onToggleColumnExpand,
    });
  }, [
    datamapReport,
    getDataUseDisplayName,
    getDataCategoryDisplayName,
    getDataSubjectDisplayName,
    customFields,
    systemGroups,
    isRenamingColumns,
    form,
    groupBy,
    columnNameMap,
    expandedColumns,
    onToggleColumnExpand,
  ]);

  // Apply column ordering and visibility
  const visibleColumns = useMemo(() => {
    if (!columns.length) {
      return columns;
    }

    // Mark hidden columns via Ant Design's `hidden` property
    const withVisibility = columns.map((col) => {
      const key = getColKey(col);
      if (!key) {
        return col;
      }
      return columnVisibility[key] === false ? { ...col, hidden: true } : col;
    });

    // Compute effective column order synchronously to avoid stale ordering
    // when groupBy changes before the useEffect below persists the new order.
    const allColumnKeys = withVisibility.map(getColKey);
    const effectiveOrder = groupBy
      ? getColumnOrder(
          groupBy,
          columnOrder.length > 0 ? columnOrder : allColumnKeys,
        )
      : columnOrder;

    if (effectiveOrder.length > 0) {
      const orderMap = new Map(effectiveOrder.map((id, idx) => [id, idx]));
      return [...withVisibility].sort((a, b) => {
        const aIdx = orderMap.get(getColKey(a)) ?? Infinity;
        const bIdx = orderMap.get(getColKey(b)) ?? Infinity;
        return aIdx - bIdx;
      });
    }

    return withVisibility;
  }, [columns, columnVisibility, columnOrder, groupBy]);

  // Update column order when groupBy or data changes
  useEffect(() => {
    if (groupBy && datamapReport) {
      const allColumnKeys = columns.map(getColKey);
      if (columnOrder.length === 0) {
        setColumnOrder(getColumnOrder(groupBy, allColumnKeys));
      } else {
        setColumnOrder(getColumnOrder(groupBy, columnOrder));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupBy, datamapReport]);

  // Column renaming handler
  const handleColumnRenaming = useCallback(
    (values: Record<string, string>) => {
      setSavedCustomReportId("");
      setColumnNameMapOverrides(values);
      setIsRenamingColumns(false);
    },
    [setSavedCustomReportId, setColumnNameMapOverrides],
  );

  // Export handler
  const onExport = useCallback(
    (downloadType: ExportFormat) => {
      const columnMap: Record<string, CustomReportColumn> = {};
      Object.entries(columnVisibility).forEach(([key, isVisible]) => {
        columnMap[key] = { enabled: isVisible };
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
      return exportMinimalDatamapReport({
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
      });
    },
    [
      columnVisibility,
      columnNameMapOverrides,
      exportMinimalDatamapReport,
      reportQuery,
      savedCustomReportId,
      groupBy,
      selectedFilters,
      columnOrder,
    ],
  );

  // Column settings helpers
  const columnDescriptors = useMemo(() => {
    const prefixCols = getPrefixColumns(groupBy);
    return columns
      .filter((c) => {
        const key = getColKey(c);
        return key && !prefixCols.includes(key);
      })
      .map((c) => {
        const key = getColKey(c);
        return {
          id: key,
          isVisible: columnVisibility[key] !== false,
        };
      })
      .sort((a, b) => {
        if (columnOrder.length === 0) {
          return 0;
        }
        const aIdx = columnOrder.indexOf(a.id);
        const bIdx = columnOrder.indexOf(b.id);
        if (aIdx === -1 && bIdx === -1) {
          return 0;
        }
        if (aIdx === -1) {
          return 1;
        }
        if (bIdx === -1) {
          return -1;
        }
        return aIdx - bIdx;
      });
  }, [columns, groupBy, columnVisibility, columnOrder]);

  return {
    // Form
    form,

    // Table
    tableProps,
    columns: visibleColumns,

    // Data
    reportError,

    // Search
    searchQuery: searchQuery || "",
    updateSearch,

    // GroupBy
    groupBy,
    onGroupChange,
    groupChangeStarted,

    // Filters
    selectedFilters,
    setSelectedFilters,

    // Column settings
    columnOrder,
    setColumnOrder,
    columnVisibility,
    setColumnVisibility,
    columnNameMap,
    columnNameMapOverrides,
    setColumnNameMapOverrides,
    columnDescriptors,

    // Column renaming
    isRenamingColumns,
    setIsRenamingColumns,
    handleColumnRenaming,

    // Export
    onExport,
    isExportingReport,

    // System drawer
    selectedSystemId,
    setSelectedSystemId,

    // Custom reports
    savedCustomReportId,
    setSavedCustomReportId,
    userCanSeeReports,

    // Report reset/apply
    setGroupBy,
  };
};
