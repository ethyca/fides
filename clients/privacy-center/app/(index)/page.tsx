"use server";

import HomePage from "~/components/HomePage";
import PageLayout from "~/components/PageLayout";

import getPrivacyCenterEnvironmentCached from "../server-utils/getPrivacyCenterEnvironment";

const Home = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      <HomePage />
    </PageLayout>
  );
};
export default Home;
