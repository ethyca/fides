import {
  Badge,
  Button,
  ButtonGroup,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  Portal,
  Td,
  Text,
  Tr,
  useDisclosure,
} from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";
import { useGetUserPermissionsQuery } from "user-management/user-management.slice";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import Restrict, { useHasPermission } from "~/features/common/Restrict";
import { ROLES } from "~/features/user-management/constants";
import { ScopeRegistryEnum } from "~/types/api";

import { USER_MANAGEMENT_ROUTE } from "../../constants";
import DeleteUserModal from "./DeleteUserModal";
import { User } from "./types";

interface UserManagementRowProps {
  user: User;
}

const UserManagementRow: React.FC<UserManagementRowProps> = ({ user }) => {
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
  const permissionsLabels: string[] = [];
  if (userPermissions && userPermissions.roles) {
    userPermissions.roles.forEach((permissionRole) => {
      const matchingRole = ROLES.find(
        (role) => role.roleKey === permissionRole
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
          {user.username}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.first_name}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.last_name}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {permissionsLabels.map((permission) => (
            <Badge
              bg="gray.500"
              color="white"
              paddingLeft="8px"
              textTransform="none"
              paddingRight="8px"
              height="18px"
              lineHeight="18px"
              borderRadius="6px"
              fontWeight="500"
              textAlign="center"
              data-testid="user-permissions-badge"
              key={permission}
            >
              {permission}
            </Badge>
          ))}
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.created_at ? new Date(user.created_at).toUTCString() : null}
        </Td>
        <Restrict
          scopes={[
            ScopeRegistryEnum.USER_UPDATE,
            ScopeRegistryEnum.USER_DELETE,
          ]}
        >
          <Td pr={0} py={1} textAlign="end" position="relative">
            <ButtonGroup>
              <Menu>
                <MenuButton
                  as={Button}
                  size="xs"
                  bg="white"
                  data-testid="menu-btn"
                >
                  <MoreIcon color="gray.700" w={18} h={18} />
                </MenuButton>
                <Portal>
                  <MenuList shadow="xl" data-testid={`menu-${user.id}`}>
                    <Restrict scopes={[ScopeRegistryEnum.USER_UPDATE]}>
                      <MenuItem
                        _focus={{ color: "complimentary.500", bg: "gray.100" }}
                        onClick={handleEditUser}
                        data-testid="edit-btn"
                      >
                        <Text fontSize="sm">Edit</Text>
                      </MenuItem>
                    </Restrict>
                    <Restrict scopes={[ScopeRegistryEnum.USER_DELETE]}>
                      <MenuItem
                        _focus={{ color: "complimentary.500", bg: "gray.100" }}
                        onClick={deleteModal.onOpen}
                        data-testid="delete-btn"
                      >
                        <Text fontSize="sm">Delete</Text>
                      </MenuItem>
                    </Restrict>
                  </MenuList>
                </Portal>
              </Menu>
            </ButtonGroup>
          </Td>
        </Restrict>
      </Tr>
      <DeleteUserModal user={user} {...deleteModal} />
    </>
  );
};

export default UserManagementRow;
