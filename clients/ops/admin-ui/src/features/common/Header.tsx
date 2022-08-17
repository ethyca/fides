import {
  Button,
  Flex,
  Link,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Stack,
  Text,
} from "@fidesui/react";
import NextLink from "next/link";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { INDEX_ROUTE } from "../../constants";
import { logout, selectUser } from "../auth";
import { UserIcon } from "./Icon";
import Image from "./Image";

const useHeader = () => {
  const dispatch = useDispatch();
  const handleLogout = () => dispatch(logout());
  const { username } = useSelector(selectUser) ?? { username: "" };
  return {
    handleLogout,
    username,
  };
};

const Header: React.FC = () => {
  const { handleLogout, username } = useHeader();
  return (
    <header>
      <Flex
        bg="gray.50"
        width="100%"
        py={3}
        px={10}
        justifyContent="space-between"
        alignItems="center"
      >
        <NextLink href={INDEX_ROUTE} passHref>
          {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
          <Link display="flex">
            <Image src="/logo.svg" width={83} height={26} alt="FidesOps Logo" />
          </Link>
        </NextLink>
        <Flex alignItems="center">
          <Menu>
            <MenuButton as={Button} size="sm" variant="ghost">
              <UserIcon color="gray.700" />
            </MenuButton>
            <MenuList shadow="xl">
              <Stack px={3} py={2} spacing={0}>
                <Text fontWeight="medium">{username}</Text>
                {/* This text should only show if actually an admin */}
                {/* <Text fontSize="sm" color="gray.600">
              Administrator
            </Text> */}
              </Stack>
              <MenuDivider />
              <MenuItem
                px={3}
                _focus={{ color: "complimentary.500", bg: "gray.100" }}
                onClick={handleLogout}
              >
                Sign out
              </MenuItem>
            </MenuList>
          </Menu>
        </Flex>
      </Flex>
    </header>
  );
};

export default Header;
