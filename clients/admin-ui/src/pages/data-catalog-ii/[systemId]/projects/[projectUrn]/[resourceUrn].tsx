import { NextPage } from "next";
import { useRouter } from "next/router";

import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { DATA_CATALOG_II_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import CatalogResourcesTable from "~/features/data-catalog/staged-resources/CatalogResourcesTable";
import parseUrnWithProjectToBreadcrumbs from "~/features/data-catalog/staged-resources/parseUrnToBreadcrumbs";
import { useGetSystemByFidesKeyQuery } from "~/features/system";

const CatalogResourceView: NextPage = () => {
  const { query } = useRouter();
  const systemId = query.systemId as string;
  const resourceUrn = query.resourceUrn as string;
  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId);

  const resourceBreadcrumbs =
    parseUrnWithProjectToBreadcrumbs(
      resourceUrn,
      `${DATA_CATALOG_II_ROUTE}/${systemId}/projects/`,
    ) ?? [];

  if (isLoading) {
    return <FidesSpinner />;
  }

  return (
    <Layout title="Data catalog">
      <PageHeader
        heading="Data catalog"
        breadcrumbItems={[
          { title: "All systems", href: DATA_CATALOG_II_ROUTE },
          {
            title: system?.name ?? system?.fides_key,
            href: `${DATA_CATALOG_II_ROUTE}/${systemId}`,
          },
          ...resourceBreadcrumbs,
        ]}
      />
      <CatalogResourcesTable resourceUrn={resourceUrn} system={system!} />
    </Layout>
  );
};

export default CatalogResourceView;
