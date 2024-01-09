import { Box, Heading, Link, Text } from "@fidesui/react";
import type { NextPage } from "next";

import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  DATAMAP_ROUTE,
} from "~/features/common/nav/v2/routes";
import { AddMultipleSystems } from "~/features/system/add-multiple-systems/AddMultipleSystems";

const DESCRIBE_SYSTEM_COPY =
  "Select your vendors below and they will be added as systems to your data map. Fides Compass will automatically populate the system information so that you can quickly configure privacy requests and consent. To add custom systems or unlisted vendors, please";

const Header = () => (
  <Box display="flex" mb={4} alignItems="center" data-testid="header">
    <Heading fontSize="2xl" fontWeight="semibold">
      Choose vendors
    </Heading>
  </Box>
);

const AddMultipleSystemsPage: NextPage = () => {
  const { systemOrDatamapRoute } = useSystemOrDatamapRoute();

  return (
    <Layout title="Describe your system">
      <BackButton backPath={systemOrDatamapRoute} />
      <Header />
      <Box w={{ base: "100%", md: "75%" }}>
        <Text fontSize="sm" mb={8}>
          {DESCRIBE_SYSTEM_COPY}
          <Link href={ADD_SYSTEMS_MANUAL_ROUTE} color="complimentary.500">
            {" "}
            click here.{" "}
          </Link>
        </Text>
      </Box>
      <AddMultipleSystems redirectRoute={DATAMAP_ROUTE} />
    </Layout>
  );
};

export default AddMultipleSystemsPage;
