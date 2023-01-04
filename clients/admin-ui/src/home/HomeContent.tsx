import { Center, Flex, SimpleGrid, Text } from "@fidesui/react";
import Link from "next/link";
import * as React from "react";
import { useMemo } from "react";

import { useFeatures } from "~/features/common/features";

import { MODULE_CARD_ITEMS, ModuleCardKeys } from "./constants";

const DEFAULT_CARD_ITEMS = MODULE_CARD_ITEMS.filter((item) =>
  [
    ModuleCardKeys.ADD_SYSTEMS,
    ModuleCardKeys.CONFIGURE_PRIVACY_REQUESTS,
  ].includes(item.key)
);

const HomeContent: React.FC = () => {
  const COLUMNS = 3;
  const { connectionsCount, systemsCount } = useFeatures();
  const hasConnections = connectionsCount > 0;
  const hasSystems = systemsCount > 0;

  const getCardItem = (key: ModuleCardKeys) => {
    const cardItem = MODULE_CARD_ITEMS.find((item) => item.key === key);
    return cardItem;
  };

  const getCardList = useMemo(
    () => () => {
      const list = [...DEFAULT_CARD_ITEMS];
      if (hasConnections || hasSystems) {
        if (hasConnections) {
          const card = getCardItem(ModuleCardKeys.REVIEW_PRIVACY_REQUESTS);
          list.push(card!);
        }
        if (hasSystems) {
          const card = getCardItem(ModuleCardKeys.MANAGE_SYSTEMS);
          list.push(card!);
        }
      }
      return list;
    },
    [hasConnections, hasSystems]
  );

  const list = getCardList();

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
                background={item.backgroundColor}
                borderRadius="8px"
                boxShadow="base"
                flexDirection="column"
                maxH="164px"
                overflow="hidden"
                padding="16px 16px 20px 16px"
                maxW="469.33px"
                _hover={{
                  border: "1px solid",
                  borderColor: `${item.hoverBorderColor}`,
                  cursor: "pointer",
                }}
              >
                <Flex
                  alignItems="center"
                  border="2px solid"
                  borderColor={item.titleColor}
                  borderRadius="5.71714px"
                  color={item.titleColor}
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
                  color={item.nameColor}
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
                  color={item.descriptionColor}
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
