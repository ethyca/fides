import { Box, Heading, Spinner } from "@fidesui/react";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy/data-categories.slice";
import DataCategoryChecklist from "~/features/taxonomy/DataCategoryChecklist";

const useDataCategories = () => {
  const { data, isLoading } = useGetAllDataCategoriesQuery();

  return {
    isLoading,
    dataCategories: data,
  };
};

const DataSets: NextPage = () => {
  const { isLoading, dataCategories } = useDataCategories();

  return (
    <Layout title="Datasets">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Taxonomy
      </Heading>
      <Box mb={4}>
        {isLoading ? (
          <Spinner />
        ) : (
          dataCategories && (
            <DataCategoryChecklist dataCategories={dataCategories} />
          )
        )}
      </Box>
    </Layout>
  );
};

export default DataSets;
