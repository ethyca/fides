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

import { useFeatures } from "~/features/common/features.slice";
import Layout from "~/features/common/Layout";
import { useCreateSystemsFromScanMutation } from "~/features/common/plus.slice";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import SystemYamlForm from "~/features/system/SystemYamlForm";

const NewSystem: NextPage = () => {
  const [showYamlForm, setShowYamlForm] = useState(false);
  const { systemScanning: systemScanningEnabled } = useFeatures();
  const [scanMutation, { isLoading: isScanning }] =
    useCreateSystemsFromScanMutation();

  const startScan = async () => {
    const result = await scanMutation(DEFAULT_ORGANIZATION_FIDES_KEY);
    console.log({ result });
  };

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
            onClick={() => setShowYamlForm(true)}
            isActive={showYamlForm}
            data-testid="upload-yaml-btn"
          >
            Upload a new system YAML
          </Button>
          <Button
            size="sm"
            mr={2}
            variant="outline"
            data-testid="manually-generate-btn"
          >
            <NextLink href="/system/new/configure">
              Manually generate a system
            </NextLink>
          </Button>
          {systemScanningEnabled ? (
            <Button
              size="sm"
              mr={2}
              variant="outline"
              onClick={startScan}
              data-testid="scan-btn"
              isLoading={isScanning}
            >
              Scan for systems
            </Button>
          ) : null}
        </Box>
        <Box w={{ base: "100%", lg: "50%" }}>
          {showYamlForm ? <SystemYamlForm /> : null}
        </Box>
      </Stack>
    </Layout>
  );
};

export default NewSystem;
