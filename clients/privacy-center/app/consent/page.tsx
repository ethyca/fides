"use server";

import ConsentPage from "~/components/ConsentPage";
import PageLayout from "~/components/PageLayout";

import getPageMetadata from "../server-utils/getPageMetadata";
import getPrivacyCenterEnvironmentCached from "../server-utils/getPrivacyCenterEnvironment";

export const generateMetadata = getPageMetadata;

const Consent = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      <ConsentPage />
    </PageLayout>
  );
};
export default Consent;
