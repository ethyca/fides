import { useRouter } from "next/router";

import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { DATA_CATALOG_II_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import CatalogProjectsTable from "~/features/data-catalog/projects/CatalogProjectsTable";
import { useGetSystemByFidesKeyQuery } from "~/features/system";

const CatalogProjectView = () => {
  const { query } = useRouter();
  const systemKey = query.systemId as string;
  const monitorConfigIds = query.monitor_config_ids as string[];
  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemKey);

  if (isLoading) {
    return <FidesSpinner />;
  }

  return (
    <Layout title="Data catalog">
      <PageHeader
        heading="Data catalog"
        breadcrumbItems={[
          { title: "All systems", href: DATA_CATALOG_II_ROUTE },
          { title: system?.name ?? system?.fides_key },
        ]}
      />
      <CatalogProjectsTable
        systemKey={systemKey}
        monitorConfigIds={monitorConfigIds}
      />
    </Layout>
  );
};

export default CatalogProjectView;
