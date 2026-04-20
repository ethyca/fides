"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import PageLayout from "~/components/PageLayout";
import { PrivacyRequestMetrics } from "~/components/privacy-request-metrics/PrivacyRequestMetrics";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

const PrivacyRequestMetricsPage = async ({
  searchParams,
}: {
  searchParams: NextSearchParams;
}) => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PageLayout>
        <PrivacyRequestMetrics />
      </PageLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestMetricsPage;
