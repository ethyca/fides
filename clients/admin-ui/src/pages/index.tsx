import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PrivacyRequestsContainer from "~/features/privacy-requests/PrivacyRequestsContainer";
import HomeContainer from "~/home/HomeContainer";

const Home: NextPage = () => {
  const navBar2 = true;

  return (
    <>
      {navBar2 && (
        <Layout noPadding title="Home">
          <HomeContainer />
        </Layout>
      )}
      {!navBar2 && (
        <Layout title="Privacy Requests">
          <PrivacyRequestsContainer />
        </Layout>
      )}
    </>
  );
};

export default Home;
