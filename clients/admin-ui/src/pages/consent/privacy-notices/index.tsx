import { PRIVACY_REQUESTS_ROUTE } from "@fidesui/components";
import { Box, Breadcrumb, BreadcrumbItem, Heading, Text } from "@fidesui/react";
import NextLink from "next/link";
import React from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import { PrivacyNoticesTable } from "~/features/privacy-notices/PrivacyNoticesTable";

const PrivacyNoticesPage = () => (
  <Layout title="Privacy notices">
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        Manage privacy notices
      </Heading>
      <Box>
        <Breadcrumb
          fontWeight="medium"
          fontSize="sm"
          color="gray.600"
          data-testid="breadcrumbs"
        >
          <BreadcrumbItem>
            <NextLink href={PRIVACY_REQUESTS_ROUTE}>Privacy requests</NextLink>
          </BreadcrumbItem>
          {/* TODO: Add Consent breadcrumb once the page exists */}
          <BreadcrumbItem color="complimentary.500">
            <NextLink href={PRIVACY_NOTICES_ROUTE}>Privacy notices</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
    </Box>
    <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
      Manage the privacy notices and mechanisms that are displayed to your users
      based on their location, what information you collect about them, and how
      you use that data.
    </Text>
    <Box data-testid="privacy-notices-page">
      <PrivacyNoticesTable />
    </Box>
  </Layout>
);

export default PrivacyNoticesPage;
