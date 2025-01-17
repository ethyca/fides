import { Flex, SimpleGrid } from "fidesui";
import NextLink from "next/link";
import * as React from "react";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import CalloutNavCard from "~/features/common/CalloutNavCard";
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
            <NextLink href={item.href} key={item.key} className="flex">
              <CalloutNavCard
                title={item.name}
                description={item.description}
                color={item.color}
              />
            </NextLink>
          ))}
      </SimpleGrid>
    </Flex>
  );
};

export default HomeContent;
