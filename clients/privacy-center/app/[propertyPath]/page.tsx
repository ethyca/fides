/**
 * Renders the custom property path home page.
 * This page catches any route (/something) that hasn't been caught by other pages (home, consent).
 * Properties can have custom paths (/myproperty) so we render the homepage if a property was detected from the path,
 * and we render the 404 page  if we don't have a property that matched the path.
 * @returns The rendered custom property path home page.
 *          If no property matched the path, it renders the 404 page.
 */

import HomePage from "~/components/HomePage";
import PageLayout from "~/components/PageLayout";

import Custom404 from "../not-found";
import getPrivacyCenterEnvironmentCached from "../server-utils/getPrivacyCenterEnvironment";

interface PropertyPathHomePageProps {
  params: Promise<{
    propertyPath: string;
  }>;
}

const PropertyPathHomePage = async ({ params }: PropertyPathHomePageProps) => {
  const { propertyPath } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    propertyPath: `/${propertyPath}`,
  });
  const isPropertyFoundForPath = !!serverEnvironment.property;

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      {isPropertyFoundForPath ? <HomePage /> : <Custom404 />}
    </PageLayout>
  );
};

export default PropertyPathHomePage;
