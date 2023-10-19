import { Box, Breadcrumb, BreadcrumbItem, Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";

import FixedLayout from "~/features/common/FixedLayout";
import { AddMultipleSystems } from "~/features/system/AddMultipleSystems";
import {
  CONFIGURE_CONSENT_ROUTE,
  ADD_MULTIPLE_VENDORS_ROUTE,
} from "~/features/common/nav/v2/routes";

const DESCRIBE_VENDOR_COPY =
  "Select and add vendors. All vendors available here are from the TCF Global Vendor list, Google's AC list, and Fides Compass. All Systems come pre-configured so there is no need for your to do anything!";

const Header = () => (
  <Box display="flex" mb={2} alignItems="center" data-testid="header">
    <Heading fontSize="2xl" fontWeight="semibold">
      Add vendors
    </Heading>
  </Box>
);

const AddMultipleSystemsPage: NextPage = () => {
  return (
    <FixedLayout isDefaultLayoutPadding title="Describe your system">
      <Box mb={4}>
        <Header />
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
            <BreadcrumbItem>
              <NextLink href={ADD_MULTIPLE_VENDORS_ROUTE}>Vendors</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      <Box w={{ base: "100%", md: "75%" }}>
        <Text fontSize="sm" mb={8}>
          {DESCRIBE_VENDOR_COPY}
        </Text>
      </Box>
      <AddMultipleSystems
        isSystem={false}
        redirectRoute={CONFIGURE_CONSENT_ROUTE}
      />
    </FixedLayout>
  );
};

export default AddMultipleSystemsPage;
