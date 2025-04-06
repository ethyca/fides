import { TrashCanSolidIcon } from "common/Icon/TrashCanSolidIcon";
import {
  AntButton as Button,
  AntTag as Tag,
  Td,
  Tr,
  useDisclosure,
} from "fidesui";
import { useRouter } from "next/router";
import React from "react";
import {
  useGetUserManagedSystemsQuery,
  useGetUserPermissionsQuery,
} from "user-management/user-management.slice";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import { ROLES } from "~/features/user-management/constants";
import { ScopeRegistryEnum } from "~/types/api";

import DeleteUserModal from "./DeleteUserModal";
import { User } from "./types";

interface UserManagementRowProps {
  user: User;
}

const UserManagementRow = ({ user }: UserManagementRowProps) => {
  const router = useRouter();
  const deleteModal = useDisclosure();
  const loggedInUser = useAppSelector(selectUser);
  const isOwnProfile = loggedInUser ? loggedInUser.id === user.id : false;
  const canEditUser =
    useHasPermission([ScopeRegistryEnum.USER_UPDATE]) || isOwnProfile;

  const handleEditUser = () => {
    if (canEditUser) {
      router.push(`${USER_MANAGEMENT_ROUTE}/profile/${user.id}`);
    }
  };

  const { data: userPermissions } = useGetUserPermissionsQuery(user.id ?? "", {
    skip: !user.id,
  });
  const { data: userSystems } = useGetUserManagedSystemsQuery(user.id ?? "", {
    skip: !user.id,
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
      <Tr
        key={user.id}
        _hover={{ bg: "gray.50", cursor: canEditUser ? "pointer" : undefined }}
        height="36px"
        data-testid={`row-${user.id}`}
      >
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.username}{" "}
          {user.disabled && (
            <Tag color="success" data-testid="invite-sent-badge">
              Invite sent
            </Tag>
          )}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.email_address}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.first_name}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.last_name}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {permissionsLabels.map((permission) => (
            <Tag data-testid="user-permissions-badge" key={permission}>
              {permission}
            </Tag>
          ))}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          <Tag className="text-center" data-testid="user-systems-badge">
            {userSystems ? userSystems.length : 0}
          </Tag>
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.created_at ? new Date(user.created_at).toUTCString() : null}
        </Td>
        <Restrict scopes={[ScopeRegistryEnum.USER_DELETE]}>
          <Td pr={0} py={1} textAlign="end" position="relative">
            <Button
              aria-label="delete"
              icon={<TrashCanSolidIcon />}
              onClick={deleteModal.onOpen}
              data-testid="delete-user-btn"
            />
          </Td>
        </Restrict>
      </Tr>
      <DeleteUserModal user={user} {...deleteModal} />
    </>
  );
};

export default UserManagementRow;
