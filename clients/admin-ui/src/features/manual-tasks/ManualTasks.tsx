import {
  AntButton as Button,
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
import { useHasPermission } from "~/features/common/Restrict";
import { GlobalFilterV2 } from "~/features/common/table/v2/filters/GlobalFilterV2";
import { formatUser } from "~/features/common/utils";
import {
  ManualFieldRequestType,
  ManualFieldStatus,
  ManualFieldSystem,
  ManualFieldUser,
  ScopeRegistryEnum,
} from "~/types/api";

import { DownloadLightIcon } from "../common/Icon";
import { DEFAULT_PAGE_SIZES } from "../common/table/constants";
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

  // Check if user has access to all tasks (not just their own)
  const hasAccessToAllTasks = useHasPermission([
    ScopeRegistryEnum.MANUAL_FIELD_READ_ALL,
  ]);

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

    // Check if the current user is already in the list of assigned users
    // If not, add them to ensure they see an option selected in their filter
    if (currentUser?.id) {
      const isCurrentUserInList = users.some(
        (user) => user.value === currentUser.id,
      );
      if (!isCurrentUserInList) {
        users.push({
          text: formatUser(currentUser, { fallbackToId: true }),
          value: currentUser.id,
        });
      }
    }
    return users;
  }, [filterOptions?.assigned_users, currentUser]);

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

  const handleExport = async () => {
    console.log("Exporting manual tasks");
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
    hasAccessToAllTasks,
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
            You have no tasks assigned.{" "}
            {hasAccessToAllTasks && (
              <span>
                You can modify the &quot;Assigned to&quot; column filter to view
                tasks assigned to other users.
              </span>
            )}
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
      <Flex gap={3} align="center" justify="space-between" className="mb-4">
        <GlobalFilterV2
          globalFilter={filters.privacyRequestId || ""}
          setGlobalFilter={handlePrivacyRequestIdChange}
          placeholder="Search by privacy request ID"
          testid="privacy-request-id-filter"
        />
        <Button
          aria-label="Export manual tasks as CSV"
          data-testid="export-manual-tasks-btn"
          icon={<DownloadLightIcon ml="1.5px" />}
          onClick={handleExport}
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
          pageSizeOptions: DEFAULT_PAGE_SIZES,
          total: totalRows || 0,
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
        scroll={{ scrollToFirstRowOnChange: true }}
        tableLayout="fixed"
        className="[&_th]:!break-normal"
      />
    </div>
  );
};
