import { AntCard, AntTypography, Box, Flex, SimpleGrid } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
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
            <NextLink href={item.href} key={item.key} className="flex">
              <Box
                borderLeft={`9px solid ${item.color}`}
                borderRadius="6px"
                className="flex grow"
              >
                <AntCard
                  className="grow"
                  style={{
                    backgroundColor: palette.FIDESUI_CORINTH,
                    borderRadius: "0px 6px 6px 0px",
                    borderLeft: "none",
                  }}
                  data-testid={`tile-${item.name}`}
                >
                  <AntTypography.Title level={5}>
                    {item.name}
                  </AntTypography.Title>
                  <AntTypography.Text>{item.description}</AntTypography.Text>
                </AntCard>
              </Box>
            </NextLink>
          ))}
      </SimpleGrid>
    </Flex>
  );
};

export default HomeContent;
