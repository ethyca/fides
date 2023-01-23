import { Box, Breadcrumb, BreadcrumbItem, Heading } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";

const ConfigurePrivacyRequests: NextPage = () => (
  <Layout title="Configure Privacy Requests">
    <Box mb={8}>
      <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
        <BreadcrumbItem>
          <NextLink href="/privacy-requests">Privacy requests</NextLink>
        </BreadcrumbItem>
        <BreadcrumbItem>
          <NextLink href="/privacy-requests/configure">Configuration</NextLink>
        </BreadcrumbItem>
      </Breadcrumb>
    </Box>
    <Heading mb={2} fontSize="2xl" fontWeight="semibold">
      Configure your privacy requests
    </Heading>
    <Box>
      <Heading size="sm">Configure messaging provider</Heading>
      Fides supports email (Mailgun & Twillio) and SMS (Twillio) server
      configurations for sending processing notices to privacy request subjects.
      You'll need to set up config variables to send out messages from Fides.
      Configure your settings here.
    </Box>
    <Box>
      <Heading size="sm">Configure storage</Heading>
      The data produced by an access request will need to be uploaded to a
      storage destination (e.g. an S3 bucket) in order to be returned to the
      user. At least one storage destination must be configured to process
      access requests. Configure your settings here.
    </Box>
  </Layout>
);

export default ConfigurePrivacyRequests;
