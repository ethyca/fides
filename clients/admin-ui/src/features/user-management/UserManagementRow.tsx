import {
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

import { USER_MANAGEMENT_ROUTE } from "../../constants";
import DeleteUserModal from "./DeleteUserModal";
import { User } from "./types";

interface UserManagementRowProps {
  user: User;
}

const UserManagementRow: React.FC<UserManagementRowProps> = ({ user }) => {
  const router = useRouter();
  const modal = useDisclosure();

  const handleEditUser = () => {
    router.push(`${USER_MANAGEMENT_ROUTE}/profile/${user.id}`);
  };

  return (
    <>
      <Tr
        key={user.id}
        _hover={{ bg: "gray.50" }}
        height="36px"
        data-testid={`row-${user.id}`}
      >
        <Td pl={0} py={1}>
          {user.username}
        </Td>
        <Td pl={0} py={1}>
          {user.first_name}
        </Td>
        <Td pl={0} py={1}>
          {user.last_name}
        </Td>
        <Td pl={0} py={1}>
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
                    onClick={modal.onOpen}
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
      <DeleteUserModal user={user} {...modal} />
    </>
  );
};

export default UserManagementRow;
