import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  LinkBox,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";

const ConfigurePrivacyRequests: NextPage = () => (
  <Layout title="Configure Privacy Requests">
    <Box mb={8}>
      <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
        <BreadcrumbItem>
          <BreadcrumbLink as={NextLink} href="/privacy-requests">
            Privacy requests
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbItem color="complimentary.500">
          <BreadcrumbLink
            as={NextLink}
            href="/privacy-requests/configure"
            isCurrentPage
          >
            Configuration
          </BreadcrumbLink>
        </BreadcrumbItem>
      </Breadcrumb>
    </Box>
    <Heading mb={5} fontSize="2xl" fontWeight="semibold">
      Configure your privacy requests
    </Heading>
    <Box
      display="flex"
      alignItems="center"
      mb={5}
      data-testid="privacy-requests-configure"
    >
      <NextLink href="/privacy-requests/configure/messaging" passHref>
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
            Configure messaging provider
          </Heading>
          Fides supports email (Mailgun & Twilio) and SMS (Twilio) server
          configurations for sending processing notices to privacy request
          subjects. Configure your settings here.
        </LinkBox>
      </NextLink>
      <NextLink href="/privacy-requests/configure/storage" passHref>
        <LinkBox
          p="5"
          borderWidth="1px"
          rounded="md"
          borderColor="gray.300"
          _hover={{ borderColor: "complimentary.500", cursor: "pointer" }}
          minHeight="100%"
        >
          <Heading mb={2} size="sm">
            Configure storage
          </Heading>
          The data produced by an access request will need to be uploaded to a
          storage destination (e.g. an S3 bucket) in order to be returned to the
          user. At least one storage destination must be configured to process
          access requests. Configure your settings here.
        </LinkBox>
      </NextLink>
    </Box>
  </Layout>
);

export default ConfigurePrivacyRequests;
