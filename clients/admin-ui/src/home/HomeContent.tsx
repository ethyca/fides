import { Col, Flex, Row } from "fidesui";
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
    <Flex style={{ paddingInline: 40 }} data-testid="home-content">
      <Row gutter={[24, 24]} style={{ width: "100%" }}>
        {list
          .sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
          .map((item) => (
            <Col key={item.key} xs={24} md={12} xl={8}>
              <NextLink href={item.href} className="flex h-full">
                <CalloutNavCard
                  title={item.name}
                  description={item.description}
                  color={item.color}
                />
              </NextLink>
            </Col>
          ))}
      </Row>
    </Flex>
  );
};

export default HomeContent;
