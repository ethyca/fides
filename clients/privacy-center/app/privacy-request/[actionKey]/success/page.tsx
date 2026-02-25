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
 * Privacy Request Success Page
 * Full-page view showing request submitted confirmation
 */
const PrivacyRequestSuccessPage = async ({
  searchParams,
}: {
  searchParams: NextSearchParams;
}) => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <AuthFormLayout
        showTitleOnDesktop
        title="Request submitted"
        dataTestId="privacy-request-success-layout"
      >
        <RequestSubmittedPage />
      </AuthFormLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestSuccessPage;
