"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import { PrivacyRequestLayout } from "~/components/privacy-request/PrivacyRequestLayout";
import RequestSubmittedPage from "~/components/privacy-request/RequestSubmittedPage";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

/**
 * Privacy Request Success Page
 * Full-page view showing request submitted confirmation
 */
const PrivacyRequestSuccessPage = async ({
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
      <PrivacyRequestLayout title="Request submitted">
        <RequestSubmittedPage />
      </PrivacyRequestLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestSuccessPage;
