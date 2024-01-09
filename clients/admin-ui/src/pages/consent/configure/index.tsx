import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Flex,
  Heading,
  Text,
} from "@fidesui/react";
import NextLink from "next/link";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { CONFIGURE_CONSENT_ROUTE } from "~/features/common/nav/v2/routes";
import { ConsentManagementTable } from "~/features/configure-consent/ConsentManagementTable";

type Props = {
  title: string;
  breadCrumbText: string;
  description: string;
};

const ConsentMetadata: React.FC<Props> = ({
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
    </Flex>
  </>
);

const ConfigureConsentPage = () => (
  <FixedLayout
    title="Configure consent"
    mainProps={{
      padding: "40px",
      paddingRight: "48px",
    }}
  >
    <ConsentMetadata
      title="Manage your vendors"
      breadCrumbText="Vendors"
      description="Use the table below to manage your vendors. Modify the legal basis for a vendor if permitted and view and group your views by applying different filters"
    />
    <ConsentManagementTable />
  </FixedLayout>
);

export default ConfigureConsentPage;
