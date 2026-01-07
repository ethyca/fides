import {
  Button,
  ColumnsType,
  Flex,
  Icons,
  Tag,
  useChakraDisclosure as useDisclosure,
} from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { ScopeRegistryEnum } from "~/types/api";

import { ROLES } from "./constants";
import DeleteUserModal from "./DeleteUserModal";
import { User } from "./types";
import {
  useGetAllUsersQuery,
  useGetUserManagedSystemsQuery,
  useGetUserPermissionsQuery,
} from "./user-management.slice";

export const UserPermissionsCell = ({ userId }: { userId: string }) => {
  const { data: userPermissions } = useGetUserPermissionsQuery(userId, {
    skip: !userId,
  });
  const permissionsLabels: string[] = [];
  if (userPermissions && userPermissions.roles) {
    userPermissions.roles.forEach((permissionRole) => {
      const matchingRole = ROLES.find(
        (role) => role.roleKey === permissionRole,
      );
      if (matchingRole) {
        permissionsLabels.push(matchingRole.permissions_label);
      }
    });
  }
  return (
    <>
      {permissionsLabels.map((permission) => (
        <Tag data-testid="user-permissions-badge" key={permission}>
          {permission}
        </Tag>
      ))}
    </>
  );
};

export const UserSystemsCell = ({ userId }: { userId: string }) => {
  const { data: userSystems } = useGetUserManagedSystemsQuery(userId, {
    skip: !userId,
  });
  return (
    <Tag className="text-center" data-testid="user-systems-badge">
      {userSystems ? userSystems.length : 0}
    </Tag>
  );
};

export const UserActionsCell = ({ user }: { user: User }) => {
  const deleteModal = useDisclosure();
  return (
    <>
      <Button
        size="small"
        aria-label="delete"
        icon={<Icons.TrashCan />}
        onClick={(e) => {
          e.stopPropagation();
          deleteModal.onOpen();
        }}
        data-testid="delete-user-btn"
      />
      <DeleteUserModal user={user} {...deleteModal} />
    </>
  );
};

const useUserManagementTable = () => {
  const loggedInUser = useAppSelector(selectUser);
  const canUserDelete = useHasPermission([ScopeRegistryEnum.USER_DELETE]);
  const canUserUpdate = useHasPermission([ScopeRegistryEnum.USER_UPDATE]);

  // Table state management
  const tableState = useTableState({
    pagination: {
      defaultPageSize: 25,
      pageSizeOptions: [25, 50, 100],
    },
    search: {
      defaultSearchQuery: "",
    },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;

  // Fetch data
  const { data, isLoading, isFetching, error } = useGetAllUsersQuery({
    page: pageIndex,
    size: pageSize,
    username: searchQuery || undefined,
  });

  // Ant Table integration
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

  // Columns definition
  const columns: ColumnsType<User> = useMemo(
    () => [
      {
        title: "Username",
        dataIndex: "username",
        key: "username",
        fixed: "left",
        render: (username: string, user: User) => {
          const isOwnProfile = loggedInUser
            ? loggedInUser.id === user.id
            : false;
          const canEditUser = canUserUpdate || isOwnProfile;

          return (
            <Flex gap="small">
              <LinkCell
                href={
                  canEditUser
                    ? `${USER_MANAGEMENT_ROUTE}/profile/${user.id}`
                    : undefined
                }
                data-testid={`user-link-${user.id}`}
              >
                {username}
              </LinkCell>{" "}
              {user.disabled && (
                <Tag color="success" data-testid="invite-sent-badge">
                  Invite sent
                </Tag>
              )}
            </Flex>
          );
        },
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
        title: "Permissions",
        key: "permissions",
        render: (_: unknown, user: User) => (
          <UserPermissionsCell userId={user.id ?? ""} />
        ),
      },
      {
        title: "Assigned systems",
        key: "systems",
        render: (_: unknown, user: User) => (
          <UserSystemsCell userId={user.id ?? ""} />
        ),
      },
      {
        title: "Created at",
        dataIndex: "created_at",
        key: "created_at",
        render: (createdAt: string | null | undefined) =>
          createdAt ? new Date(createdAt).toUTCString() : null,
      },
      ...(canUserDelete
        ? [
            {
              title: "",
              key: "actions",
              width: 80,
              render: (_: unknown, user: User) => (
                <UserActionsCell user={user} />
              ),
            },
          ]
        : []),
    ],
    [canUserDelete, canUserUpdate, loggedInUser],
  );

  return {
    tableProps,
    columns,
    error,
    searchQuery,
    updateSearch,
  };
};

export default useUserManagementTable;
