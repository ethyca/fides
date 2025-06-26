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
  AntColumnsType as ColumnsType,
  AntInput as Input,
  AntTable as Table,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";
import { useMemo, useState } from "react";

import { useGetExternalTasksQuery } from "../external-manual-tasks.slice";
// import { useExternalAppSelector } from "../hooks";
import { ManualTask, RequestType, System, TaskStatus } from "../types";
// import { ExternalTaskActionButtons } from "./ExternalTaskActionButtons";

// Map task status to tag colors and labels - aligned with RequestStatusBadge colors
const statusMap: Record<TaskStatus, { color: string; label: string }> = {
  new: { color: "info", label: "New" },
  completed: { color: "success", label: "Completed" },
  skipped: { color: "marble", label: "Skipped" },
};

// Page sizes for external users (simplified)
const PAGE_SIZES = ["10", "25", "50"];

// Extract column definitions for external users
const getExternalColumns = (
  systemFilters: { text: string; value: string }[],
): ColumnsType<ManualTask> => [
  {
    title: "Task name",
    dataIndex: "name",
    key: "name",
    width: 350,
    render: (name) => (
      <Typography.Text
        ellipsis={{ tooltip: name }}
        data-testid="task-details-name"
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
    render: (status: TaskStatus) => (
      <Tag
        color={statusMap[status].color}
        data-testid="external-task-status-tag"
      >
        {statusMap[status].label}
      </Tag>
    ),
    filters: [
      { text: "New", value: "new" },
      { text: "Completed", value: "completed" },
      { text: "Skipped", value: "skipped" },
    ],
  },
  {
    title: "System",
    dataIndex: ["system", "name"],
    key: "system_name",
    width: 200,
    filters: systemFilters,
  },
  {
    title: "Type",
    dataIndex: ["privacy_request", "request_type"],
    key: "request_type",
    width: 150,
    render: (type: RequestType) => {
      // Capitalize the first letter for display
      const capitalizedType = type.charAt(0).toUpperCase() + type.slice(1);
      return <Typography.Text>{capitalizedType}</Typography.Text>;
    },
    filters: [
      { text: "Access", value: "access" },
      { text: "Erasure", value: "erasure" },
    ],
  },
  {
    title: "Days left",
    dataIndex: ["privacy_request", "days_left"],
    key: "days_left",
    width: 120,
    render: (daysLeft: number) => {
      // Simple days left display for external users
      let color = "green";
      if (daysLeft <= 5) {
        color = "red";
      } else if (daysLeft <= 10) {
        color = "orange";
      }
      return <Tag color={color}>{daysLeft} days</Tag>;
    },
  },
  {
    title: "Subject identity",
    dataIndex: ["privacy_request", "subject_identity"],
    key: "subject_identity",
    width: 200,
    render: (subjectIdentity) => {
      if (!subjectIdentity) {
        return <Typography.Text>-</Typography.Text>;
      }

      // Display email or phone number
      const identity =
        subjectIdentity.email?.value ||
        subjectIdentity.phone_number?.value ||
        "";
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
    render: () => (
      <div data-testid="task-actions-placeholder">
        {/* Placeholder for actions - will implement next */}
        Actions
      </div>
    ),
  },
];

export const ExternalManualTasks = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{
    status?: string[];
    systemName?: string[];
    requestType?: string[];
  }>({});

  // Use external tasks query
  const { data, isLoading, isFetching, error } = useGetExternalTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchTerm,
    // Pass filter parameters to API
    status: filters.status?.[0] as TaskStatus,
    systemName: filters.systemName?.[0],
    requestType: filters.requestType?.[0] as RequestType,
  });

  const {
    items: tasks,
    total: totalRows,
    filterOptions,
  } = useMemo(
    () =>
      data || {
        items: [],
        total: 0,
        pages: 0,
        filterOptions: { assigned_users: [], systems: [] },
      },
    [data],
  );

  // Create filter options from API response
  const systemFilters = useMemo(
    () =>
      filterOptions?.systems?.map((system: System) => ({
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
      newFilters.status = tableFilters.status;
    }
    if (tableFilters.system_name) {
      newFilters.systemName = tableFilters.system_name;
    }
    if (tableFilters.request_type) {
      newFilters.requestType = tableFilters.request_type;
    }

    setFilters(newFilters);
    setPageIndex(1); // Reset to first page when filters change
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setPageIndex(1); // Reset to first page when searching
  };

  const columns = useMemo(
    () => getExternalColumns(systemFilters),
    [systemFilters],
  );

  const showSpinner = (isLoading || isFetching) && pageIndex === 1;

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Typography.Text type="danger" data-testid="tasks-error-message">
            Failed to load tasks. Please try again.
          </Typography.Text>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="external-tasks-container">
      <Input
        placeholder="Search tasks by name or description..."
        value={searchTerm}
        onChange={(e) => handleSearchChange(e.target.value)}
        className="max-w-sm"
        data-testid="external-tasks-search"
      />

      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="task_id"
        data-testid="external-tasks-table"
        pagination={{
          current: pageIndex,
          pageSize,
          total: totalRows || 0,
          showSizeChanger: true,
          pageSizeOptions: PAGE_SIZES,
          showTotal: (total, range) =>
            `${range[0]}-${range[1]} of ${total} items`,
          onChange: (page, size) => {
            setPageIndex(page);
            if (size !== pageSize) {
              setPageSize(size);
              setPageIndex(1); // Reset to first page when changing page size
            }
          },
        }}
        onChange={handleTableChange}
        locale={{
          emptyText: searchTerm ? (
            <div data-testid="external-empty-state">
              No tasks match your search
            </div>
          ) : (
            <div data-testid="external-empty-state">
              No manual tasks available
            </div>
          ),
        }}
        loading={showSpinner}
      />
    </div>
  );
};
