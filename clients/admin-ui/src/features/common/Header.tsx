import {
  Button,
  Flex,
  Link,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  QuestionIcon,
  Stack,
  Text,
  UserIcon,
} from "@fidesui/react";
import React from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { logout, selectUser, useLogoutMutation } from "~/features/auth";

const useHeader = () => {
  const { username } = useAppSelector(selectUser) ?? { username: "" };
  return { username };
};

const Header: React.FC = () => {
  const { username } = useHeader();
  const [logoutMutation] = useLogoutMutation();
  const dispatch = useAppDispatch();

  const handleLogout = async () => {
    await logoutMutation({});
    dispatch(logout());
  };

  return (
    <Flex
      as="header"
      height={12}
      width="100%"
      paddingX={10}
      flexShrink={0}
      alignItems="center"
      justifyContent="end"
      backgroundColor="gray.50"
    >
      <Flex alignItems="center">
        <Link href="https://docs.ethyca.com" isExternal>
          <Button size="sm" variant="ghost">
            <QuestionIcon color="gray.700" boxSize={4} />
          </Button>
        </Link>
        {username && (
          <Menu>
            <MenuButton
              as={Button}
              size="sm"
              variant="ghost"
              data-testid="header-menu-button"
            >
              <UserIcon color="gray.700" />
            </MenuButton>
            <MenuList shadow="xl" zIndex="20">
              <Stack px={3} py={2} spacing={1}>
                <Text fontWeight="medium">{username}</Text>
              </Stack>

              <MenuDivider />
              <MenuItem
                _focus={{ color: "complimentary.500", bg: "gray.100" }}
                onClick={handleLogout}
                data-testid="header-menu-sign-out"
              >
                Sign out
              </MenuItem>
            </MenuList>
          </Menu>
        )}
      </Flex>
    </Flex>
  );
};

export default Header;
