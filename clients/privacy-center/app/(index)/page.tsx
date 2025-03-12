"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import HomePage from "~/components/HomePage";
import LoadDataIntoProviders from "~/components/LoadDataIntoProviders";
import PageLayout from "~/components/PageLayout";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

/**
 * Renders the home page for the privacy center.
 * This is a server component that will fetch all the necessary data for the Privacy Center and
 * stores by using the LoadDataIntoProviders component.
 *
 * @returns The rendered home page.
 */
const Home = async ({ searchParams }: { searchParams: NextSearchParams }) => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });

  return (
    <LoadDataIntoProviders serverEnvironment={serverEnvironment}>
      <PageLayout>
        <HomePage />
      </PageLayout>
    </LoadDataIntoProviders>
  );
};
export default Home;
