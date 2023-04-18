import { PRIVACY_REQUESTS_ROUTE } from "@fidesui/components";
import { Box, Breadcrumb, BreadcrumbItem, Heading, Text } from "@fidesui/react";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/v2/routes";
import PrivacyNoticeForm from "~/features/privacy-notices/PrivacyNoticeForm";

const NewPrivacyNoticePage = () => (
  <Layout title="New privacy notice">
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        New privacy notice
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
         
          <BreadcrumbItem>
            <NextLink href={PRIVACY_NOTICES_ROUTE}>Privacy notices</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem color="complimentary.500">
            <NextLink href="#">New notice</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
    </Box>
    <Box width={{ base: "100%", lg: "70%" }}>
      <Text fontSize="sm" mb={8}>
        Configure your privacy notice including consent mechanism, associated
        data uses and the locations in which this should be displayed to users.
      </Text>
      <Box data-testid="new-privacy-notice-page">
        <PrivacyNoticeForm />
      </Box>
    </Box>
  </Layout>
);

export default NewPrivacyNoticePage;
