import { Heading, Spinner } from "@fidesui/react";
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

const Systems: NextPage = () => {
  const { isLoading, systems } = useSystemsData();

  return (
    <Layout title="Systems">
      <Heading mb={8} fontSize="2xl" fontWeight="semibold">
        System Management
      </Heading>
      {isLoading ? <Spinner /> : <SystemsManagement systems={systems} />}
    </Layout>
  );
};

export default Systems;
