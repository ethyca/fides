import { Box, Breadcrumb, BreadcrumbItem, Heading, Text } from "@fidesui/react";
import NextLink from "next/link";
import React from "react";

import Layout from "~/features/common/Layout";
import { CONSENT_REPORTING_ROUTE } from "~/features/common/nav/v2/routes";
import ConsentReporting from "~/features/consent-reporting/ConsentReporting";

const ConsentReportingPage = () => (
  <Layout title="Configure consent">
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        Configure consent
      </Heading>
      <Box>
        <Breadcrumb
          fontWeight="medium"
          fontSize="sm"
          color="gray.600"
          data-testid="breadcrumbs"
        >
          <BreadcrumbItem>
            <NextLink href={CONSENT_REPORTING_ROUTE}>Consent</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem color="complimentary.500">
            <NextLink href="#">Reporting</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
    </Box>
    <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
      [DRAFT COPY] You can download a detailed consent report consisting of XXX.
      To download a consent report, simply set your &quot;from&quot; and
      &quot;to&quot; dates below, then hit the download button.
    </Text>
    <Box data-testid="consent">
      <ConsentReporting />
    </Box>
  </Layout>
);

export default ConsentReportingPage;
