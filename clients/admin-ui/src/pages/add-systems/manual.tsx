import { Box, Breadcrumb, BreadcrumbItem, Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import Layout from "~/features/common/Layout";
import { ADD_SYSTEMS_ROUTE } from "~/features/common/nav/v2/routes";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import { selectLockedForGVL } from "~/features/system/dictionary-form/dict-suggestion.slice";
import SystemFormTabs from "~/features/system/SystemFormTabs";
import GVLNotice from "~/features/system/GVLNotice";
import { ConnectionSystemTypeMap } from "~/types/api";

const DESCRIBE_SYSTEM_COPY =
  "Systems are anything that might store or process data in your organization, from a web application, to a database or data warehouse. Describe your system below to register it to the map. You may optionally complete data entry for the system using the additional tabs to navigate the sections.";

const Header = ({ connector }: { connector?: ConnectionSystemTypeMap }) => (
  <Box display="flex" mb={2} alignItems="center" data-testid="header">
    <ConnectionTypeLogo data={connector ?? "ethyca"} mr={2} />
    <Heading fontSize="2xl" fontWeight="semibold">
      Describe your {connector ? connector.human_readable : "new"} system
    </Heading>
  </Box>
);

const NewManualSystem: NextPage = () => {
  const { systemOrDatamapRoute } = useSystemOrDatamapRoute();
  const router = useRouter();
  const { connectorType } = router.query;

  const connector: ConnectionSystemTypeMap | undefined = useMemo(() => {
    if (!connectorType) {
      return undefined;
    }

    const value = Array.isArray(connectorType)
      ? connectorType[0]
      : connectorType;
    return JSON.parse(value);
  }, [connectorType]);

  const lockedForGVL = useAppSelector(selectLockedForGVL);

  return (
    <Layout title="Describe your system">
      <Box mb={4}>
        <Header connector={connector} />
        <Box>
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
              <NextLink href={ADD_SYSTEMS_ROUTE}>Add systems</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem color="complimentary.500">
              <NextLink href="#">Describe your system</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      {lockedForGVL ? <GVLNotice /> : null}
      <Box w={{ base: "100%", md: "75%" }}>
        <Text fontSize="sm" mb={8}>
          {DESCRIBE_SYSTEM_COPY}
        </Text>
        <SystemFormTabs isCreate />
      </Box>
    </Layout>
  );
};

export default NewManualSystem;
