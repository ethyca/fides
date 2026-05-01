"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import { AuthFormLayout } from "~/components/common/AuthFormLayout";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import RequestSubmittedPage from "~/components/privacy-request/RequestSubmittedPage";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

/**
 * Privacy Request Success Page for custom property paths.
 * Loads the property-specific environment using the propertyPath from the URL.
 */
const PropertyPathPrivacyRequestSuccessPage = async ({
  params,
  searchParams,
}: {
  params: Promise<{ propertyPath: string }>;
  searchParams: NextSearchParams;
}) => {
  const { propertyPath } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    propertyPath: `/${propertyPath}`,
    searchParams,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <AuthFormLayout
        className="pc-page-success"
        title="Request submitted"
        dataTestId="privacy-request-success-layout"
      >
        <RequestSubmittedPage />
      </AuthFormLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PropertyPathPrivacyRequestSuccessPage;
