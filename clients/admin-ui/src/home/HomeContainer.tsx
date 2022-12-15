import { Flex } from "@fidesui/react";
import * as React from "react";

import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";

const HomeContainer: React.FC = () => (
  <Flex flexDirection="column" gap="40px" marginX={-9}>
    <HomeBanner />
    <HomeContent />
  </Flex>
);

export default HomeContainer;
