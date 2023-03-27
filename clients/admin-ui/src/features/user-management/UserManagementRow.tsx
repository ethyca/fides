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
import {useGetUserManagedSystemsQuery, useGetUserPermissionsQuery} from "user-management/user-management.slice";

import { ROLES } from "~/features/user-management/constants";

import { USER_MANAGEMENT_ROUTE } from "../../constants";
import DeleteUserModal from "./DeleteUserModal";
import { User } from "./types";

interface UserManagementRowProps {
  user: User;
}

const UserManagementRow: React.FC<UserManagementRowProps> = ({ user }) => {
  const router = useRouter();
  const deleteModal = useDisclosure();

  const handleEditUser = () => {
    router.push(`${USER_MANAGEMENT_ROUTE}/profile/${user.id}`);
  };

  const { data: userPermissions } = useGetUserPermissionsQuery(user.id ?? "", {
    skip: !user.id,
  });
  const { data: userSystems } = useGetUserManagedSystemsQuery(user.id ?? "", {
    skip: !user.id
  })
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
        _hover={{ bg: "gray.50", cursor: "pointer" }}
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
            >
              {userSystems ? userSystems.length : 0}
            </Badge>
        </Td>
        <Td pl={0} py={1} onClick={handleEditUser}>
          {user.created_at ? new Date(user.created_at).toUTCString() : null}
        </Td>
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
                  <MenuItem
                    _focus={{ color: "complimentary.500", bg: "gray.100" }}
                    onClick={handleEditUser}
                    data-testid="edit-btn"
                  >
                    <Text fontSize="sm">Edit</Text>
                  </MenuItem>
                  <MenuItem
                    _focus={{ color: "complimentary.500", bg: "gray.100" }}
                    onClick={deleteModal.onOpen}
                    data-testid="delete-btn"
                  >
                    <Text fontSize="sm">Delete</Text>
                  </MenuItem>
                </MenuList>
              </Portal>
            </Menu>
          </ButtonGroup>
        </Td>
      </Tr>
      <DeleteUserModal user={user} {...deleteModal} />
    </>
  );
};

export default UserManagementRow;
