import { Flex, PageSpinner } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetSystemByFidesKeyQuery } from "~/features/system";
import EditorSection from "~/features/test-datasets/DatasetEditorSection";

// Helper functions
const getSystemId = (query: { id?: string | string[] }): string => {
  if (!query.id) {
    return "";
  }
  return Array.isArray(query.id) ? query.id[0] : query.id;
};

const TestDatasetPage: NextPage = () => {
  const router = useRouter();

  const systemId = getSystemId(router.query);

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId, {
    skip: !systemId,
  });

  const connectionConfig = system?.connection_configs?.[0];
  const connectionKey = connectionConfig?.key || "";
  const connectionType = connectionConfig?.connection_type;

  if (isLoading) {
    return (
      <Layout title="System inventory">
        <PageSpinner />
      </Layout>
    );
  }

  return (
    <Layout
      title="System inventory"
      mainProps={{
        height: "100vh",
      }}
    >
      <PageHeader
        heading="System inventory"
        breadcrumbItems={[
          { title: "System inventory", href: SYSTEM_ROUTE },
          {
            title: system?.name || "",
            href: `/systems/configure/${systemId}#integrations`,
          },
          { title: "Edit dataset" },
        ]}
      />
      <Flex align="stretch" flex="1" gap="medium" vertical>
        <EditorSection
          connectionKey={connectionKey}
          connectionType={connectionType}
        />
      </Flex>
    </Layout>
  );
};

export default TestDatasetPage;
