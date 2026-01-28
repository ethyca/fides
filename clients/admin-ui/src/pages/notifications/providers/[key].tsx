import { NextPage } from "next";
import { useRouter } from "next/router";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/BackButton";
import { MESSAGING_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import { EditMessagingConfiguration } from "~/features/messaging/EditMessagingConfiguration";
import { useGetMessagingConfigurationByKeyQuery } from "~/features/messaging/messaging.slice";

const EditMessagingProvider: NextPage = () => {
  const router = useRouter();
  const { key } = router.query;

  const { error } = useGetMessagingConfigurationByKeyQuery({
    key: key as string,
  });
  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage={`A problem occurred while fetching the messaging configuration for key ${key}`}
        actions={[
          {
            label: "Return to messaging providers",
            onClick: () => router.push(MESSAGING_PROVIDERS_ROUTE),
          },
        ]}
      />
    );
  }

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
