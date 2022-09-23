import { Box, Button, Heading, Spinner } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import React from "react";

import Layout from "~/features/common/Layout";
import { useGetAllSystemsQuery } from "~/features/system";
import SystemsManagement from "~/features/system/SystemsManagement";

const useSystemsData = () => {
  const { data, isLoading } = useGetAllSystemsQuery();

  return {
    isLoading,
    systems: data,
  };
};

const Systems: NextPage = () => {
  const { isLoading, systems } = useSystemsData();

  return (
    <Layout title="Systems">
      <Box display="flex" justifyContent="space-between">
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          System Management
        </Heading>
        <Button
          size="sm"
          colorScheme="primary"
          mr={2}
          data-testid="create-system-btn"
        >
          <NextLink href="/system/new">Create New System</NextLink>
        </Button>
      </Box>
      {isLoading ? <Spinner /> : <SystemsManagement systems={systems} />}
    </Layout>
  );
};

export default Systems;
