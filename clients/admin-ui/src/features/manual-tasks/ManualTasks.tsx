import {
  AntFilterValue as FilterValue,
  AntTable as Table,
  AntTablePaginationConfig as TablePaginationConfig,
  AntTypography as Typography,
  Flex,
} from "fidesui";
import { isEqual } from "lodash";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import FidesSpinner from "~/features/common/FidesSpinner";
import { USER_PROFILE_ROUTE } from "~/features/common/nav/routes";
import { GlobalFilterV2 } from "~/features/common/table/v2/filters/GlobalFilterV2";
import { PAGE_SIZES } from "~/features/common/table/v2/PaginationBar";
import { formatUser } from "~/features/common/utils";
import {
  ManualFieldRequestType,
  ManualFieldStatus,
  ManualFieldSystem,
  ManualFieldUser,
} from "~/types/api";

import { useManualTaskColumns } from "./hooks";
import { useGetTasksQuery } from "./manual-tasks.slice";

interface ManualTaskFilters {
  status?: string;
  systemName?: string;
  requestType?: string;
  assignedUsers?: string;
  privacyRequestId?: string;
}

export const ManualTasks = () => {
  const router = useRouter();
  const currentUser = useAppSelector(selectUser);
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const privacyRequestIdQueryParam =
    router.query.privacy_request_id || undefined;

  // Default filters - current user assigned by default
  // (unless we're receiving a privacy_request_id query param)
  // which means it comes from a link to view the tasks for a specific privacy request
  const defaultFilters: ManualTaskFilters = useMemo(() => {
    const filters: ManualTaskFilters = {};

    if (currentUser?.id && !privacyRequestIdQueryParam) {
      filters.assignedUsers = currentUser.id;
    }

    if (
      privacyRequestIdQueryParam &&
      typeof privacyRequestIdQueryParam === "string"
    ) {
      filters.privacyRequestId = privacyRequestIdQueryParam;
    }

    return filters;
  }, [currentUser?.id, privacyRequestIdQueryParam]);

  // Initialize filters with default
  const [filters, setFilters] = useState<ManualTaskFilters>(defaultFilters);

  const handlePrivacyRequestIdChange = (value: string | undefined) => {
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

  // Separate query for filter options without any filters applied
  const { data: filterOptionsData } = useGetTasksQuery({
    page: 1,
    size: 1, // Minimal results, we only need the filter_options
  });

  const { items: tasks, total: totalRows } = useMemo(
    () =>
      data || {
        items: [],
        total: 0,
        pages: 0,
        filter_options: { assigned_users: [], systems: [] },
      },
    [data],
  );

  const filterOptions = useMemo(
    () =>
      filterOptionsData?.filter_options || {
        assigned_users: [],
        systems: [],
      },
    [filterOptionsData],
  );

  const systemFilters = useMemo(
    () =>
      filterOptions?.systems?.map((system: ManualFieldSystem) => ({
        text: system.name,
        value: system.name,
      })) || [],
    [filterOptions?.systems],
  );

  const userFilters = useMemo(() => {
    const users =
      filterOptions?.assigned_users?.map((user: ManualFieldUser) => ({
        text: formatUser(user),
        value: user.id,
      })) || [];

    // If it's a root user, it's not going to be in the list of users from the API
    // so we need to add it to the list of users for it to be a valid option in the dropdown
    const isRootUser = currentUser?.id && !currentUser?.id.startsWith("fid_");
    if (isRootUser) {
      users.push({
        text: currentUser?.username || currentUser?.id,
        value: currentUser.id,
      });
    }
    return users;
  }, [filterOptions?.assigned_users, currentUser?.id, currentUser?.username]);

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

  const onUserClick = (userId: string) => {
    router.push({
      pathname: USER_PROFILE_ROUTE,
      query: { id: userId },
    });
  };

  const columns = useManualTaskColumns({
    systemFilters,
    userFilters,
    onUserClick,
    currentFilters: filters,
  });

  // Check if only the current user filter is applied (for custom empty state)
  const isOnlyCurrentUserFiltered = useMemo(
    () => isEqual(filters, defaultFilters),
    [filters, defaultFilters],
  );

  if (isLoading) {
    return <FidesSpinner />;
  }

  const showSpinner = isLoading || isFetching;

  // Custom empty text based on filters
  const getEmptyText = () => {
    if (isOnlyCurrentUserFiltered) {
      return (
        <div data-testid="empty-state-current-user" className="my-4">
          <Typography.Paragraph>
            You have no tasks assigned. You can modify the &quot;Assigned
            to&quot; column filter to view tasks assigned to other users.
          </Typography.Paragraph>
        </div>
      );
    }

    return (
      <div data-testid="empty-state" className="my-4">
        No results found.
      </div>
    );
  };

  return (
    <div className="mt-2 space-y-4">
      <Flex gap={3} align="center" className="mb-4">
        <GlobalFilterV2
          globalFilter={filters.privacyRequestId || ""}
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
          emptyText: getEmptyText(),
        }}
        loading={showSpinner}
      />
    </div>
  );
};
