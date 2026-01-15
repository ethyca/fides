"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import { PrivacyRequestLayout } from "~/components/privacy-request/PrivacyRequestLayout";
import PrivacyRequestFormPageClient from "~/components/privacy-request/PrivacyRequestFormPageClient";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

/**
 * Privacy Request Form Page
 * Full-page view for submitting privacy requests (replaces modal)
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
      <PrivacyRequestLayout>
        <PrivacyRequestFormPageClient
          actionIndex={actionIndex}
          searchParams={searchParams}
        />
      </PrivacyRequestLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestPage;
