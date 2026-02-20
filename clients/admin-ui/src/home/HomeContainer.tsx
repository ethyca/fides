import { ChakraFlex as Flex } from "fidesui";

import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";

import { ChartsPlayground } from "./components";
import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";

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
  );
};

export default HomeContainer;
