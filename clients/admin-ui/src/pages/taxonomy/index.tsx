import { Box, Heading, Spinner, Text } from "@fidesui/react";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy/data-categories.slice";
import TaxonomyTabs from "~/features/taxonomy/TaxonomyTabs";

const useDataCategories = () => {
  const { data, isLoading } = useGetAllDataCategoriesQuery();

  return {
    isLoading,
    dataCategories: data,
  };
};

const DataSets: NextPage = () => (
  // const { isLoading, dataCategories } = useDataCategories();

  // let content = dataCategories ? <Text> In progress </Text> : null;
  // if (isLoading) {
  //   content = <Spinner />;
  // }

  <Layout title="Datasets">
    <Heading mb={2} fontSize="2xl" fontWeight="semibold">
      Taxonomy Management
    </Heading>
    {/* TODO: get actual copy */}
    <Text mb={4}>Placeholder instruction</Text>
    <Box>
      <TaxonomyTabs />
    </Box>
  </Layout>
);
export default DataSets;
