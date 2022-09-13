import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Heading,
  Spinner,
  useToast,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useSelector } from "react-redux";

import Layout from "~/features/common/Layout";
import { successToastParams } from "~/features/common/toast";
import {
  selectActiveDataset,
  useGetAllDatasetsQuery,
} from "~/features/dataset/dataset.slice";
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
  const activeDataset = useSelector(selectActiveDataset);
  const router = useRouter();
  const toast = useToast();

  const handleLoadDataset = () => {
    if (activeDataset) {
      router.push(`/dataset/${activeDataset.fides_key}`);
      toast(successToastParams("Successfully loaded dataset"));
    }
  };

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
      <Box mb={4}>
        {isLoading ? <Spinner /> : <DatasetsTable datasets={datasets} />}
      </Box>
      <Box>
        <Button
          size="sm"
          mr={2}
          variant="outline"
          data-testid="create-dataset-btn"
        >
          <NextLink href="/dataset/new">Create new dataset</NextLink>
        </Button>
        <Button
          size="sm"
          colorScheme="primary"
          disabled={!activeDataset}
          onClick={handleLoadDataset}
          data-testid="load-dataset-btn"
        >
          Load dataset
        </Button>
      </Box>
    </Layout>
  );
};

export default DataSets;
