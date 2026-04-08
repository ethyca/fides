import { Spin } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { DATA_CATALOG_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import CatalogResourcesTable from "~/features/data-catalog/staged-resources/CatalogResourcesTable";
import { parseResourceBreadcrumbsNoProject } from "~/features/data-catalog/utils/urnParsing";
import { useGetSystemByFidesKeyQuery } from "~/features/system";

const CatalogResourceView: NextPage = () => {
  const { query } = useRouter();
  const systemId = query.systemId as string;
  const resourceUrn = query.resourceUrn as string;
  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId);

  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const resourceBreadcrumbs = parseResourceBreadcrumbsNoProject(
    resourceUrn,
    `${DATA_CATALOG_ROUTE}/${systemId}/resources`,
  );

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
            {
              title: system?.name ?? system?.fides_key ?? systemId,
              href: DATA_CATALOG_ROUTE,
            },
            ...resourceBreadcrumbs.map((b) => ({
              title: String(b.title ?? ""),
              href: typeof b.href === "string" ? b.href : undefined,
            })),
          ]}
        />
        <SidePanel.Search
          onSearch={setSearchQuery}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search resources..."
        />
      </SidePanel>
      <Layout title="Data catalog">
        <CatalogResourcesTable
          resourceUrn={resourceUrn}
          onRowClick={(row) =>
            router.push(
              `${DATA_CATALOG_ROUTE}/${system!.fides_key}/resources/${row.urn}`,
            )
          }
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />
      </Layout>
    </>
  );
};

export default CatalogResourceView;
