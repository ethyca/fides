import {
  AntColumnsType as ColumnsType,
  AntFilterValue as FilterValue,
  AntTable as Table,
  AntTablePaginationConfig as TablePaginationConfig,
  AntTag as Tag,
  AntTypography as Typography,
  SelectInline,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import DaysLeftTag from "~/features/common/DaysLeftTag";
import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import FidesSpinner from "~/features/common/FidesSpinner";
import { USER_PROFILE_ROUTE } from "~/features/common/nav/routes";
import { PAGE_SIZES } from "~/features/common/table/v2/PaginationBar";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

import { ActionButtons } from "./components/ActionButtons";
import {
  REQUEST_TYPE_FILTER_OPTIONS,
  STATUS_FILTER_OPTIONS,
  STATUS_MAP,
} from "./constants";
import { useGetTasksQuery } from "./manual-tasks.slice";
import {
  AssignedUser,
  ManualTask,
  RequestType,
  SubjectIdentity,
  System,
  TaskStatus,
} from "./mocked/types";

interface FilterOption {
  text: string;
  value: string;
}

interface ManualTaskFilters {
  status?: string;
  systemName?: string;
  requestType?: string;
  assignedUsers?: string;
}

interface UserOption {
  label: string;
  value: string;
}

const getColumns = (
  systemFilters: FilterOption[],
  userFilters: FilterOption[],
  onUserClick: (userId: string) => void,
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
      <Tag
        color={STATUS_MAP[status].color}
        data-testid="manual-task-status-tag"
      >
        {STATUS_MAP[status].label}
      </Tag>
    ),
    filters: STATUS_FILTER_OPTIONS,
    filterMultiple: false,
  },
  {
    title: "System",
    dataIndex: ["system", "name"],
    key: "system_name",
    width: 210,
    filters: systemFilters,
    filterMultiple: false,
  },
  {
    title: "Type",
    dataIndex: ["privacy_request", "request_type"],
    key: "request_type",
    width: 150,
    render: (type: RequestType) => {
      const actionType =
        type === "access" ? ActionType.ACCESS : ActionType.ERASURE;
      const displayName = SubjectRequestActionTypeMap.get(actionType) || type;
      return <Typography.Text>{displayName}</Typography.Text>;
    },
    filters: REQUEST_TYPE_FILTER_OPTIONS,
    filterMultiple: false,
  },
  {
    title: "Assigned to",
    dataIndex: "assigned_users",
    key: "assigned_users",
    width: 380,
    render: (assignedUsers: AssignedUser[]) => {
      const userOptions: UserOption[] = assignedUsers.map((user) => ({
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
          onTagClick={(userId) => onUserClick(userId)}
        />
      );
    },
    filters: userFilters,
    filterMultiple: false,
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
    render: (subjectIdentity: SubjectIdentity) => {
      if (!subjectIdentity) {
        return <Typography.Text>-</Typography.Text>;
      }

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

export const ManualTasks = () => {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<ManualTaskFilters>({});

  const { data, isLoading, isFetching } = useGetTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchTerm,

    status: filters.status as TaskStatus,
    systemName: filters.systemName,
    requestType: filters.requestType as RequestType,
    assignedUserId: filters.assignedUsers,
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

  const handleTableChange = (
    _pagination: TablePaginationConfig,
    tableFilters: Record<string, FilterValue | null>,
  ) => {
    const newFilters: ManualTaskFilters = {};

    if (tableFilters.status) {
      [newFilters.status] = tableFilters.status as string[];
    }
    if (tableFilters.system_name) {
      [newFilters.systemName] = tableFilters.system_name as string[];
    }
    if (tableFilters.request_type) {
      [newFilters.requestType] = tableFilters.request_type as string[];
    }
    if (tableFilters.assigned_users) {
      [newFilters.assignedUsers] = tableFilters.assigned_users as string[];
    }

    setFilters(newFilters);
    setPageIndex(1);
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  const columns = useMemo(
    () =>
      getColumns(systemFilters, userFilters, (userId) => {
        router.push({
          pathname: USER_PROFILE_ROUTE,
          query: { id: userId },
        });
      }),
    [systemFilters, userFilters, router],
  );

  if (isLoading) {
    return <FidesSpinner />;
  }

  const showSpinner = isLoading || isFetching;

  return (
    <div className="mt-2 space-y-4">
      <DebouncedSearchInput
        placeholder="Search by name or description..."
        value={searchTerm}
        onChange={handleSearchChange}
        className="max-w-sm"
      />

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
              setPageIndex(1);
            }
          },
        }}
        onChange={handleTableChange}
        locale={{
          emptyText: searchTerm ? (
            "No tasks match your search"
          ) : (
            <div data-testid="empty-state">No manual tasks available.</div>
          ),
        }}
        loading={showSpinner}
      />
    </div>
  );
};
