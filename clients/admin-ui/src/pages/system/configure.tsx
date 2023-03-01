import { Box, Breadcrumb, BreadcrumbItem, Heading } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import EditSystemFlow from "~/features/system/EditSystemFlow";

const ConfigureSystem: NextPage = () => (
  <Layout title="Systems">
    <Heading mb={2} fontSize="2xl" fontWeight="semibold">
      Configure your system
    </Heading>
    <Box mb={8}>
      <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
        <BreadcrumbItem>
          <NextLink href="/system">System Connections</NextLink>
        </BreadcrumbItem>
        <BreadcrumbItem>
          <NextLink href="#">Configure your connection</NextLink>
        </BreadcrumbItem>
      </Breadcrumb>
    </Box>
    <EditSystemFlow />
  </Layout>
);

export default ConfigureSystem;
