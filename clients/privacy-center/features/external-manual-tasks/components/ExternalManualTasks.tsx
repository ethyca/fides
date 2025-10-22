/**
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/ManualTasks.tsx
 *
 * Key differences for external users:
 * - No "Assigned to" column (always filtered to current user)
 * - No user navigation/routing
 * - Simplified UI for external users
 * - Uses external data-testids for Cypress testing
 * - Uses external Redux hooks and slice
 *
 * IMPORTANT: When updating admin-ui ManualTasks.tsx, review this component for sync!
 */

import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntFlex as Flex,
  AntTable as Table,
  AntTag as Tag,
  AntTypography as Typography,
  CUSTOM_TAG_COLOR,
  Icons,
} from "fidesui";
import { useMemo, useState } from "react";

import {
  ManualFieldListItem,
  ManualFieldRequestType,
  ManualFieldStatus,
  ManualFieldSystem,
  useGetExternalTasksQuery,
} from "../external-manual-tasks.slice";
import { ExternalTaskActionButtons } from "./ExternalTaskActionButtons";
import useDownloadExternalTasksReport from "./hooks/useDownloadExternalTasksReport";

// Map task status to tag colors and labels - aligned with RequestStatusBadge colors
const statusMap: Record<
  ManualFieldStatus,
  { color: CUSTOM_TAG_COLOR; label: string }
> = {
  [ManualFieldStatus.NEW]: { color: CUSTOM_TAG_COLOR.INFO, label: "New" },
  [ManualFieldStatus.COMPLETED]: {
    color: CUSTOM_TAG_COLOR.SUCCESS,
    label: "Completed",
  },
  [ManualFieldStatus.SKIPPED]: {
    color: CUSTOM_TAG_COLOR.MARBLE,
    label: "Skipped",
  },
};

// Extract column definitions for external users
const getExternalColumns = (
  systemFilters: { text: string; value: string }[],
): ColumnsType<ManualFieldListItem> => [
  {
    title: "Task name",
    dataIndex: "name",
    key: "name",
    width: 350,
    render: (name) => (
      <Typography.Text
        ellipsis={{ tooltip: name }}
        data-testid="task-details-name"
        className="!max-w-[350px]"
      >
        {name}
      </Typography.Text>
    ),
  },
  {
    title: "Status",
    dataIndex: "status",
    key: "status",
    width: 120,
    render: (status: ManualFieldStatus) => (
      <Tag
        color={statusMap[status].color}
        data-testid="external-task-status-tag"
      >
        {statusMap[status].label}
      </Tag>
    ),
    filters: [
      { text: "New", value: ManualFieldStatus.NEW },
      { text: "Completed", value: ManualFieldStatus.COMPLETED },
      { text: "Skipped", value: ManualFieldStatus.SKIPPED },
    ],
    filterMultiple: false,
  },
  {
    title: "System",
    dataIndex: ["system", "name"],
    key: "system_name",
    width: 200,
    filters: systemFilters,
    filterMultiple: false,
    render: (systemName: string) => (
      <Typography.Text
        ellipsis={{ tooltip: systemName }}
        className="!max-w-[200px]"
      >
        {systemName}
      </Typography.Text>
    ),
  },
  {
    title: "Type",
    dataIndex: "request_type",
    key: "request_type",
    width: 150,
    render: (type: ManualFieldRequestType) => {
      // Capitalize the first letter for display
      const capitalizedType = type.charAt(0).toUpperCase() + type.slice(1);
      return <Typography.Text>{capitalizedType}</Typography.Text>;
    },
    filters: [
      { text: "Access", value: ManualFieldRequestType.ACCESS },
      { text: "Erasure", value: ManualFieldRequestType.ERASURE },
    ],
    filterMultiple: false,
  },
  {
    title: "Days left",
    dataIndex: ["privacy_request", "days_left"],
    key: "days_left",
    width: 120,
    render: (daysLeft: number | null) => {
      if (!daysLeft) {
        return <Typography.Text>-</Typography.Text>;
      }

      // Simple days left display for external users
      let color = CUSTOM_TAG_COLOR.SUCCESS;
      if (daysLeft <= 5) {
        color = CUSTOM_TAG_COLOR.ERROR;
      } else if (daysLeft <= 10) {
        color = CUSTOM_TAG_COLOR.WARNING;
      }
      return <Tag color={color}>{daysLeft} days</Tag>;
    },
  },
  {
    title: "Subject identity",
    dataIndex: ["privacy_request", "subject_identities"],
    key: "subject_identities",
    width: 200,
    render: (subjectIdentities: Record<string, string>) => {
      if (!subjectIdentities) {
        return <Typography.Text>-</Typography.Text>;
      }

      // Display email or phone_number if available
      const identity =
        subjectIdentities.email || subjectIdentities.phone_number || "";
      return (
        <Typography.Text ellipsis={{ tooltip: identity }}>
          {identity}
        </Typography.Text>
      );
    },
  },
  {
    title: "Actions",
    key: "actions",
    width: 160,
    render: (_, task: ManualFieldListItem) => (
      <ExternalTaskActionButtons task={task} />
    ),
  },
];

