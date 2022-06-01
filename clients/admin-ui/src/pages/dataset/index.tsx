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
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Datasets
      </Heading>
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <NextLink href="/dataset">Datasets</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">Select dataset</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
      {isLoading ? <Spinner /> : <DatasetsTable datasets={datasets} />}
    </Layout>
  );
};

export default DataSets;
