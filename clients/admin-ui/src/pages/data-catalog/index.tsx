import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import CatalogSystemsTable from "~/features/data-catalog/systems/CatalogSystemsTable";

const DataCatalogMainPage = () => {
  return (
    <Layout title="Data catalog">
      <PageHeader
        heading="Data catalog"
        breadcrumbItems={[{ title: "All systems" }]}
      />
      <CatalogSystemsTable />
    </Layout>
  );
};

export default DataCatalogMainPage;
