/**
 * Renders the custom property path home page.
 * This page catches any route (/something) that hasn't been caught by other pages (home, consent).
 * Properties can have custom paths (/myproperty) so we render the homepage if a property was detected from the path,
 * and we render the 404 page  if we don't have a property that matched the path.
 * @returns The rendered custom property path home page.
 *          If no property matched the path, it renders the 404 page.
 */

import HomePage from "~/components/HomePage";
import LoadDataIntoProviders from "~/components/LoadDataIntoProviders";
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

  return (
    <LoadDataIntoProviders serverEnvironment={serverEnvironment}>
      <PageLayout>
        {/* @ts-expect-error Async Server Component. Remove when upgraded to TypeScript 5.1.3 or higher. */}
        {isPropertyFoundForPath ? <HomePage /> : <Custom404 />}
      </PageLayout>
    </LoadDataIntoProviders>
  );
};

export default PropertyPathHomePage;
