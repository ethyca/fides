import { NextPage } from "next";
import { useRouter } from "next/router";

import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import CatalogResourcesTable from "~/features/data-catalog/staged-resources/CatalogResourcesTable";
import { useGetSystemByFidesKeyQuery } from "~/features/system";

const CatalogResourceView: NextPage = () => {
  const { query } = useRouter();
  const systemId = query.systemId as string;
  const resourceUrn = query.resourceUrn as string;
  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId);

  if (isLoading) {
    return <FidesSpinner />;
  }

  return (
    <Layout title="Data catalog">
      <PageHeader
        title="Data catalog"
        breadcrumbs={[{ title: "Data catalog" }]}
      />
      <CatalogResourcesTable resourceUrn={resourceUrn} system={system!} />
    </Layout>
  );
};

export default CatalogResourceView;
