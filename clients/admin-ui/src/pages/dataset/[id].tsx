import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { DATASET_ROUTE } from "~/features/common/nav/v2/routes";
import DatasetCollectionView from "~/features/dataset/DatasetCollectionView";

const DatasetDetail: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;

  if (!id) {
    return <Layout title="Dataset">Dataset not found</Layout>;
  }

  const fidesKey = Array.isArray(id) ? id[0] : id;

  return (
    <Layout title={`Dataset - ${id}`}>
      <BackButton backPath={DATASET_ROUTE} />
      <DatasetCollectionView fidesKey={fidesKey} />
    </Layout>
  );
};

export default DatasetDetail;
