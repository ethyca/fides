import { Box, Text } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { PrivacyNoticesTable } from "~/features/privacy-notices/PrivacyNoticesTable";

const PrivacyNoticesPage = () => (
  <FixedLayout title="Privacy notices">
    <PageHeader heading="Privacy Notices">
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        Manage the privacy notices and mechanisms that are displayed to your
        users based on their location, what information you collect about them,
        and how you use that data.
      </Text>
    </PageHeader>
    <Box data-testid="privacy-notices-page">
      <PrivacyNoticesTable />
    </Box>
  </FixedLayout>
);

export default PrivacyNoticesPage;
