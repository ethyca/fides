import { AntButton, Box, Stack } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { DATASET_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import DatabaseConnectForm from "~/features/dataset/DatabaseConnectForm";
import DatasetYamlForm from "~/features/dataset/DatasetYamlForm";

const NewDataset: NextPage = () => {
  const features = useFeatures();
  const [generateMethod, setGenerateMethod] = useState<
    "yaml" | "database" | "manual" | null
  >(null);
  return (
    <Layout title="Create New Dataset" mainProps={{ paddingTop: 0 }}>
      <PageHeader
        breadcrumbs={[
          { title: "Datasets", link: DATASET_ROUTE },
          { title: "Create new" },
        ]}
      />

      <Stack spacing={8}>
        <Box>
          <AntButton
            onClick={() => setGenerateMethod("yaml")}
            ghost={generateMethod === "yaml"}
            data-testid="upload-yaml-btn"
            className="mr-2"
          >
            Upload a Dataset YAML
          </AntButton>
          <AntButton
            onClick={() => setGenerateMethod("database")}
            ghost={generateMethod === "database"}
            disabled={features.flags.dataDiscoveryAndDetection}
            className="mr-2"
            data-testid="connect-db-btn"
          >
            Connect to a database
          </AntButton>
          {features.flags.dataDiscoveryAndDetection ? (
            <QuestionTooltip label="Creating a dataset via a database connection is disabled when the 'detection & discovery' beta feature is enabled" />
          ) : null}
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
