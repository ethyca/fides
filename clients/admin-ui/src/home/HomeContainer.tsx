import { Flex } from "fidesui";
import * as React from "react";

import Layout from "~/features/common/Layout";

import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";

const HomeContainer = () => (
  <Layout title="Home" mainProps={{ padding: 0 }}>
    <Flex direction="column" gap={10}>
      <HomeBanner />
      <HomeContent />
    </Flex>
  </Layout>
);

export default HomeContainer;
