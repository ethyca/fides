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
import { signOut, useSession } from "next-auth/react";
import React from "react";

import { QuestionIcon, UserIcon } from "./Icon";

const Header = () => {
  const { data: session } = useSession();
  // TODO: what should be displayed if there is no user name?
  const username = session?.user?.name ?? "";

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
        <NextLink href="/" passHref>
          {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
          <Link display="flex">
            <img src="/logo.svg" width={83} height={26} alt="Fidesctl Logo" />
          </Link>
        </NextLink>
        <Flex alignItems="center">
          {username ? (
            <Menu>
              <MenuButton as={Button} size="sm" variant="ghost">
                <UserIcon color="gray.700" />
              </MenuButton>

              <MenuList shadow="xl">
                <Stack px={3} py={2} spacing={0}>
                  <Text fontWeight="medium">{username}</Text>
                  <Text fontSize="sm" color="gray.600">
                    Administrator
                  </Text>
                </Stack>
                <MenuDivider />
                <MenuItem
                  px={3}
                  _focus={{ color: "complimentary.500", bg: "gray.100" }}
                  onClick={() => signOut()}
                >
                  Sign out
                </MenuItem>
              </MenuList>
            </Menu>
          ) : (
            <>
              <QuestionIcon boxSize={5} />
              <Link
                href="https://ethyca.github.io/fides/"
                isExternal
                color="gray.700"
                fontWeight="400"
              >
                Get help (Fides community)
              </Link>
            </>
          )}
        </Flex>
      </Flex>
    </header>
  );
};

export default Header;
