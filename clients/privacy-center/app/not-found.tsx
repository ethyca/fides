"use server";

import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import NotFoundMessage from "~/components/NotFoundMessage";
import PageLayout from "~/components/PageLayout";

import getPrivacyCenterEnvironmentCached from "./server-utils/getPrivacyCenterEnvironment";

const Custom404 = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PageLayout>
        <NotFoundMessage />
      </PageLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default Custom404;
