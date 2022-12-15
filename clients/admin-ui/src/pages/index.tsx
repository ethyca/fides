import type { NextPage } from "next";

import { useFeatures } from "~/features/common/features.slice";
import Layout from "~/features/common/Layout";
import PrivacyRequestsContainer from "~/features/privacy-requests/PrivacyRequestsContainer";
import HomeContainer from "~/home/HomeContainer";

const Home: NextPage = () => {
  const { navV2 } = useFeatures();

  return (
    <>
      {navV2 && (
        <Layout title="Home">
          <HomeContainer />
        </Layout>
      )}
      {!navV2 && (
        <Layout title="Privacy Requests">
          <PrivacyRequestsContainer />
        </Layout>
      )}
    </>
  );
};

export default Home;
