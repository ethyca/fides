import { Heading, Spinner, Stack, Text } from "@fidesui/react";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useEffect } from "react";

import Layout from "~/features/common/Layout";
import {
  useGetAllClassifyInstancesQuery,
  useGetHealthQuery,
} from "~/features/plus/plus.slice";
import { useGetAllSystemsQuery } from "~/features/system";
import ClassifySystemsTable from "~/features/system/ClassifySystemsTable";
import { ClassificationStatus } from "~/types/api";

const ClassifySystems: NextPage = () => {
  const router = useRouter();
  const { isSuccess: hasPlus, isLoading: isLoadingPlus } = useGetHealthQuery();
  const { isLoading: isLoadingSystems, data: systems } = useGetAllSystemsQuery(
    undefined,
    { skip: !hasPlus }
  );
  const { isLoading: isLoadingClassifications, data: classifications } =
    useGetAllClassifyInstancesQuery(undefined, { skip: !hasPlus });

  useEffect(() => {
    if (!isLoadingPlus && !hasPlus) {
      router.push("/");
    }
  }, [router, hasPlus, isLoadingPlus]);

  const isLoading = isLoadingSystems || isLoadingClassifications;

  const isClassificationFinished = classifications
    ? classifications.every(
        (c) =>
          c.status === ClassificationStatus.COMPLETE ||
          c.status === ClassificationStatus.FAILED ||
          c.status === ClassificationStatus.REVIEWED
      )
    : false;

  return (
    <Layout title="Classify Systems">
      <Stack spacing={4}>
        <Heading fontSize="2xl" fontWeight="semibold">
          Classified systems
        </Heading>
        <Text>
          {isClassificationFinished
            ? "All systems have been classifed by Fides."
            : "Systems are still being classified by Fides."}
        </Text>

        {isLoading ? <Spinner /> : null}
        {systems && classifications ? (
          <ClassifySystemsTable systems={systems} />
        ) : (
          "No systems with classifications found"
        )}
      </Stack>
    </Layout>
  );
};

export default ClassifySystems;
