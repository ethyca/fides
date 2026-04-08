import { Spin } from "fidesui";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { DATA_CATALOG_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import CatalogProjectsTable from "~/features/data-catalog/projects/CatalogProjectsTable";
import { useGetSystemByFidesKeyQuery } from "~/features/system";

const CatalogProjectView = () => {
  const { query } = useRouter();
  const systemKey = query.systemId as string;
  const monitorConfigIds = query.monitor_config_ids as string[];
  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemKey);

  if (isLoading) {
    return <Spin />;
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Data catalog"
          breadcrumbItems={[
            { title: "All systems", href: DATA_CATALOG_ROUTE },
            { title: system?.name ?? system?.fides_key ?? systemKey },
          ]}
        />
      </SidePanel>
      <Layout title="Data catalog">
        <CatalogProjectsTable
          systemKey={systemKey}
          monitorConfigIds={monitorConfigIds}
        />
      </Layout>
    </>
  );
};

export default CatalogProjectView;
