"use server";

import LoadDataIntoProviders from "~/components/LoadDataIntoProviders";
import NotFoundMessage from "~/components/NotFoundMessage";
import PageLayout from "~/components/PageLayout";

import getPrivacyCenterEnvironmentCached from "./server-utils/getPrivacyCenterEnvironment";

const Custom404 = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();

  return (
    <LoadDataIntoProviders serverEnvironment={serverEnvironment}>
      <PageLayout>
        <NotFoundMessage />
      </PageLayout>
    </LoadDataIntoProviders>
  );
};

export default Custom404;
