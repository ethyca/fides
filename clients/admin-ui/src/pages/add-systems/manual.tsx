import { Box, Heading, Text } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import DataTabs from "~/features/common/DataTabs";
import Layout from "~/features/common/Layout";
import { ADD_SYSTEMS_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import { selectLockedForGVL } from "~/features/system/dictionary-form/dict-suggestion.slice";
import GVLNotice from "~/features/system/GVLNotice";
import useSystemFormTabs from "~/features/system/hooks/useSystemFormTabs";
import { ConnectionSystemTypeMap } from "~/types/api";

const DESCRIBE_SYSTEM_COPY =
  "Systems are anything that might store or process data in your organization, from a web application, to a database or data warehouse. Describe your system below to register it to the map. You may optionally complete data entry for the system using the additional tabs to navigate the sections.";

const Header = ({ connector }: { connector?: ConnectionSystemTypeMap }) => (
  <Box display="flex" mb={4} alignItems="center" data-testid="header">
    <ConnectionTypeLogo data={connector ?? "ethyca"} mr={2} />
    <Heading fontSize="md">
      Describe your {connector ? connector.human_readable : "new"} system
    </Heading>
  </Box>
);

const NewManualSystem: NextPage = () => {
  const router = useRouter();
  const { connectorType } = router.query;

  const { tabData, tabIndex, onTabChange } = useSystemFormTabs({
    isCreate: true,
  });

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
      <PageHeader
        heading="Add systems"
        breadcrumbItems={[
          {
            title: "Add systems",
            href: ADD_SYSTEMS_ROUTE,
          },
          { title: "New system" },
        ]}
      />
      <Header connector={connector} />

      {lockedForGVL ? <GVLNotice /> : null}
      <Box w={{ base: "100%", md: "75%" }}>
        <Text fontSize="sm" mb={8}>
          {DESCRIBE_SYSTEM_COPY}
        </Text>
        <DataTabs
          data={tabData}
          data-testid="system-tabs"
          index={tabIndex}
          isLazy
          isManual
          onChange={onTabChange}
        />
      </Box>
    </Layout>
  );
};

export default NewManualSystem;
