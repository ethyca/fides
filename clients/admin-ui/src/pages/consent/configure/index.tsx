import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Flex,
  Heading,
  Spacer,
  Text,
} from "@fidesui/react";
import { useFeatures } from "common/features";
import NextLink from "next/link";
import React from "react";

import Layout from "~/features/common/Layout";
import { CONFIGURE_CONSENT_ROUTE } from "~/features/common/nav/v2/routes";
import AddVendor from "~/features/configure-consent/AddVendor";
import ConfigureConsent from "~/features/configure-consent/ConfigureConsent";
import { ConsentManagementTable } from "~/features/configure-consent/ConsentMangagementTable";

type Props = {
  includeAddVendors?: boolean;
  title: string;
  breadCrumbText: string;
  description: string;
};

const ConsentMetadata: React.FC<Props> = ({
  includeAddVendors,
  title,
  breadCrumbText,
  description,
}) => (
  <>
    <Box mb={4}>
      <Heading fontSize="2xl" fontWeight="semibold" mb={2} data-testid="header">
        {title}
      </Heading>
      <Box>
        <Breadcrumb
          fontWeight="medium"
          fontSize="sm"
          color="gray.600"
          data-testid="breadcrumbs"
        >
          <BreadcrumbItem>
            <NextLink href={CONFIGURE_CONSENT_ROUTE}>Consent</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem color="complimentary.500">
            <NextLink href="#">{breadCrumbText}</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
    </Box>
    <Flex>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        {description}
      </Text>
      {includeAddVendors ? (
        <>
          <Spacer />
          <AddVendor />
        </>
      ) : null}
    </Flex>
  </>
);

const ConfigureConsentPage = () => {
  const { tcf: isTcfEnabled } = useFeatures();

  if (isTcfEnabled) {
    return (
      <Layout title="Configure consent">
        <ConsentMetadata
          includeAddVendors
          title="Manage your vendors"
          breadCrumbText="Vendors"
          description="Use the table below to manage your vendors. Modify the legal basis for a vendor if permitted and view and group your views by applying different filters"
        />
        <ConsentManagementTable />
      </Layout>
    );
  }

  return (
    <Layout title="Configure consent">
      <ConsentMetadata
        title="Configure consent"
        breadCrumbText="Configure consent"
        description="Your current cookies and tracking information."
      />
      <ConfigureConsent />
    </Layout>
  );
};

export default ConfigureConsentPage;
