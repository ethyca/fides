import {
  Button,
  ChakraBox as Box,
  Icons,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { findDatasetByKey } from "~/features/dataset-mock/mock-data";
import { MockSchemaExplorer } from "~/features/dataset-mock/MockSchemaExplorer";

const DatasetMockCollectionPage: NextPage = () => {
  const router = useRouter();
  const datasetId = router.query.datasetId
    ? decodeURIComponent(router.query.datasetId as string)
    : "legacy_orders_pg";
  const collectionId = router.query.collectionId
    ? decodeURIComponent(router.query.collectionId as string)
    : "users";

  const dataset = findDatasetByKey(datasetId);

  return (
    <Layout title={`Collection — ${collectionId}`}>
      <Box data-testid="dataset-mock-collection-detail">
        <PageHeader
          heading="Datasets"
          breadcrumbItems={[
            { title: "All datasets", href: "/dataset-mock" },
            {
              title: datasetId,
              href: `/dataset-mock/${encodeURIComponent(datasetId)}`,
            },
            { title: collectionId },
          ]}
          rightContent={
            <Button icon={<Icons.Flow />} data-testid="visual-editor-btn">
              Visual editor
            </Button>
          }
        />

        {!dataset ? (
          <Box p={6}>Dataset not found.</Box>
        ) : (
          <MockSchemaExplorer
            collectionKey={collectionId}
            initialWireDrawerOpen={router.query.wire === "open"}
          />
        )}
      </Box>
    </Layout>
  );
};

export default DatasetMockCollectionPage;
