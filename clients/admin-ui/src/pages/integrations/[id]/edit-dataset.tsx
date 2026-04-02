import { Flex, PageSpinner } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import EditorSection from "~/features/test-datasets/DatasetEditorSection";

const EditDatasetPage: NextPage = () => {
  const router = useRouter();
  const connectionKey = router.query.id as string;

  const { data: connection, isLoading } = useGetDatastoreConnectionByKeyQuery(
    connectionKey,
    {
      skip: !connectionKey,
    },
  );

  if (isLoading) {
    return (
      <Layout title="Integrations">
        <PageSpinner />
      </Layout>
    );
  }

  return (
    <Layout
      title="Integrations"
      mainProps={{
        height: "100vh",
      }}
    >
      <PageHeader
        heading="Integrations"
        breadcrumbItems={[
          {
            title: "All integrations",
            href: INTEGRATION_MANAGEMENT_ROUTE,
          },
          {
            title: connection?.name || connectionKey,
            href: `${INTEGRATION_MANAGEMENT_ROUTE}/${connectionKey}`,
          },
          { title: "Edit dataset" },
        ]}
      />
      <Flex align="stretch" flex="1" gap="medium" vertical>
        <EditorSection
          connectionKey={connectionKey}
          connectionType={connection?.connection_type}
        />
      </Flex>
    </Layout>
  );
};

export default EditDatasetPage;
