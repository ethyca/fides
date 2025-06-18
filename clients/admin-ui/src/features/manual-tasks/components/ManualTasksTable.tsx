import type { ColumnsType } from "antd/es/table";
import { format } from "date-fns";
import {
  AntTable as Table,
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";
import { useEffect, useMemo } from "react";

import FidesSpinner from "~/features/common/FidesSpinner";
import {
  PaginationBar,
  useServerSidePagination,
} from "~/features/common/table/v2";
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

// Map request types to tag colors and labels
const requestTypeMap: Record<RequestType, { color: string; label: string }> = {
  access: { color: "blue", label: "Access" },
  erasure: { color: "red", label: "Erasure" },
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
    sorter: (a, b) => a.name.localeCompare(b.name),
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
    render: (daysLeft) => (
      <Tooltip title={`Due in ${daysLeft} days`}>
        <span className={daysLeft < 3 ? "font-medium text-red-500" : ""}>
          {daysLeft}
        </span>
      </Tooltip>
    ),
    sorter: (a, b) => a.days_left - b.days_left,
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
    width: 120,
    render: (type: RequestType) => (
      <Tag
        color={requestTypeMap[type].color}
        data-testid="manual-task-request-type-tag"
      >
        {requestTypeMap[type].label}
      </Tag>
    ),
    filters: [
      { text: "Access", value: "access" },
      { text: "Erasure", value: "erasure" },
    ],
    onFilter: (value, record) => record.request_type === value,
  },
  {
    title: "Created date",
    dataIndex: "created_at",
    key: "created_at",
    width: 120,
    render: (date) => format(new Date(date), "MMM d, yyyy"),
    sorter: (a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
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

      <div className="mt-4">
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
