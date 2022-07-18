import { Heading, Text } from "@fidesui/react";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import TaxonomyTabs from "~/features/taxonomy/TaxonomyTabs";

const DataSets: NextPage = () => (
  <Layout title="Datasets">
    <Heading mb={2} fontSize="2xl" fontWeight="semibold">
      Taxonomy Management
    </Heading>
    {/* TODO: get actual copy */}
    <Text size="sm" mb={4}>
      Placeholder instruction
    </Text>
    <TaxonomyTabs />
  </Layout>
);
export default DataSets;
