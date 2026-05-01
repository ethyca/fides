"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import { AuthFormLayout } from "~/components/common/AuthFormLayout";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import VerificationPage from "~/components/privacy-request/VerificationPage";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

/**
 * Privacy Request Verification Page for custom property paths.
 * Loads the property-specific environment using the propertyPath from the URL.
 */
const PropertyPathPrivacyRequestVerifyPage = async ({
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
      <AuthFormLayout
        className="pc-page-verify"
        dataTestId="privacy-request-verify-layout"
      >
        <VerificationPage actionKey={actionKey} />
      </AuthFormLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PropertyPathPrivacyRequestVerifyPage;
