import { Flex } from "fidesui";
import * as React from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";

import DashboardContent from "./DashboardContent";
import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";

const HomeContainer = () => {
  const { flags } = useFeatures();
  const showDashboardInsights = flags.alphaDashboardInsights;

  return (
    <Layout title="Home" padded={false}>
      <Flex direction="column" gap={10} pb={6}>
        {showDashboardInsights ? (
          <DashboardContent />
        ) : (
          <>
            <HomeBanner />
            <HomeContent />
          </>
        )}
      </Flex>
    </Layout>
  );
};

export default HomeContainer;
