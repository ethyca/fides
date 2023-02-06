import { Box, Heading, Spinner } from "@fidesui/react";
import type { NextPage } from "next";
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

const NewSystem: NextPage = () => {
  const { isLoading, systems } = useSystemsData();

  return (
    <Layout title="Choose a system type">
      <Box display="flex" justifyContent="space-between">
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Choose a type of system
        </Heading>
      </Box>
      {isLoading ? <Spinner /> : <SystemsManagement systems={systems} />}
    </Layout>
  );
};

export default NewSystem;
