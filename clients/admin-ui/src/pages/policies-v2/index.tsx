import { ChakraBox as Box, ChakraText as Text } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { PolicyV2Table } from "~/features/policy-v2/PolicyV2Table";

const PoliciesV2Page = () => (
  <FixedLayout title="Policy Engine v2">
    <PageHeader heading="Policy Engine v2">
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        Manage runtime policies that control data processing based on privacy
        declarations, consent status, and contextual attributes. Policies are
        evaluated via the /evaluate endpoint to make real-time allow/deny
        decisions.
      </Text>
    </PageHeader>
    <Box data-testid="policies-v2-page">
      <PolicyV2Table />
    </Box>
  </FixedLayout>
);

export default PoliciesV2Page;
