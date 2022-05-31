import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Heading,
  Spinner,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useSelector } from "react-redux";

import Layout from "~/features/common/Layout";
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

  const handleLoadDataset = () => {
    // use the router to let the page know we loaded the dataset from this view
    // this allows us to display a Success toast message, which we would not want to display
    // if just navigating directly to the page via URL
    // the second URL to `push` allows us to hide the query parameter from the URL the user sees
    if (activeDataset) {
      router.push(
        `/dataset/${activeDataset.fides_key}/?fromLoad=1`,
        `/dataset/${activeDataset.fides_key}`
      );
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
        <Button size="sm" mr={2} variant="outline">
          Create new dataset
        </Button>
        <Button
          size="sm"
          variant="outline"
          // TODO: need a primary color scheme with a dark background?
          colorScheme="complimentary"
          disabled={!activeDataset}
          onClick={handleLoadDataset}
        >
          Load dataset
        </Button>
      </Box>
    </Layout>
  );
};

export default DataSets;
