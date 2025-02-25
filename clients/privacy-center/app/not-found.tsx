"use server";

import NotFoundMessage from "~/components/NotFoundMessage";
import PageLayout from "~/components/PageLayout";

import getPrivacyCenterEnvironmentCached from "./server-utils/getPrivacyCenterEnvironment";

const Custom404 = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      <NotFoundMessage />
    </PageLayout>
  );
};

export default Custom404;
