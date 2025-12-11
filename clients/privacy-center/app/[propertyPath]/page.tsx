/**
 * Renders the custom property path home page.
 * This page catches any route (/something) that hasn't been caught by other pages (home, consent).
 * Properties can have custom paths (/myproperty) so we render the homepage if a property was detected from the path,
 * and we render the 404 page  if we don't have a property that matched the path.
 * @returns The rendered custom property path home page.
 *          If no property matched the path, it renders the 404 page.
 */

import { getNonce } from "~/common/get-nonce";
import HomePage from "~/components/HomePage";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import PageLayout from "~/components/PageLayout";
import { NextSearchParams } from "~/types/next";

import Custom404 from "../not-found";
import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "../server-utils";

interface PropertyPathHomePageProps {
  params: Promise<{
    propertyPath: string;
  }>;
  searchParams: NextSearchParams;
}

export const generateMetadata = getPageMetadata;

const PropertyPathHomePage = async ({
  params,
  searchParams,
}: PropertyPathHomePageProps) => {
  const { propertyPath } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    propertyPath: `/${propertyPath}`,
    searchParams,
  });
  const isPropertyFoundForPath = !!serverEnvironment.property;
  const nonce = await getNonce();

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PageLayout nonce={nonce}>
        {isPropertyFoundForPath ? <HomePage /> : <Custom404 />}
      </PageLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PropertyPathHomePage;
