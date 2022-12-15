import { Box, Flex } from "@fidesui/react";
import * as React from "react";

import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";

const HomeContainer: React.FC = () => (
  <Flex flexDirection="column" gap="40px" py="40px">
    <HomeBanner />
    <Box px="36px">
      <HomeContent />
    </Box>
  </Flex>
);

export default HomeContainer;
