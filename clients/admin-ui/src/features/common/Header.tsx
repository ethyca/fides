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
import NextLink from "next/link";
import React from "react";

import logoImage from "~/../public/logo.svg";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { INDEX_ROUTE } from "~/constants";
import { logout, selectUser, useLogoutMutation } from "~/features/auth";
import Image from "~/features/common/Image";

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
      justifyContent="space-between"
      alignItems="center"
      backgroundColor="gray.50"
    >
      <NextLink href={INDEX_ROUTE} passHref>
        {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
        <Link display="flex">
          <Image src={logoImage} width={83} height={26} alt="Fides Logo" />
        </Link>
      </NextLink>
      <Flex alignItems="center">
        <Link href="https://ethyca.github.io/fides/" isExternal>
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
            <MenuList shadow="xl">
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
