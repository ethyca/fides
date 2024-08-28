import { Flex, SimpleGrid, Text } from "fidesui";
import NextLink from "next/link";
import * as React from "react";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { selectThisUsersScopes } from "~/features/user-management";

import { MODULE_CARD_ITEMS } from "./constants";
import { configureTiles } from "./tile-config";

const HomeContent = () => {
  const { plus, flags } = useFeatures();
  const userScopes = useAppSelector(selectThisUsersScopes);

  const list = useMemo(
    () =>
      configureTiles({
        config: MODULE_CARD_ITEMS,
        hasPlus: plus,
        userScopes,
        flags,
      }),
    [plus, userScopes, flags],
  );

  return (
    <Flex paddingX={10} data-testid="home-content">
      <SimpleGrid columns={{ md: 2, xl: 3 }} spacing="24px">
        {list
          .sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
          .map((item) => (
            <NextLink href={item.href} key={item.key}>
              <Flex
                background={`${item.color}.50`}
                borderRadius="8px"
                flexDirection="column"
                maxH="164px"
                overflow="hidden"
                padding="16px 16px 20px 16px"
                maxW="469.33px"
                border="1px solid"
                borderColor="transparent"
                _hover={{
                  border: "1px solid",
                  borderColor: `${item.color}.500`,
                  cursor: "pointer",
                }}
                data-testid={`tile-${item.name}`}
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
            </NextLink>
          ))}
      </SimpleGrid>
    </Flex>
  );
};

export default HomeContent;
