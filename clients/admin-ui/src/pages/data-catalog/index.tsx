import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import SystemsTable from "~/features/data-catalog/systems/CatalogSystemsTable";

const DataCatalogMainPage = () => {
  return (
    <Layout title="Data catalog">
      <PageHeader breadcrumbs={[{ title: "Data catalog" }]} />
      <SystemsTable />
    </Layout>
  );
};

export default DataCatalogMainPage;
