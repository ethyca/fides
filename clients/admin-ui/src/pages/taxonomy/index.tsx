import { Heading } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import TaxonomyTabs from "~/features/taxonomy/TaxonomyTabs";

const DataSets: NextPage = () => (
  <Layout title="Datasets">
    <Heading mb={2} fontSize="2xl" fontWeight="semibold">
      Taxonomy Management
    </Heading>
    <TaxonomyTabs />
  </Layout>
);
export default DataSets;
