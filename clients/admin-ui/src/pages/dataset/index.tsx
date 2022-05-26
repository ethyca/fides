import { Heading, Spinner } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

import Layout from "~/features/common/Layout";
import { useGetAllDatasetsQuery } from "~/features/dataset/dataset.slice";
import DatasetsTable from "~/features/dataset/DatasetTable";

const useDatasetsTable = () => {
  const { data, isLoading } = useGetAllDatasetsQuery();

  return {
    isLoading,
    datasets: data,
  };
};

const DataSets: NextPage = () => {
  const { isLoading, datasets } = useDatasetsTable();

  return (
    <Layout title="Datasets">
      <Heading mb={8} fontSize="2xl" fontWeight="semibold">
        Datasets
      </Heading>
      {isLoading ? <Spinner /> : <DatasetsTable datasets={datasets} />}
    </Layout>
  );
};

export default DataSets;
