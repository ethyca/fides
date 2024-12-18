import { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import CatalogResourcesTable from "~/features/data-catalog/staged-resource/CatalogResourcesTable";

const CatalogResourceView: NextPage = () => {
  const { query } = useRouter();
  //   const systemId = query["system-id"] as string;
  const resourceUrn = query["resource-urn"] as string;

  return (
    <Layout title="Data catalog">
      <PageHeader title="Data catalog" breadcrumbs={false} />
      <CatalogResourcesTable resourceUrn={resourceUrn} />
    </Layout>
  );
};

export default CatalogResourceView;
