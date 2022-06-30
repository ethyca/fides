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
        <Box w={["100%", "100%", "50%"]}>
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
          >
            Upload a new dataset YAML
          </Button>
          <Button size="sm" mr={2} variant="outline">
            Connect a database using a connection URL
          </Button>
          <Button size="sm" variant="outline" disabled>
            Manually generate a dataset
          </Button>
        </Box>
        <Box w={["100%", "100%", "50%"]}>
          {generateMethod === "yaml" ? <DatasetYamlForm /> : null}
        </Box>
      </Stack>
    </Layout>
  );
};

export default NewDataset;
