import type { ColumnsType } from "antd/es/table";
import { format } from "date-fns";
import {
  AntTable as Table,
  AntTableProps as TableProps,
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";
import { useCallback, useState } from "react";

import FidesSpinner from "~/features/common/FidesSpinner";
import { ManualTask, RequestType } from "~/types/api/models/ManualTask";

import { useGetTasksQuery } from "../manual-tasks.slice";
import { ActionButtons } from "./ActionButtons";
import { StatusTag } from "./StatusTag";

const DEFAULT_PAGE_SIZE = 10;

interface Props {
  searchTerm?: string;
}

export const ManualTasksTable = ({ searchTerm }: Props) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const { data, isLoading } = useGetTasksQuery();

  // Filter tasks by search term
  const filteredTasks =
    searchTerm && data?.tasks
      ? data.tasks.filter(
          (task) =>
            task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            task.description.toLowerCase().includes(searchTerm.toLowerCase()),
        )
      : data?.tasks;

  const handleTableChange = useCallback((pagination: any) => {
    setPage(pagination.current ?? 1);
    setPageSize(pagination.pageSize ?? DEFAULT_PAGE_SIZE);
  }, []);

  // Create unique filters for system names
  const systemFilters = data?.tasks
    ? Array.from(new Set(data.tasks.map((task) => task.system_name))).map(
        (name) => ({ text: name, value: name }),
      )
    : [];

  const columns: ColumnsType<ManualTask> = [
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
      render: (status) => <StatusTag status={status} />,
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
        <Tag color={type === "access" ? "blue" : "red"}>
          {type === "access" ? "Access" : "Erasure"}
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

  const paginationConfig: TableProps<ManualTask>["pagination"] = {
    current: page,
    pageSize,
    total: filteredTasks?.length,
    showSizeChanger: true,
    showTotal: (total) => `${total} tasks`,
    pageSizeOptions: ["10", "25", "50", "100"],
  };

  const tableLocale = {
    emptyText: searchTerm ? (
      "No tasks match your search"
    ) : (
      <div data-testid="empty-state">No manual tasks available.</div>
    ),
  };

  if (isLoading) {
    return <FidesSpinner />;
  }

  return (
    <Table
      columns={columns}
      dataSource={filteredTasks}
      rowKey="task_id"
      size="small"
      pagination={paginationConfig}
      onChange={handleTableChange}
      locale={tableLocale}
    />
  );
};
