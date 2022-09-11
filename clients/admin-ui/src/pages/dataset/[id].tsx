import { Box, Breadcrumb, BreadcrumbItem, Heading } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
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
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Dataset
      </Heading>
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <NextLink href="/dataset">Datasets</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">{id}</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>
      <DatasetCollectionView fidesKey={fidesKey} />
    </Layout>
  );
};

export default DatasetDetail;
