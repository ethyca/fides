import {
  ChakraBox as Box,
  ChakraHeading as Heading,
  Typography,
} from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { RouterLink } from "~/features/common/nav/RouterLink";
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
      <RouterLink
        unstyled
        href="/privacy-requests/configure/messaging"
        className="mr-5 block min-h-full rounded-md border border-gray-300 p-5 hover:cursor-pointer hover:border-[var(--fidesui-color-primary)]"
      >
        <Heading mb={2} size="sm">
          Configure messaging provider
        </Heading>
        Fides supports email (Mailgun & Twilio) and SMS (Twilio) server
        configurations for sending processing notices to privacy request
        subjects. Configure your settings here.
      </RouterLink>
      <RouterLink
        unstyled
        href="/privacy-requests/configure/storage"
        className="block min-h-full rounded-md border border-gray-300 p-5 hover:cursor-pointer hover:border-[var(--fidesui-color-primary)]"
      >
        <Heading mb={2} size="sm">
          Configure storage
        </Heading>
        The data produced by an access request will need to be uploaded to a
        storage destination (e.g. an S3 bucket) in order to be returned to the
        user. At least one storage destination must be configured to process
        access requests. Configure your settings here.
      </RouterLink>
    </Box>
  </Layout>
);

export default ConfigurePrivacyRequests;
