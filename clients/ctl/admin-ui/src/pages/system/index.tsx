import { Heading, Spinner } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

import Layout from "~/features/common/Layout";
import { useGetAllSystemsQuery } from "~/features/system";
import SystemsTable from "~/features/system/SystemTable";

const useSystemsTable = () => {
  const { data, isLoading } = useGetAllSystemsQuery();

  return {
    isLoading,
    systems: data,
  };
};

const Systems: NextPage = () => {
  const { isLoading, systems } = useSystemsTable();

  return (
    <Layout title="Systems">
      <Heading mb={8} fontSize="2xl" fontWeight="semibold">
        Systems
      </Heading>
      {isLoading ? <Spinner /> : <SystemsTable systems={systems} />}
    </Layout>
  );
};

export default Systems;
