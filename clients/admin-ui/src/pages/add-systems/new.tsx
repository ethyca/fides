import { Box, Breadcrumb, BreadcrumbItem, Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useMemo } from "react";

import { useInterzoneNav } from "~/features/common/hooks/useInterzoneNav";
import Layout from "~/features/common/Layout";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import DescribeSystem from "~/features/system/DescribeSystem";
import SystemCatalog from "~/features/system/SystemCatalog";
import { ConnectionSystemTypeMap } from "~/types/api";

const CHOOSE_SYSTEM_COPY =
  "Systems are anything that might store or process data in your organization, from a web application, to a database or data warehouse. Pick from common system types below or create a new type of system to get started.";
const DESCRIBE_SYSTEM_COPY =
  "Systems are anything that might store or process data in your organization, from a web application, to a database or data warehouse. Describe your system below to register it to the map. You may optionally complete data entry for the system using the additional tabs to navigate the sections.";

type Step = "choose-system" | "describe-system";

const Header = ({
  step,
  connector,
}: {
  step: Step;
  connector?: ConnectionSystemTypeMap;
}) => {
  if (step === "choose-system") {
    return (
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        Choose a type of system
      </Heading>
    );
  }

  return (
    <Box display="flex" mb={2} alignItems="center" data-testid="header">
      <ConnectionTypeLogo
        data={connector ? connector.identifier : "ethyca"}
        mr={2}
      />
      <Heading fontSize="2xl" fontWeight="semibold">
        Describe your {connector ? connector.human_readable : "new"} system
      </Heading>
    </Box>
  );
};

const NewSystem: NextPage = () => {
  const { systemOrDatamapRoute } = useInterzoneNav();
  const router = useRouter();
  const { step, connectorType } = router.query;

  const currentStep: Step = step === "2" ? "describe-system" : "choose-system";
  const connector: ConnectionSystemTypeMap | undefined = useMemo(() => {
    if (!connectorType) {
      return undefined;
    }

    const value = Array.isArray(connectorType)
      ? connectorType[0]
      : connectorType;
    return JSON.parse(value);
  }, [connectorType]);

  return (
    <Layout title="Choose a system type">
      <Box mb={4}>
        <Header step={currentStep} connector={connector} />
        <Box mb={8}>
          <Breadcrumb
            fontWeight="medium"
            fontSize="sm"
            color="gray.600"
            data-testid="breadcrumbs"
          >
            <BreadcrumbItem>
              <NextLink href={systemOrDatamapRoute}>Data map</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <NextLink href="/add-systems">Add systems</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem
              color={
                currentStep === "choose-system"
                  ? "complimentary.500"
                  : undefined
              }
            >
              <NextLink href="/add-systems/new">Choose your system</NextLink>
            </BreadcrumbItem>
            {currentStep === "describe-system" ? (
              <BreadcrumbItem color="complimentary.500">
                <NextLink href="#">Describe your system</NextLink>
              </BreadcrumbItem>
            ) : null}
          </Breadcrumb>
        </Box>
        <Text fontSize="sm" w={{ base: "100%", md: "50%" }}>
          {currentStep === "choose-system"
            ? CHOOSE_SYSTEM_COPY
            : DESCRIBE_SYSTEM_COPY}
        </Text>
      </Box>
      {currentStep === "choose-system" ? <SystemCatalog /> : <DescribeSystem />}
    </Layout>
  );
};

export default NewSystem;
