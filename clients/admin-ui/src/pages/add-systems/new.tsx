import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Spinner,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import React from "react";

import { useInterzoneNav } from "~/features/common/hooks/useInterzoneNav";
import Layout from "~/features/common/Layout";
import { useGetAllSystemsQuery } from "~/features/system";
import SystemCatalog from "~/features/system/SystemCatalog";

const useNewSystemData = () => {
  const { data, isLoading } = useGetAllSystemsQuery();

  return {
    isLoading,
    systems: data,
  };
};

const NewSystem: NextPage = () => {
  const { isLoading } = useNewSystemData();
  const { systemOrDatamapRoute } = useInterzoneNav();

  return (
    <Layout title="Choose a system type">
      <Box mb={4}>
        <Heading mb={2} fontSize="2xl" fontWeight="semibold">
          Choose a type of system
        </Heading>
        <Box mb={8}>
          <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
            <BreadcrumbItem>
              <NextLink href={systemOrDatamapRoute}>Data map</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <NextLink href="/add-systems">Add systems</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <NextLink href="#">Choose your system</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
        <Text fontSize="sm" w={{ base: "100%", md: "50%" }}>
          Systems are anything that might store or process data in your
          organization, from a web application, to a database or data warehouse.
          Pick from common system types below or create a new type of system to
          get started.
        </Text>
      </Box>
      {isLoading ? <Spinner /> : <SystemCatalog />}
    </Layout>
  );
};

export default NewSystem;
