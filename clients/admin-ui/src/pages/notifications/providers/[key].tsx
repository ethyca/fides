import { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/BackButton";
import { MESSAGING_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import { EditMessagingConfiguration } from "~/features/messaging/EditMessagingConfiguration";

const EditMessagingProvider: NextPage = () => {
  const router = useRouter();
  const { key } = router.query;

  if (!key || typeof key !== "string") {
    return (
      <Layout title="Edit Messaging Provider">
        <BackButton backPath={MESSAGING_PROVIDERS_ROUTE} />
        <div>Invalid messaging provider key</div>
      </Layout>
    );
  }

  return (
    <Layout title={`Edit Messaging Provider - ${key}`}>
      <BackButton backPath={MESSAGING_PROVIDERS_ROUTE} />
      <EditMessagingConfiguration configKey={key} />
    </Layout>
  );
};

export default EditMessagingProvider;
