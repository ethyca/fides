"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import { getNonce } from "~/common/get-nonce";
import HomePage from "~/components/HomePage";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import PageLayout from "~/components/PageLayout";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

/**
 * Renders the home page for the privacy center.
 * This is a server component that will fetch all the necessary data for the Privacy Center and
 * stores by using the LoadServerEnvironmentIntoStores component.
 *
 * @returns The rendered home page.
 */
const Home = async ({ searchParams }: { searchParams: NextSearchParams }) => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });
  const nonce = await getNonce();

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PageLayout nonce={nonce}>
        <HomePage />
      </PageLayout>
    </LoadServerEnvironmentIntoStores>
  );
};
export default Home;
