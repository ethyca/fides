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
import SystemYamlForm from "~/features/system/SystemYamlForm";

const NewSystem: NextPage = () => {
  const [generateMethod, setGenerateMethod] = useState<
    "yaml" | "manual" | null
  >(null);
  return (
    <Layout title="Systems">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Create a new system
      </Heading>
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <NextLink href="/system">System Connections</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">Create a new system</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
      <Stack spacing={8}>
        <Box w={{ base: "100%", lg: "50%" }}>
          <Text>
            Choose whether to upload a new system YAML or manually generate a
            system.
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
            Upload a new system YAML
          </Button>
          <Button size="sm" variant="outline">
            Manually generate a system
          </Button>
        </Box>
        <Box w={{ base: "100%", lg: "50%" }}>
          {generateMethod === "yaml" ? <SystemYamlForm /> : null}
        </Box>
      </Stack>
    </Layout>
  );
};

export default NewSystem;
