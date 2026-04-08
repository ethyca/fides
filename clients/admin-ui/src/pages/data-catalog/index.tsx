import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import CatalogSystemsTable from "~/features/data-catalog/systems/CatalogSystemsTable";

const DataCatalogMainPage = () => (
  <>
    <SidePanel>
      <SidePanel.Identity title="Data catalog" breadcrumbItems={[{ title: "All systems" }]} />
    </SidePanel>
    <Layout title="Data catalog">
      <CatalogSystemsTable />
    </Layout>
  </>
);

export default DataCatalogMainPage;
