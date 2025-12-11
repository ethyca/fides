"use server";

import { getNonce } from "~/common/get-nonce";
import LoadServerEnvironmentIntoStores from "~/components/LoadServerEnvironmentIntoStores";
import NotFoundMessage from "~/components/NotFoundMessage";
import PageLayout from "~/components/PageLayout";

import getPrivacyCenterEnvironmentCached from "./server-utils/getPrivacyCenterEnvironment";

const Custom404 = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();
  const nonce = await getNonce();

  return (
    <LoadServerEnvironmentIntoStores serverEnvironment={serverEnvironment}>
      <PageLayout nonce={nonce}>
        <NotFoundMessage />
      </PageLayout>
    </LoadServerEnvironmentIntoStores>
  );
};

export default Custom404;
