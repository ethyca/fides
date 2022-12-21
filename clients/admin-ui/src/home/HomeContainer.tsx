import * as React from "react";

import HomeBanner from "./HomeBanner";
import HomeContent from "./HomeContent";
import HomeLayout from "./HomeLayout";

const HomeContainer: React.FC = () => (
  <HomeLayout title="Home">
    <HomeBanner />
    <HomeContent />
  </HomeLayout>
);

export default HomeContainer;
