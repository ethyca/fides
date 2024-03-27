import { Box, Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";
import InfoBox from "~/features/common/InfoBox";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { CONFIGURE_CONSENT_ROUTE } from "~/features/common/nav/v2/routes";
import { AddMultipleSystems } from "~/features/system/add-multiple-systems/AddMultipleSystems";

const Header = () => (
  <Box display="flex" mb={4} alignItems="center" data-testid="header">
    <Heading fontSize="2xl" fontWeight="semibold">
      Choose vendors
    </Heading>
  </Box>
);

const AddMultipleVendorsPage: NextPage = () => (
  <Layout title="Choose vendors">
    <BackButton backPath={CONFIGURE_CONSENT_ROUTE} />
    <Header />
    <Box w={{ base: "100%", md: "75%" }}>
      <Text fontSize="sm" mb={8}>
        Select your vendors below and they will be added as systems to your data
        map. Fides Compass will automatically populate the system information so
        that you can quickly configure privacy requests and consent. Note that,
        for clarity, Global Vendor List (GVL) and Google Additional Consent (AC)
        vendors will not be displayed on the "Data lineage" visualization page.
        To manage these vendors, use the "Systems & vendors" page instead.
      </Text>
    </Box>
    <AddMultipleSystems redirectRoute={CONFIGURE_CONSENT_ROUTE} />
  </Layout>
);

export default AddMultipleVendorsPage;
