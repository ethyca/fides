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
 * Privacy Request Verification Page
 * Full-page view for OTP verification (replaces modal)
 */
const PrivacyRequestVerifyPage = async ({
  params,
  searchParams,
}: {
  params: Promise<{ actionKey: string }>;
  searchParams: NextSearchParams;
}) => {
  const { actionKey } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <AuthFormLayout
        showTitleOnDesktop
        dataTestId="privacy-request-verify-layout"
      >
        <VerificationPage actionKey={actionKey} />
      </AuthFormLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestVerifyPage;
