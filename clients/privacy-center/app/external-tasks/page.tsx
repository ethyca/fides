"use server";

import { notFound } from "next/navigation";

import getPrivacyCenterEnvironmentCached from "~/app/server-utils/getPrivacyCenterEnvironment";
import loadEnvironmentVariables from "~/app/server-utils/loadEnvironmentVariables";
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
  // Check if external task portal is enabled
  const envVariables = loadEnvironmentVariables();
  if (!envVariables.ENABLE_EXTERNAL_TASK_PORTAL) {
    notFound();
  }

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
