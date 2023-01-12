import type { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import PrivacyRequestsContainer from "~/features/privacy-requests/PrivacyRequestsContainer";
import HomeContainer from "~/home/HomeContainer";

const Home: NextPage = () => {
  const {
    flags: { navV2 },
  } = useFeatures();

  return (
    <>
      {navV2 && <HomeContainer />}
      {!navV2 && (
        <Layout title="Privacy Requests">
          <PrivacyRequestsContainer />
        </Layout>
      )}
    </>
  );
};

export default Home;
