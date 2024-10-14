import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import TaxonomyTabs from "~/features/taxonomy/TaxonomyTabs";

const TaxonomyPage: NextPage = () => {
  return (
    <Layout
      title="Taxonomy"
      mainProps={{
        padding: "0 40px 48px",
      }}
    >
      <PageHeader breadcrumbs={[{ title: "Taxonomy" }]} />

      <div className="mt-10">
        <TaxonomyTabs />
      </div>
    </Layout>
  );
};
export default TaxonomyPage;
