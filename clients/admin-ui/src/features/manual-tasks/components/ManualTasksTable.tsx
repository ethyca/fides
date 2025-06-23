import type { ColumnsType } from "antd/es/table";
import {
  AntTable as Table,
  AntTag as Tag,
  AntTypography as Typography,
  SelectInline,
} from "fidesui";
import { useMemo, useState } from "react";

import DaysLeftTag from "~/features/common/DaysLeftTag";
import FidesSpinner from "~/features/common/FidesSpinner";
import { PAGE_SIZES } from "~/features/common/table/v2/PaginationBar";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

import { useGetTasksQuery } from "../manual-tasks.slice";
import {
  AssignedUser,
  ManualTask,
  RequestType,
  System,
  TaskStatus,
} from "../mocked/types";
import { ActionButtons } from "./ActionButtons";

// Map task status to tag colors and labels - aligned with RequestStatusBadge colors
const statusMap: Record<TaskStatus, { color: string; label: string }> = {
  new: { color: "info", label: "New" },
  completed: { color: "success", label: "Completed" },
  skipped: { color: "marble", label: "Skipped" },
};

interface Props {
  searchTerm?: string;
}

// Extract column definitions to a separate function for better readability
const getColumns = (
  systemFilters: { text: string; value: string }[],
  userFilters: { text: string; value: string }[],
): ColumnsType<ManualTask> => [
  {
    title: "Task name",
    dataIndex: "name",
    key: "name",
    width: 300,
    render: (name) => (
      <Typography.Text ellipsis={{ tooltip: name }}>{name}</Typography.Text>
    ),
  },
  {
    title: "Status",
    dataIndex: "status",
    key: "status",
    width: 120,
    render: (status: TaskStatus) => (
      <Tag color={statusMap[status].color} data-testid="manual-task-status-tag">
        {statusMap[status].label}
      </Tag>
    ),
    filters: [
      { text: "New", value: "new" },
      { text: "Completed", value: "completed" },
      { text: "Skipped", value: "skipped" },
    ],
    onFilter: (value, record) => record.status === value,
  },
  {
    title: "System",
    dataIndex: ["system", "name"],
    key: "system_name",
    width: 210,
    filters: systemFilters,
    onFilter: (value, record) => record.system.name === value,
  },
  {
    title: "Type",
    dataIndex: ["privacy_request", "request_type"],
    key: "request_type",
    width: 150,
    render: (type: RequestType) => {
      // Map the lowercase string to the ActionType enum value
      const actionType =
        type === "access" ? ActionType.ACCESS : ActionType.ERASURE;
      const displayName = SubjectRequestActionTypeMap.get(actionType) || type;
      return <Typography.Text>{displayName}</Typography.Text>;
    },
    filters: [
      { text: "Access", value: "access" },
      { text: "Erasure", value: "erasure" },
    ],
    onFilter: (value, record) => record.privacy_request.request_type === value,
  },
  {
    title: "Assigned to",
    dataIndex: "assigned_users",
    key: "assigned_users",
    width: 380,
    render: (assignedUsers: AssignedUser[]) => {
      const userOptions = assignedUsers.map((user) => ({
        label:
          `${user.first_name || ""} ${user.last_name || ""}`.trim() ||
          user.email_address ||
          "Unknown User",
        value: user.id,
      }));

      const currentAssignedUserIds = assignedUsers.map((user) => user.id);

      return (
        <SelectInline
          value={currentAssignedUserIds}
          options={userOptions}
          readonly
        />
      );
    },
    filters: userFilters,
    onFilter: (value, record) =>
      record.assigned_users.some((user) => user.id === value),
  },
  {
    title: "Days left",
    dataIndex: ["privacy_request", "days_left"],
    key: "days_left",
    width: 140,
    render: (daysLeft: number) => (
      <DaysLeftTag
        daysLeft={daysLeft}
        includeText={false}
        status={PrivacyRequestStatus.PENDING}
      />
    ),
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

      // Display email or phone number, similar to privacy requests
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
    width: 120,
    render: (_, record) => <ActionButtons task={record} />,
  },
];

export const ManualTasksTable = ({ searchTerm }: Props) => {
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const { data, isLoading, isFetching } = useGetTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchTerm,
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

  const userFilters = useMemo(
    () =>
      filterOptions?.assigned_users?.map((user: AssignedUser) => ({
        text: `${user.first_name} ${user.last_name}`,
        value: user.id,
      })) || [],
    [filterOptions?.assigned_users],
  );

  const columns = useMemo(
    () => getColumns(systemFilters, userFilters),
    [systemFilters, userFilters],
  );

  if (isLoading) {
    return <FidesSpinner />;
  }

  const showSpinner = isLoading || isFetching;

  return (
    <Table
      columns={columns}
      dataSource={tasks}
      rowKey="task_id"
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
      locale={{
        emptyText: searchTerm ? (
          "No tasks match your search"
        ) : (
          <div data-testid="empty-state">No manual tasks available.</div>
        ),
      }}
      loading={showSpinner}
    />
  );
};
