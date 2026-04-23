"use server";

import { buildAttributionOptions } from "~/app/server-environment";
import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import { AttributionLink } from "~/components/AttributionLink";
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
  const attribution = buildAttributionOptions(serverEnvironment.settings);

  return (
    <>
      <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
        <PageLayout>
          <PrivacyRequestMetrics />
        </PageLayout>
      </LoadServerEnvironmentIntoStores>
      {attribution && <AttributionLink attribution={attribution} />}
    </>
  );
};

export default PrivacyRequestMetricsPage;
