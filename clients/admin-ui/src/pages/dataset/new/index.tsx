import { AntButton as Button, Box, Stack } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { DATASET_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import DatabaseConnectForm from "~/features/dataset/DatabaseConnectForm";
import DatasetYamlForm from "~/features/dataset/DatasetYamlForm";

const NewDataset: NextPage = () => {
  const [generateMethod, setGenerateMethod] = useState<
    "yaml" | "database" | "manual" | null
  >(null);
  return (
    <Layout title="Create New Dataset">
      <PageHeader
        heading="Datasets"
        breadcrumbItems={[
          {
            title: "All datasets",
            href: DATASET_ROUTE,
          },
          { title: "Create new" },
        ]}
      />

      <Stack spacing={8}>
        <Box>
          <Button
            onClick={() => setGenerateMethod("yaml")}
            data-testid="upload-yaml-btn"
            className="mr-2"
          >
            Upload a Dataset YAML
          </Button>
          <Button
            onClick={() => setGenerateMethod("database")}
            ghost={generateMethod === "database"}
            className="mr-2"
            data-testid="connect-db-btn"
          >
            Connect to a database
          </Button>
        </Box>
        {generateMethod === "database" && (
          <Box w={{ base: "100%", lg: "50%" }}>
            <DatabaseConnectForm />
          </Box>
        )}
        {generateMethod === "yaml" && (
          <Box w={{ base: "100%" }}>
            <DatasetYamlForm />
          </Box>
        )}
      </Stack>
    </Layout>
  );
};

export default NewDataset;
