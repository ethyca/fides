"use server";

import { notFound } from "next/navigation";

import { buildAttributionOptions } from "~/app/server-environment";
import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import loadEnvironmentVariables from "~/app/server-utils/loadEnvironmentVariables";
import { AttributionLink } from "~/components/AttributionLink";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import PageLayout from "~/components/PageLayout";
import { PrivacyRequestMetrics } from "~/components/privacy-request-metrics/PrivacyRequestMetrics";
import { NextSearchParams } from "~/types/next";

export const generateMetadata = getPageMetadata;

const PropertyPathPrivacyRequestMetricsPage = async ({
  searchParams,
}: {
  searchParams: NextSearchParams;
}) => {
  const envVariables = loadEnvironmentVariables();
  if (!envVariables.PRIVACY_REQUEST_DISCLOSURE_ENABLED) {
    notFound();
  }

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

export default PropertyPathPrivacyRequestMetricsPage;
