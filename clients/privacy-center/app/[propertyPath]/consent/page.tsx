"use server";

import { getNonce } from "~/common/get-nonce";
import ConsentPageWrapper from "~/components/ConsentPageWrapper";
import PageLayout from "~/components/PageLayout";

/**
 * Renders the consent page for a custom property path.
 * It relies on having the config loaded into the providers by the homepage component.
 * If the config is not loaded, it will redirect to the property home path.
 */
const CustomPropertyPathConsentPage = async () => {
  const nonce = await getNonce();

  return (
    <PageLayout nonce={nonce}>
      <ConsentPageWrapper />
    </PageLayout>
  );
};

export default CustomPropertyPathConsentPage;
