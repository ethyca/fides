import { Center, Flex, SimpleGrid, Text } from "@fidesui/react";
import Link from "next/link";
import * as React from "react";
import { useEffect, useState } from "react";

import { useFeatures } from "~/features/common/features.slice";

import { MODULE_CARD_ITEMS,ModuleCardKeys } from "./constants";
import { ModuleCard } from "./types";

const HomeContent: React.FC = () => {
  const [list, setList] = useState<ModuleCard[]>(
    MODULE_CARD_ITEMS.filter((item) =>
      [
        ModuleCardKeys.ADD_SYSTEMS,
        ModuleCardKeys.CONFIGURE_PRIVACY_REQUESTS,
      ].includes(item.key)
    )
  );
  const { connectionsCount, systemsCount } = useFeatures();
  const COLUMNS = 3;
  const MIN_COUNT = 0;

  useEffect(() => {
    if (connectionsCount > MIN_COUNT || systemsCount > MIN_COUNT) {
      let card: ModuleCard | undefined;
      if (connectionsCount > MIN_COUNT) {
        card = MODULE_CARD_ITEMS.find(
          (item) => item.key === ModuleCardKeys.REVIEW_PRIVACY_REQUESTS
        );
      }
      if (systemsCount > MIN_COUNT) {
        card = MODULE_CARD_ITEMS.find(
          (item) => item.key === ModuleCardKeys.MANAGE_SYSTEMS
        );
      }
      setList((prev) => [...prev, card as ModuleCard]);
    }
  }, [connectionsCount, systemsCount]);

  return (
    <Center>
      <SimpleGrid
        columns={list.length >= COLUMNS ? COLUMNS : list.length}
        spacing="24px"
      >
        {list
          .sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
          .map((item) => (
            <Link href={item.href} key={item.key} passHref>
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
                  boxShadow:
                    "0px 10px 15px -3px rgba(0, 0, 0, 0.1), 0px 4px 6px -2px rgba(0, 0, 0, 0.05)",
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
