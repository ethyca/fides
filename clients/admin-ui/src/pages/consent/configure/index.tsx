import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Text,
  Flex,
  Spacer,
} from "@fidesui/react";
import { useFeatures } from "common/features";
import NextLink from "next/link";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import Layout from "~/features/common/Layout";
import { CONFIGURE_CONSENT_ROUTE } from "~/features/common/nav/v2/routes";
import ConfigureConsent from "~/features/configure-consent/ConfigureConsent";
import { ConsentManagementTable } from "~/features/configure-consent/ConsentMangagementTable";
import AddVendor from "~/features/configure-consent/AddVendor";

const ConsentMetadata: React.FC<{ includeAddVendors?: boolean }> = ({
  includeAddVendors,
}) => (
  <>
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
            <NextLink href={CONFIGURE_CONSENT_ROUTE}>Consent</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem color="complimentary.500">
            <NextLink href="#">Configure consent</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
    </Box>
    <Flex>
      <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
        Your current cookies and tracking information.
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
      <FixedLayout
        title="Configure consent"
        mainProps={{
          padding: "40px",
          paddingRight: "48px",
        }}
      >
        <ConsentMetadata includeAddVendors />
        <ConsentManagementTable />
      </FixedLayout>
    );
  }

  return (
    <Layout title="Configure consent">
      <ConsentMetadata />
      <ConfigureConsent />
    </Layout>
  );
};

export default ConfigureConsentPage;
