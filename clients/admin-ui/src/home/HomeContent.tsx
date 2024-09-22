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
    [plus, userScopes, flags]
  );

  return (
    <Flex paddingX={10} data-testid="home-content">
      <SimpleGrid columns={{ md: 2, xl: 3 }} spacing="24px">
        {list
          .sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
          .map((item) => (
            <NextLink href={item.href} key={item.key}>
              <Flex
                background="corinth"
                borderRadius="8px"
                maxH="164px"
                overflow="hidden"
                maxW="469.33px"
                border="1px solid"
                borderColor="neutral.200"
                _hover={{
                  border: "1px solid",
                  borderColor: "neutral.400",
                  cursor: "pointer",
                }}
                data-testid={`tile-${item.name}`}
              >
                <Flex
                  background={`${item.color}`}
                  width="8px"
                  border-top-left-radius="8px"
                  border-bottom-left-radius="8px"
                />
                <Flex flexDirection="column" padding="10px 16px 24px 16px">
                  <Flex
                    color="minos"
                    fontSize="16px"
                    fontWeight="semibold"
                    lineHeight="24px"
                    mt="12px"
                    mb="4px"
                  >
                    {item.name}
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
              </Flex>
            </NextLink>
          ))}
      </SimpleGrid>
    </Flex>
  );
};

export default HomeContent;
