import { Heading, Spinner, Stack, Text } from "@fidesui/react";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import Layout from "~/features/common/Layout";
import {
  selectSystemsForReview,
  setSystemsForReview,
} from "~/features/config-wizard/config-wizard.slice";
import {
  useGetAllClassifyInstancesQuery,
  useGetHealthQuery,
} from "~/features/plus/plus.slice";
import { useGetAllSystemsQuery } from "~/features/system";
import ClassifySystemsTable from "~/features/system/ClassifySystemsTable";
import { ClassificationStatus, GenerateTypes } from "~/types/api";

const ClassifySystems: NextPage = () => {
  const router = useRouter();
  const dispatch = useDispatch();
  const { isSuccess: hasPlus, isLoading: isLoadingPlus } = useGetHealthQuery();
  /**
   * TODO: fides#1744
   * Because there is currently no way to associate a scan with its classification,
   * we attempt to get the classification results for only the systems in review.
   * However, because this is a page that is waiting for results and so will likely
   * be refreshed, we can't necessarily rely on knowing the systems we put into review
   * Therefore, as a fallback, query all systems.
   */
  const systemsForReview = useAppSelector(selectSystemsForReview);
  const { isLoading: isLoadingSystems, data: allSystems } =
    useGetAllSystemsQuery(undefined, {
      skip: !hasPlus || systemsForReview.length > 0,
    });
  const systems = systemsForReview || allSystems;
  useEffect(() => {
    if (allSystems && allSystems.length) {
      dispatch(setSystemsForReview(allSystems));
    }
  }, [dispatch, allSystems]);

  const { isLoading: isLoadingClassifications, data: classifications } =
    useGetAllClassifyInstancesQuery(
      {
        resource_type: GenerateTypes.SYSTEMS,
        fides_keys: systems.map((s) => s.fides_key),
      },
      { skip: !hasPlus }
    );

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
        {systems && systems.length && classifications ? (
          <ClassifySystemsTable systems={systems} />
        ) : (
          "No systems with classifications found"
        )}
      </Stack>
    </Layout>
  );
};

export default ClassifySystems;
