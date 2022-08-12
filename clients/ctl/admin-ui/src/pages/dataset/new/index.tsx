import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Heading,
  Stack,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import DatabaseConnectForm from "~/features/dataset/DatabaseConnectForm";
import DatasetYamlForm from "~/features/dataset/DatasetYamlForm";

const NewDataset: NextPage = () => {
  const [generateMethod, setGenerateMethod] = useState<
    "yaml" | "database" | "manual" | null
  >(null);
  return (
    <Layout title="Datasets">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Datasets
      </Heading>
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <NextLink href="/dataset">Datasets</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">Create new dataset</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
      <Stack spacing={8}>
        <Box w={{ base: "100%", lg: "50%" }}>
          <Text>
            Choose whether to upload a new dataset YAML, connect to a database
            using a connection URL or manually generate a dataset.
          </Text>
        </Box>
        <Box>
          <Button
            size="sm"
            mr={2}
            variant="outline"
            onClick={() => setGenerateMethod("yaml")}
            isActive={generateMethod === "yaml"}
            data-testid="upload-yaml-btn"
          >
            Upload a new dataset YAML
          </Button>
          <Button
            size="sm"
            mr={2}
            variant="outline"
            onClick={() => setGenerateMethod("database")}
            isActive={generateMethod === "database"}
            data-testid="connect-db-btn"
          >
            Connect a database using a connection URL
          </Button>
          <Button size="sm" variant="outline" disabled>
            Manually generate a dataset
          </Button>
        </Box>
        <Box w={{ base: "100%", lg: "50%" }}>
          {generateMethod === "yaml" ? <DatasetYamlForm /> : null}
          {generateMethod === "database" ? <DatabaseConnectForm /> : null}
        </Box>
      </Stack>
    </Layout>
  );
};

export default NewDataset;
