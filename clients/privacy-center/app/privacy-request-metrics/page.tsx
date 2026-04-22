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
  const [serverEnvironment, locationsData] = await Promise.all([
    getPrivacyCenterEnvironmentCached({ searchParams }),
    fetchLocationsFromApi(),
  ]);

  const locationGroups = (locationsData?.location_groups ?? [])
    .filter((g) => g.selected)
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PageLayout>
        <PrivacyRequestMetrics locationGroups={locationGroups} />
      </PageLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default PrivacyRequestMetricsPage;