export const ExternalManualTasks = () => {
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{
    status?: string;
    systemName?: string;
    requestType?: string;
  }>({});

  // Use external tasks query
  const { data, isLoading, isFetching, error } = useGetExternalTasksQuery({
    page: pageIndex,
    size: pageSize,
    // Pass filter parameters to API
    status: filters.status as ManualFieldStatus,
    system_name: filters.systemName,
    request_type: filters.requestType as ManualFieldRequestType,
  });

  const { downloadReport, isDownloadingReport } =
    useDownloadExternalTasksReport();

  const handleExport = async () => {
    await downloadReport({
      status: filters.status as ManualFieldStatus,
      system_name: filters.systemName,
      request_type: filters.requestType as ManualFieldRequestType,
    });
  };

  const {
    items: tasks,
    total: totalRows,
    filter_options: filterOptions,
  } = useMemo(
    () =>
      data || {
        items: [],
        total: 0,
        pages: 0,
        filter_options: { assigned_users: [], systems: [] },
      },
    [data],
  );

  // Create filter options from API response
  const systemFilters = useMemo(
    () =>
      filterOptions?.systems?.map((system: ManualFieldSystem) => ({
        text: system.name,
        value: system.name,
      })) || [],
    [filterOptions?.systems],
  );

  // Handle table filter changes
  const handleTableChange = (pagination: any, tableFilters: any) => {
    // Convert Ant Design filters to our filter state
    const newFilters: typeof filters = {};

    if (tableFilters.status) {
      [newFilters.status] = tableFilters.status as string[];
    }
    if (tableFilters.system_name) {
      [newFilters.systemName] = tableFilters.system_name as string[];
    }
    if (tableFilters.request_type) {
      [newFilters.requestType] = tableFilters.request_type as string[];
    }

    setFilters(newFilters);
    setPageIndex(1); // Reset to first page when filtering
  };

  // Handle pagination changes
  const handlePaginationChange = (page: number, size?: number) => {
    setPageIndex(page);
    if (size && size !== pageSize) {
      setPageSize(size);
      setPageIndex(1); // Reset to first page when changing page size
    }
  };

  const columns = useMemo(
    () => getExternalColumns(systemFilters),
    [systemFilters],
  );

  if (error) {
    return (
      <div
        className="p-4 text-center text-red-600"
        data-testid="tasks-error-message"
      >
        Failed to load tasks. Please try again later.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-8 text-center" data-testid="external-tasks-loading">
        <Typography.Text>Loading tasks...</Typography.Text>
      </div>
    );
  }

  const showSpinner = isLoading || isFetching;

  return (
    <div data-testid="external-manual-tasks">
      {/* Export Button */}
      <Flex justify="flex-end" style={{ marginBottom: "16px" }}>
        <Button
          aria-label="Export external tasks as CSV"
          data-testid="export-external-tasks-btn"
          icon={<Icons.Download />}
          loading={isDownloadingReport}
          onClick={handleExport}
        >
          Download tasks
        </Button>
      </Flex>

      {/* Tasks Table */}
      <Table
        columns={columns}
        dataSource={tasks}
        rowKey={(record) =>
          `${record.privacy_request.id}-${record.manual_field_id}`
        }
        pagination={{
          current: pageIndex,
          pageSize,
          pageSizeOptions: [25, 50, 100],
          total: totalRows || 0,
          showTotal: (total, range) =>
            `${range[0]}-${range[1]} of ${total} items`,
          onChange: handlePaginationChange,
        }}
        onChange={handleTableChange}
        locale={{
          emptyText: (
            <div data-testid="external-empty-state">
              No manual tasks available.
            </div>
          ),
        }}
        loading={showSpinner}
        data-testid="external-tasks-table"
        scroll={{ x: 1200 }} // Make table scrollable on mobile
      />
    </div>
  );
};
