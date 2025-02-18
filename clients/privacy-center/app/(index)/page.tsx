"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import HomePage from "~/components/HomePage";
import PageLayout from "~/components/PageLayout";

export const generateMetadata = getPageMetadata;

const Home = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      <HomePage />
    </PageLayout>
  );
};
export default Home;
