import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Link,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";

import FixedLayout from "~/features/common/FixedLayout";
import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_ROUTE,
  DATAMAP_ROUTE,
} from "~/features/common/nav/v2/routes";
import { AddMultipleSystems } from "~/features/system/add-multiple-systems/AddMultipleSystems";

const DESCRIBE_SYSTEM_COPY =
  "Select your vendors below and they will be added as systems to your data map. Fides Compass will automatically populate the system information so that you can quickly configure privacy requests and consent. To add custom systems or unlisted vendors, please";

const Header = () => (
  <Box display="flex" mb={2} alignItems="center" data-testid="header">
    <Heading fontSize="2xl" fontWeight="semibold">
      Choose vendors
    </Heading>
  </Box>
);

const AddMultipleSystemsPage: NextPage = () => {
  const { systemOrDatamapRoute } = useSystemOrDatamapRoute();

  return (
    <FixedLayout
      title="Describe your system"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
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
              <NextLink href={systemOrDatamapRoute}>Data map</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <NextLink href={ADD_SYSTEMS_ROUTE}>Add systems</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      <Box w={{ base: "100%", md: "75%" }}>
        <Text fontSize="sm" mb={8}>
          {DESCRIBE_SYSTEM_COPY}
          <Link href={ADD_SYSTEMS_MANUAL_ROUTE} color="complimentary.500">
            {" "}
            click here.{" "}
          </Link>
        </Text>
      </Box>
      <AddMultipleSystems redirectRoute={DATAMAP_ROUTE} />
    </FixedLayout>
  );
};

export default AddMultipleSystemsPage;
