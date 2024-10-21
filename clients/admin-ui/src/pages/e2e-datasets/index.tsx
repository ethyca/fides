import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import SystemsTable from "~/features/dataset-lifecycle/systems/SystemsTable";

const E2EDatasetSystemView = () => {
  return (
    <Layout title="E2E datasets">
      <PageHeader breadcrumbs={[{ title: "E2E datasets" }]} />
      <SystemsTable />
    </Layout>
  );
};

export default E2EDatasetSystemView;
