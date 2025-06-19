import type { ColumnsType } from "antd/es/table";
import {
  AntTable as Table,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";
import { useEffect, useMemo } from "react";

import DaysLeftTag from "~/features/common/DaysLeftTag";
import FidesSpinner from "~/features/common/FidesSpinner";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
import { formatDate } from "~/features/common/utils";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";
import {
  ManualTask,
  RequestType,
  TaskStatus,
} from "~/types/api/models/ManualTask";

import { useGetTasksQuery } from "../manual-tasks.slice";
import { ActionButtons } from "./ActionButtons";

// Map task status to tag colors and labels
const statusMap: Record<TaskStatus, { color: string; label: string }> = {
  new: { color: "blue", label: "New" },
  completed: { color: "green", label: "Completed" },
  skipped: { color: "gray", label: "Skipped" },
};

interface Props {
  searchTerm?: string;
}

// Extract column definitions to a separate function for better readability
const getColumns = (
  systemFilters: { text: string; value: string }[],
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
    title: "Days left",
    dataIndex: "days_left",
    key: "days_left",
    width: 100,
    render: (daysLeft: number) => (
      <DaysLeftTag
        daysLeft={daysLeft}
        includeText={false}
        status={PrivacyRequestStatus.PENDING}
      />
    ),
  },
  {
    title: "Source",
    dataIndex: "system_name",
    key: "system_name",
    width: 150,
    filters: systemFilters,
    onFilter: (value, record) => record.system_name === value,
  },
  {
    title: "Request type",
    dataIndex: "request_type",
    key: "request_type",
    width: 140,
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
    onFilter: (value, record) => record.request_type === value,
  },
  {
    title: "Created",
    dataIndex: "created_at",
    key: "created_at",
    width: 250,
    render: (date) => formatDate(date),
  },
  {
    title: "Actions",
    key: "actions",
    width: 120,
    render: (_, record) => <ActionButtons task={record} />,
  },
];

export const ManualTasksTable = ({ searchTerm }: Props) => {
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
  } = useServerSidePagination();

  const { data, isLoading, isFetching } = useGetTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchTerm,
  });

  const {
    items: tasks,
    total: totalRows,
    pages: totalPages,
  } = useMemo(() => data || { items: [], total: 0, pages: 0 }, [data]);

  useEffect(() => {
    setTotalPages(totalPages);
  }, [totalPages, setTotalPages]);

  // Create unique filters for system names
  const systemFilters = useMemo(
    () =>
      tasks
        ? Array.from(new Set(tasks.map((task) => task.system_name))).map(
            (name) => ({ text: name, value: name }),
          )
        : [],
    [tasks],
  );

  const columns = useMemo(() => getColumns(systemFilters), [systemFilters]);

  if (isLoading) {
    return <FidesSpinner />;
  }

  const showSpinner = isLoading || isFetching;

  return (
    <div>
      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="task_id"
        size="small"
        pagination={false}
        locale={{
          emptyText: searchTerm ? (
            "No tasks match your search"
          ) : (
            <div data-testid="empty-state">No manual tasks available.</div>
          ),
        }}
        loading={showSpinner}
      />

      <div className="mt-4 flex justify-end">
        <PaginationBar
          pageSizes={PAGE_SIZES}
          totalRows={totalRows || 0}
          onPreviousPageClick={onPreviousPageClick}
          isPreviousPageDisabled={isPreviousPageDisabled}
          onNextPageClick={onNextPageClick}
          isNextPageDisabled={isNextPageDisabled}
          setPageSize={setPageSize}
          startRange={startRange}
          endRange={endRange}
        />
      </div>
    </div>
  );
};
