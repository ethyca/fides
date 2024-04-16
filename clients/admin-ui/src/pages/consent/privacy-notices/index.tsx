import { Box, Heading, Text } from "@fidesui/react";
import React from "react";
import FixedLayout from "~/features/common/FixedLayout";

import { PrivacyNoticesTable } from "~/features/privacy-notices/PrivacyNoticesTable";

const PrivacyNoticesPage = () => (
  <FixedLayout title="Privacy notices"
    mainProps={{
      padding: "24px 40px",
    }}>
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        Manage privacy notices
      </Heading>
    </Box>
    <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
      Manage the privacy notices and mechanisms that are displayed to your users
      based on their location, what information you collect about them, and how
      you use that data.
    </Text>
    <Box data-testid="privacy-notices-page">
      <PrivacyNoticesTable />
    </Box>
  </FixedLayout>
);

export default PrivacyNoticesPage;
