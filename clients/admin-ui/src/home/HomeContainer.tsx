import { ChakraFlex as Flex } from "fidesui";
import * as React from "react";
import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";

import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";
import { ChartsPlayground } from "./components";

const HomeContainer = () => {
  const {
    flags: { alphaDashboardCharts },
  } = useFlags();
  return (
    <Layout title="Home" padded={false}>
      <Flex direction="column" gap={10} pb={6}>
        <HomeBanner />
        <HomeContent />
        {alphaDashboardCharts && <ChartsPlayground />}
      </Flex>
    </Layout>
  )
};

export default HomeContainer;
