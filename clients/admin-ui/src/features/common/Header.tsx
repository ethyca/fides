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
  useDisclosure,
} from "@fidesui/react";
import NextLink from "next/link";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { INDEX_ROUTE } from "../../constants";
import { logout, selectUser, useLogoutMutation } from "../auth";
import FeaturesPanel from "./features/FeaturesPanel";
import { QuestionIcon, UserIcon } from "./Icon";
import Image from "./Image";

const useHeader = () => {
  const { username } = useSelector(selectUser) ?? { username: "" };
  return { username };
};

const Header: React.FC = () => {
  const { username } = useHeader();
  const [logoutMutation] = useLogoutMutation();
  const dispatch = useDispatch();

  const featuresPanelDisclosure = useDisclosure();

  const handleLogout = async () => {
    logoutMutation({})
      .unwrap()
      .then(() => dispatch(logout()));
  };

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
            <Image src="/logo.svg" width={83} height={26} alt="Fides Logo" />
          </Link>
        </NextLink>
        <Flex alignItems="center">
          {username ? (
            <Menu>
              <MenuButton
                as={Button}
                size="sm"
                variant="ghost"
                data-testid="header-menu-button"
                onDoubleClick={() => featuresPanelDisclosure.onOpen()}
              >
                <UserIcon color="gray.700" />
              </MenuButton>
              <MenuList shadow="xl">
                <Stack py={2} spacing={0} px={3}>
                  <Text fontWeight="medium">{username}</Text>
                  {/* This text should only show if actually an admin */}
                  {/* <Text fontSize="sm" color="gray.600">
                    Administrator
                  </Text> */}
                </Stack>

                <MenuDivider />
                <MenuItem
                  _focus={{ color: "complimentary.500", bg: "gray.100" }}
                  onClick={() => featuresPanelDisclosure.onOpen()}
                >
                  Features
                  <Text as="i" ml={2}>
                    Beta
                  </Text>{" "}
                </MenuItem>

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
      <FeaturesPanel {...featuresPanelDisclosure} />
    </header>
  );
};

export default Header;
