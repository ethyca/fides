"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import HomePage from "~/components/HomePage";
import PageLayout from "~/components/PageLayout";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

const Home = async ({ searchParams }: { searchParams: NextSearchParams }) => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      <HomePage />
    </PageLayout>
  );
};
export default Home;
