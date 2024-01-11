import { Box, Heading, Text } from "@fidesui/react";
import React from "react";

import Layout from "~/features/common/Layout";
import ConsentReporting from "~/features/consent-reporting/ConsentReporting";

const ConsentReportingPage = () => (
  <Layout title="Configure consent">
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        Configure consent
      </Heading>
    </Box>
    <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
      Download a CSV containing a report of consent preferences made by users on
      your sites. Select a date range below and click &quot;Download
      report&quot;. Depending on the number of records in the date range you
      select, it may take several minutes to prepare the file after you click
      &quot;Download report&quot;.
    </Text>
    <Box data-testid="consent">
      <ConsentReporting />
    </Box>
  </Layout>
);

export default ConsentReportingPage;
