"use server";

import ConsentPage from "~/components/ConsentPage";
import PageLayout from "~/components/PageLayout";

import getPrivacyCenterEnvironmentCached from "../server-utils/getPrivacyCenterEnvironment";

const Consent = async () => {
  const serverEnvironment = await getPrivacyCenterEnvironmentCached();

  return (
    <PageLayout serverEnvironment={serverEnvironment}>
      <ConsentPage />
    </PageLayout>
  );
};
export default Consent;
