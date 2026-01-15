"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import { PrivacyRequestLayout } from "~/components/privacy-request/PrivacyRequestLayout";
import VerificationPageClient from "~/components/privacy-request/VerificationPageClient";
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
  params: Promise<{ actionIndex: string }>;
  searchParams: NextSearchParams;
}) => {
  const { actionIndex } = await params;
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PrivacyRequestLayout title="Enter verification code">
        <VerificationPageClient actionIndex={actionIndex} />
      </PrivacyRequestLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestVerifyPage;
