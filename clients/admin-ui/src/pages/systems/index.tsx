import { Spinner } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
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
    <Layout title="Systems" mainProps={{ paddingTop: 0 }}>
      <PageHeader breadcrumbs={[{ title: "Systems & vendors" }]} />
      {isLoading ? <Spinner /> : <SystemsManagement systems={systems} />}
    </Layout>
  );
};

export default Systems;
