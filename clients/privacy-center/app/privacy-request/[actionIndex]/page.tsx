"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import PrivacyRequestFormPage from "~/components/privacy-request/PrivacyRequestFormPage";
import { PrivacyRequestLayout } from "~/components/privacy-request/PrivacyRequestLayout";
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
        <PrivacyRequestFormPage actionIndex={actionIndex} />
      </PrivacyRequestLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestPage;
