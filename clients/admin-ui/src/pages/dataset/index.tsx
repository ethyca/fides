import { Box, Button, Spinner } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useGetAllFilteredDatasetsQuery } from "~/features/dataset/dataset.slice";
import DatasetsTable from "~/features/dataset/DatasetTable";

const DataSets: NextPage = () => {
  const { isLoading } = useGetAllFilteredDatasetsQuery({
    onlyUnlinkedDatasets: false,
  });

  return (
    <Layout title="Datasets" mainProps={{ paddingTop: 0 }}>
      <PageHeader breadcrumbs={[{ title: "Datasets" }]} />
      <Box mb={4}>{isLoading ? <Spinner /> : <DatasetsTable />}</Box>
      <Box>
        <Button
          as={NextLink}
          href="/dataset/new"
          size="sm"
          mr={2}
          variant="outline"
          data-testid="create-dataset-btn"
        >
          Create new dataset
        </Button>
      </Box>
    </Layout>
  );
};

export default DataSets;
