import { Center, Flex, SimpleGrid, Text } from "@fidesui/react";
import Link from "next/link";
import * as React from "react";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
import { useGetUserPermissionsQuery } from "~/features/user-management";
import { ScopeRegistry } from "~/types/api";

import { MODULE_CARD_ITEMS } from "./constants";
import { configureTiles } from "./tile-config";

const HomeContent: React.FC = () => {
  const COLUMNS = 3;
  const { connectionsCount, systemsCount, plus } = useFeatures();
  const hasConnections = connectionsCount > 0;
  const hasSystems = systemsCount > 0;
  const user = useAppSelector(selectUser);
  const { data: permissions } = useGetUserPermissionsQuery(user?.id ?? "");

  const list = useMemo(
    () =>
      configureTiles({
        config: MODULE_CARD_ITEMS,
        hasPlus: plus,
        hasConnections,
        hasSystems,
        userScopes: permissions ? (permissions.scopes as ScopeRegistry[]) : [],
      }),
    [hasConnections, hasSystems, plus, permissions]
  );

  return (
    <Center px="36px">
      <SimpleGrid
        columns={list.length >= COLUMNS ? COLUMNS : list.length}
        spacing="24px"
      >
        {list
          .sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
          .map((item) => (
            <Link
              data-testid={item.name}
              href={item.href}
              key={item.key}
              passHref
            >
              <Flex
                background={`${item.color}.50`}
                borderRadius="8px"
                boxShadow="base"
                flexDirection="column"
                maxH="164px"
                overflow="hidden"
                padding="16px 16px 20px 16px"
                maxW="469.33px"
                _hover={{
                  border: "1px solid",
                  borderColor: `${item.color}.500`,
                  cursor: "pointer",
                }}
              >
                <Flex
                  alignItems="center"
                  border="2px solid"
                  borderColor={`${item.color}.300`}
                  borderRadius="5.71714px"
                  color={`${item.color}.300`}
                  fontSize="22px"
                  fontWeight="extrabold"
                  h="48px"
                  justifyContent="center"
                  lineHeight="29px"
                  w="48px"
                >
                  {item.title}
                </Flex>
                <Flex
                  color={`${item.color}.800`}
                  fontSize="16px"
                  fontWeight="semibold"
                  lineHeight="24px"
                  mt="12px"
                  mb="4px"
                >
                  {item.name}
                  &nbsp; &#8594;
                </Flex>
                <Flex
                  color="gray.500"
                  fontSize="14px"
                  h="40px"
                  lineHeight="20px"
                >
                  <Text noOfLines={2}>{item.description}</Text>
                </Flex>
              </Flex>
            </Link>
          ))}
      </SimpleGrid>
    </Center>
  );
};

export default HomeContent;
