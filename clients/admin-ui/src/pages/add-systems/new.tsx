import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Spinner,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import React from "react";

import Layout from "~/features/common/Layout";
import { useGetAllSystemsQuery } from "~/features/system";
import SystemOptions from "~/features/system/SystemOptions";

const useNewSystemData = () => {
  const { data, isLoading } = useGetAllSystemsQuery();

  return {
    isLoading,
    systems: data,
  };
};

const NewSystem: NextPage = () => {
  const { isLoading } = useNewSystemData();

  return (
    <Layout title="Choose a system type">
      <Box display="flex" justifyContent="space-between">
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Choose a type of system
        </Heading>
        <Box mb={8}>
          <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
            <BreadcrumbItem>
              <NextLink href="/add-systems">Add systems</NextLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <NextLink href="#">Choose your system</NextLink>
            </BreadcrumbItem>
          </Breadcrumb>
        </Box>
      </Box>
      {isLoading ? <Spinner /> : <SystemOptions />}
    </Layout>
  );
};

export default NewSystem;
