import { AntLink as LinkText, Box, Text } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_ROUTE,
  DATAMAP_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { AddMultipleSystems } from "~/features/system/add-multiple-systems/AddMultipleSystems";

const DESCRIBE_SYSTEM_COPY =
  "Select your vendors below and they will be added as systems to your data map. Fides Compass will automatically populate the system information so that you can quickly configure privacy requests and consent. Add custom systems or unlisted vendors on the ";

const AddMultipleSystemsPage: NextPage = () => (
  <Layout title="Choose vendors">
    <PageHeader
      heading="Add systems"
      breadcrumbItems={[
        {
          title: "Add systems",
          href: ADD_SYSTEMS_ROUTE,
        },
        { title: "Choose vendors" },
      ]}
    />
    <Box w={{ base: "100%", md: "75%" }}>
      <Text fontSize="sm" mb={8}>
        {DESCRIBE_SYSTEM_COPY}
        <NextLink href={ADD_SYSTEMS_MANUAL_ROUTE} passHref legacyBehavior>
          <LinkText>Add a system</LinkText>
        </NextLink>{" "}
        page.
      </Text>
    </Box>
    <AddMultipleSystems redirectRoute={DATAMAP_ROUTE} />
  </Layout>
);

export default AddMultipleSystemsPage;
