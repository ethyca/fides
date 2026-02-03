import { Flex } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetSystemByFidesKeyQuery } from "~/features/system";
import EditorSection from "~/features/test-datasets/DatasetEditorSection";
import TestLogsSection from "~/features/test-datasets/TestLogsSection";
import TestResultsSection from "~/features/test-datasets/TestRunnerSection";

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

  const connectionKey = system?.connection_configs?.key || "";

  if (isLoading) {
    return (
      <Layout title="System inventory">
        <FidesSpinner />
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
          { title: "Test datasets" },
        ]}
      />
      <Flex align="stretch" flex="1" gap="middle" vertical>
        <Flex
          align="stretch"
          flex="1"
          gap="middle"
          className="max-h-[60vh] min-h-0"
        >
          <EditorSection connectionKey={connectionKey} />
          <TestResultsSection connectionKey={connectionKey} />
        </Flex>
        <Flex vertical>
          <TestLogsSection />
        </Flex>
      </Flex>
    </Layout>
  );
};

export default TestDatasetPage;
