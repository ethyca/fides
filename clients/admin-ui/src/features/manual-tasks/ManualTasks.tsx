import {
  AntColumnsType as ColumnsType,
  AntFilterValue as FilterValue,
  AntTable as Table,
  AntTablePaginationConfig as TablePaginationConfig,
  AntTag as Tag,
  AntTypography as Typography,
  Flex,
  SelectInline,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import DaysLeftTag from "~/features/common/DaysLeftTag";
import FidesSpinner from "~/features/common/FidesSpinner";
import { USER_PROFILE_ROUTE } from "~/features/common/nav/routes";
import { GlobalFilterV2 } from "~/features/common/table/v2/filters/GlobalFilterV2";
import { PAGE_SIZES } from "~/features/common/table/v2/PaginationBar";
import { formatUser } from "~/features/common/utils";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import {
  ActionType,
  ManualFieldListItem,
  ManualFieldRequestType,
  ManualFieldStatus,
  ManualFieldSystem,
  ManualFieldUser,
  PrivacyRequestStatus,
} from "~/types/api";

import { ActionButtons } from "./components/ActionButtons";
import {
  REQUEST_TYPE_FILTER_OPTIONS,
  STATUS_FILTER_OPTIONS,
  STATUS_MAP,
} from "./constants";
import { useGetTasksQuery } from "./manual-tasks.slice";

interface FilterOption {
  text: string;
  value: string;
}

interface ManualTaskFilters {
  status?: string;
  systemName?: string;
  requestType?: string;
  assignedUsers?: string;
  privacyRequestId?: string;
}

interface UserOption {
  label: string;
  value: string;
}

const getColumns = (
  systemFilters: FilterOption[],
  userFilters: FilterOption[],
  onUserClick: (userId: string) => void,
): ColumnsType<ManualFieldListItem> => [
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
    render: (status: ManualFieldStatus) => (
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
    dataIndex: "request_type",
    key: "request_type",
    width: 150,
    render: (type: ManualFieldRequestType) => {
      const actionType =
        type === ManualFieldRequestType.ACCESS
          ? ActionType.ACCESS
          : ActionType.ERASURE;
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
    render: (assignedUsers: ManualFieldUser[]) => {
      if (!assignedUsers || assignedUsers.length === 0) {
        return <Typography.Text>-</Typography.Text>;
      }

      const userOptions: UserOption[] = assignedUsers.map((user) => ({
        label: formatUser(user),
        value: user.id,
      }));

      const currentAssignedUserIds = assignedUsers.map((user) => user.id);

      return (
        <SelectInline
          value={currentAssignedUserIds}
          options={userOptions}
          readonly
          onTagClick={(userId) => onUserClick(String(userId))}
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
    render: (daysLeft: number | null) => (
      <DaysLeftTag
        daysLeft={daysLeft || 0}
        includeText={false}
        status={PrivacyRequestStatus.PENDING}
      />
    ),
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
    width: 120,
    render: (_, record) => <ActionButtons task={record} />,
  },
];

export const ManualTasks = () => {
  const router = useRouter();
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<ManualTaskFilters>({});

  const [privacyRequestIdInput, setPrivacyRequestIdInput] = useState(
    router.query.privacy_request_id || "",
  );

  // Initialize privacy request ID filter from URL query parameter
  useEffect(() => {
    const { privacy_request_id: privacyRequestIdQuery } = router.query;
    if (privacyRequestIdQuery && typeof privacyRequestIdQuery === "string") {
      setPrivacyRequestIdInput(privacyRequestIdQuery);
      setFilters((prev) => ({
        ...prev,
        privacyRequestId: privacyRequestIdQuery,
      }));
    }
  }, [router.query]);

  const handlePrivacyRequestIdChange = (value: string | undefined) => {
    setPrivacyRequestIdInput(value || "");

    const newFilters = { ...filters };
    if (value && value.trim()) {
      newFilters.privacyRequestId = value.trim();
    } else {
      delete newFilters.privacyRequestId;
    }

    setFilters(newFilters);
    setPageIndex(1);
  };

  const { data, isLoading, isFetching } = useGetTasksQuery({
    page: pageIndex,
    size: pageSize,
    status: filters.status as ManualFieldStatus,
    systemName: filters.systemName,
    requestType: filters.requestType as ManualFieldRequestType,
    assignedUserId: filters.assignedUsers,
    privacyRequestId: filters.privacyRequestId,
  });

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

  const systemFilters = useMemo(
    () =>
      filterOptions?.systems?.map((system: ManualFieldSystem) => ({
        text: system.name,
        value: system.name,
      })) || [],
    [filterOptions?.systems],
  );

  const userFilters = useMemo(
    () =>
      filterOptions?.assigned_users?.map((user: ManualFieldUser) => ({
        text: formatUser(user),
        value: user.id,
      })) || [],
    [filterOptions?.assigned_users],
  );

  const handleTableChange = (
    _pagination: TablePaginationConfig,
    tableFilters: Record<string, FilterValue | null>,
  ) => {
    const newFilters: ManualTaskFilters = {
      // Keep the privacy request ID filter if it exists
      privacyRequestId: filters.privacyRequestId,
    };

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
      <Flex gap={3} align="center" className="mb-4">
        <GlobalFilterV2
          globalFilter={privacyRequestIdInput}
          setGlobalFilter={handlePrivacyRequestIdChange}
          placeholder="Search by privacy request ID"
          testid="privacy-request-id-filter"
        />
      </Flex>

      <Table
        columns={columns}
        dataSource={tasks}
        rowKey={(record) =>
          `${record.privacy_request.id}-${record.manual_field_id}`
        }
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
          emptyText: (
            <div data-testid="empty-state">No manual tasks available.</div>
          ),
        }}
        loading={showSpinner}
      />
    </div>
  );
};
