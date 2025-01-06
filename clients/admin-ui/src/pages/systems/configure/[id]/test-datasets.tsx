import { HStack } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";
import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";
import EditorSection from "~/features/test-datasets/DatasetEditorSection";
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
  const dispatch = useAppDispatch();

  const systemId = getSystemId(router.query);

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId, {
    skip: !systemId,
  });

  const connectionKey = system?.connection_configs?.key || "";

  useEffect(() => {
    dispatch(setActiveSystem(system));
  }, [system, dispatch]);

  if (isLoading) {
    return (
      <Layout title="Systems">
        <FidesSpinner />
      </Layout>
    );
  }

  return (
    <Layout
      title="System inventory"
      mainProps={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
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
      <HStack
        alignItems="stretch"
        flex="1"
        minHeight="0"
        spacing="4"
        padding="4 4 4 0"
      >
        <EditorSection connectionKey={connectionKey} />
        <TestResultsSection connectionKey={connectionKey} />
      </HStack>
    </Layout>
  );
};

export default TestDatasetPage;
