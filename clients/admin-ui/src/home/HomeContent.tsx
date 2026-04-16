import { Col, Flex, Row } from "fidesui";
import * as React from "react";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import CalloutNavCard from "~/features/common/CalloutNavCard";
import { useFeatures } from "~/features/common/features";
import { RouterLink } from "~/features/common/nav/RouterLink";
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
    <Flex className="px-10" data-testid="home-content">
      <Row gutter={[24, 24]} className="w-full">
        {list
          .sort((a, b) => (a.sortOrder > b.sortOrder ? 1 : -1))
          .map((item) => (
            <Col key={item.key} xs={24} md={12} xl={8}>
              <RouterLink unstyled href={item.href} className="flex h-full">
                <CalloutNavCard
                  title={item.name}
                  description={item.description}
                  color={item.color}
                />
              </RouterLink>
            </Col>
          ))}
      </Row>
    </Flex>
  );
};

export default HomeContent;
