"use server";

import {
  getPageMetadata,
  getPrivacyCenterEnvironmentCached,
} from "~/app/server-utils";
import fetchLocationsFromApi from "~/app/server-utils/fetchLocationsFromApi";
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
  const [serverEnvironment, locationOptions] = await Promise.all([
    getPrivacyCenterEnvironmentCached({ searchParams }),
    fetchLocationsFromApi(),
  ]);

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PageLayout>
        <PrivacyRequestMetrics
          locationOptions={locationOptions}
          currentGeo={serverEnvironment.location?.location}
        />
      </PageLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestMetricsPage;
