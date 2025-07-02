"use server";

import getPrivacyCenterEnvironmentCached from "~/app/server-utils/getPrivacyCenterEnvironment";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import { NextSearchParams } from "~/types/next";

import ExternalTasksClient from "./ExternalTasksClient";

/**
 * Server component wrapper for the external manual tasks page.
 * Follows the same pattern as the homepage - loads server environment and passes to client component.
 */
const ExternalTasksPage = async ({
  searchParams,
}: {
  searchParams: NextSearchParams;
}) => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached({
    searchParams,
  });

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <ExternalTasksClient searchParams={searchParams} />
    </LoadServerEnvironmentIntoStores>
  );
};

export default ExternalTasksPage;
