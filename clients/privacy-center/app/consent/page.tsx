import { getNonce } from "~/common/get-nonce";
import { ConfigGate } from "~/components/common/ConfigGate";
import ConsentPage from "~/components/ConsentPage";
import PageLayout from "~/components/PageLayout";

const Consent = async () => {
  const nonce = await getNonce();

  return (
    <ConfigGate>
      <PageLayout nonce={nonce}>
        <ConsentPage />
      </PageLayout>
    </ConfigGate>
  );
};

export default Consent;
