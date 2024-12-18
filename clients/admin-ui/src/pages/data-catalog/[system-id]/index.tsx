import { useRouter } from "next/router";

import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import CatalogProjectsTable from "~/features/data-catalog/projects/CatalogProjectsTable";
import { useGetSystemByFidesKeyQuery } from "~/features/system";

const CatalogProjectView = () => {
  const { query } = useRouter();
  const systemKey = query["system-id"] as string;
  const monitorConfigIds = query.monitor_config_ids as string[];
  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemKey);

  if (isLoading) {
    return <FidesSpinner />;
  }

  return (
    <Layout title="Data catalog">
      <PageHeader breadcrumbs={[{ title: "Data catalog" }]} />
      <CatalogProjectsTable
        systemKey={systemKey}
        monitorConfigIds={monitorConfigIds}
      />
    </Layout>
  );
};

export default CatalogProjectView;
