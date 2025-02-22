import {
  AntTypography as Typography,
  Box,
  Heading,
  LinkBox,
  LinkOverlay,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const { Text } = Typography;

const ConfigurePrivacyRequests: NextPage = () => (
  <Layout title="Configure Privacy Requests">
    <PageHeader
      heading="Privacy Requests"
      breadcrumbItems={[
        { title: "All requests", href: PRIVACY_REQUESTS_ROUTE },
        { title: "Configure requests" },
      ]}
    />

    <Text strong>Configure your privacy requests:</Text>

    <Box
      display="flex"
      alignItems="center"
      my={5}
      data-testid="privacy-requests-configure"
    >
      <LinkBox
        p="5"
        borderWidth="1px"
        rounded="md"
        borderColor="gray.300"
        _hover={{ borderColor: "complimentary.500", cursor: "pointer" }}
        mr={5}
        minHeight="100%"
      >
        <Heading mb={2} size="sm">
          <LinkOverlay
            as={NextLink}
            href="/privacy-requests/configure/messaging"
          >
            Configure messaging provider
          </LinkOverlay>
        </Heading>
        Fides supports email (Mailgun & Twilio) and SMS (Twilio) server
        configurations for sending processing notices to privacy request
        subjects. Configure your settings here.
      </LinkBox>
      <LinkBox
        p="5"
        borderWidth="1px"
        rounded="md"
        borderColor="gray.300"
        _hover={{ borderColor: "complimentary.500", cursor: "pointer" }}
        minHeight="100%"
      >
        <Heading mb={2} size="sm">
          <LinkOverlay as={NextLink} href="/privacy-requests/configure/storage">
            Configure storage
          </LinkOverlay>
        </Heading>
        The data produced by an access request will need to be uploaded to a
        storage destination (e.g. an S3 bucket) in order to be returned to the
        user. At least one storage destination must be configured to process
        access requests. Configure your settings here.
      </LinkBox>
    </Box>
  </Layout>
);

export default ConfigurePrivacyRequests;
