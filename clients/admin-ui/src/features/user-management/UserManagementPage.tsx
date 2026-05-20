import { Button, ColumnsType, Flex, Table, Tag } from "fidesui";
import type { NextPage } from "next";
import { parseAsString, useQueryState } from "nuqs";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  useGetRolesQuery,
  useGetUserRolesQuery,
} from "~/features/rbac/rbac.slice";
import { ScopeRegistryEnum } from "~/types/api";

import { formatDate } from "~/features/common/utils";

import { ROLES } from "./constants";
import { User } from "./types";
import UserActionsDropdown from "./UserActionsDropdown";
import UserDrawer from "./UserDrawer";
import {
  useGetAllUsersQuery,
  useGetUserPermissionsQuery,
} from "./user-management.slice";

// --- Cell component (kept local — only used by the table columns) ---

const UserPermissionsCell = ({ userId }: { userId: string }) => {
  const { rbac: isRbacEnabled } = useFeatures();

  // Legacy permissions
  const { data: userPermissions } = useGetUserPermissionsQuery(userId, {
    skip: !userId || isRbacEnabled,
  });

  // RBAC
  const { data: rbacRoles } = useGetRolesQuery({}, { skip: !isRbacEnabled });
  const { data: userRbacRoles } = useGetUserRolesQuery(
    { userId },
    { skip: !userId || !isRbacEnabled },
  );

  const labels = useMemo(() => {
    if (isRbacEnabled) {
      if (!userRbacRoles || !rbacRoles) return [];
      return userRbacRoles
        .map((ur) => {
          const role = rbacRoles.find((r) => r.id === ur.role_id);
          const match = ROLES.find((r) => r.roleKey === role?.key);
          return match?.permissions_label || role?.name;
        })
        .filter((l): l is string => !!l);
    }
    // Legacy
    if (!userPermissions?.roles) return [];
    return userPermissions.roles
      .map((roleKey) => ROLES.find((r) => r.roleKey === roleKey)?.permissions_label)
      .filter((l): l is string => !!l);
  }, [isRbacEnabled, userRbacRoles, rbacRoles, userPermissions]);

  return (
    <>
      {labels.map((label) => (
        <Tag key={label} data-testid="user-permissions-badge">
          {label}
        </Tag>
      ))}
    </>
  );
};

// --- Main page component ---

const UserManagementPage: NextPage = () => {
  const { rbac: isRbacEnabled } = useFeatures();
  const loggedInUser = useAppSelector(selectUser);
  const canUserUpdate = useHasPermission([ScopeRegistryEnum.USER_UPDATE]);

  // Drawer state via URL query param
  const [drawerUserId, setDrawerUserId] = useQueryState(
    "userId",
    parseAsString,
  );

  // Table state
  const tableState = useTableState({
    pagination: { defaultPageSize: 25, pageSizeOptions: [25, 50, 100] },
    search: { defaultSearchQuery: "" },
  });
  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;

  // Fetch users
  const { data, isLoading, isFetching, error } = useGetAllUsersQuery({
    page: pageIndex,
    size: pageSize,
    username: searchQuery || undefined,
  });

  const antTableConfig = useMemo(
    () => ({
      dataSource: data?.items ?? [],
      totalRows: data?.total ?? 0,
      isLoading,
      isFetching,
      getRowKey: (record: User) => record.id ?? "",
    }),
    [data?.items, data?.total, isLoading, isFetching],
  );

  const { tableProps } = useAntTable(tableState, antTableConfig);

  // Columns
  const columns: ColumnsType<User> = useMemo(
    () => [
      {
        title: "Username",
        dataIndex: "username",
        key: "username",
        render: (username: string, user: User) => (
          <Flex gap="small" align="center">
            <a
              role="button"
              tabIndex={0}
              className="cursor-pointer text-link hover:underline"
              onClick={() => setDrawerUserId(user.id)}
              data-testid={`user-link-${user.id}`}
            >
              {username}
            </a>
            {user.disabled && (
              <Tag color="success" data-testid="invite-sent-badge">
                Invite sent
              </Tag>
            )}
          </Flex>
        ),
      },
      {
        title: "Email",
        dataIndex: "email_address",
        key: "email_address",
      },
      {
        title: "First name",
        dataIndex: "first_name",
        key: "first_name",
      },
      {
        title: "Last name",
        dataIndex: "last_name",
        key: "last_name",
      },
      {
        title: isRbacEnabled ? "Roles" : "Permissions",
        key: "permissions",
        render: (_: unknown, user: User) => (
          <UserPermissionsCell userId={user.id ?? ""} />
        ),
      },
      {
        title: "Created at",
        dataIndex: "created_at",
        key: "created_at",
        render: (createdAt: string | null | undefined) =>
          createdAt ? formatDate(createdAt, { showTime: false }) : null,
      },
      {
        title: "",
        key: "actions",
        width: 48,
        render: (_: unknown, user: User) => (
          <UserActionsDropdown
            user={user}
            onEdit={(id) => setDrawerUserId(id)}
          />
        ),
      },
    ],
    [isRbacEnabled, setDrawerUserId],
  );

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching user management"
      />
    );
  }

  return (
    <FixedLayout title="User Management">
      <PageHeader
        heading="Users"
        breadcrumbItems={[{ title: "All users" }]}
        isSticky={false}
      />

      <Flex justify="space-between" className="mb-4">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search by username"
          data-testid="user-search"
        />
        <Restrict scopes={[ScopeRegistryEnum.USER_CREATE]}>
          <Button
            type="primary"
            onClick={() => setDrawerUserId("new")}
            data-testid="add-new-user-btn"
          >
            Add new user
          </Button>
        </Restrict>
      </Flex>

      <Table
        {...tableProps}
        columns={columns}
        data-testid="user-management-table"
        onRow={(user) => ({
          "data-testid": `row-${user.id}`,
          style: { cursor: "pointer" },
          onClick: () => {
            const isOwnProfile = loggedInUser?.id === user.id;
            if (canUserUpdate || isOwnProfile) {
              setDrawerUserId(user.id);
            }
          },
        })}
      />

      <UserDrawer
        userId={drawerUserId}
        onClose={() => setDrawerUserId(null)}
      />
    </FixedLayout>
  );
};

export default UserManagementPage;
