import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const Steward: NextPage = () => (
  <Layout title="Steward">
    <PageHeader
      heading="Steward"
      breadcrumbItems={[{ title: "Home", href: "/" }, { title: "Steward" }]}
    />
  </Layout>
);

export default Steward;
