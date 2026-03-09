"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import { AuthFormLayout } from "~/components/common/AuthFormLayout";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import PrivacyRequestFormPage from "~/components/privacy-request/PrivacyRequestFormPage";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

/**
 * Privacy Request Form Page for custom property paths.
 * Loads the property-specific environment using the propertyPath from the URL.
 */
const PropertyPathPrivacyRequestPage = async ({
  params,
  searchParams,
}: {
  params: Promise<{ propertyPath: string; actionKey: string }>;
  searchParams: NextSearchParams;
}) => {
  const { propertyPath, actionKey } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    propertyPath: `/${propertyPath}`,
    searchParams,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <AuthFormLayout dataTestId="privacy-request-layout">
        <PrivacyRequestFormPage actionKey={actionKey} />
      </AuthFormLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PropertyPathPrivacyRequestPage;
