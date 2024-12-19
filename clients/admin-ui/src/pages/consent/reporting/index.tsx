import { Box, Text } from "fidesui";
import React from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import ConsentReporting from "~/features/consent-reporting/ConsentReporting";

const ConsentReportingPage = () => (
  <Layout title="Consent reporting">
    <PageHeader heading="Consent reporting">
      <Text fontSize="sm" width={{ base: "100%", lg: "50%" }}>
        Download a CSV containing a report of consent preferences made by users
        on your sites. Select a date range below and click &quot;Download
        report&quot;. Depending on the number of records in the date range you
        select, it may take several minutes to prepare the file after you click
        &quot;Download report&quot;.
      </Text>
    </PageHeader>
    <Box data-testid="consent">
      <ConsentReporting />
    </Box>
  </Layout>
);

export default ConsentReportingPage;
