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
 * Privacy Request Form Page
 * Full-page view for submitting privacy requests
 */
const PrivacyRequestPage = async ({
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
      <AuthFormLayout showTitleOnDesktop dataTestId="privacy-request-layout">
        <PrivacyRequestFormPage actionIndex={actionIndex} />
      </AuthFormLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestPage;
