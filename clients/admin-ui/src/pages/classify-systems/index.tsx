import { Button, Heading, HStack, Spinner, Stack, Text } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { ReactNode, useEffect, useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import { useInterzoneNav } from "~/features/common/hooks/useInterzoneNav";
import Layout from "~/features/common/Layout";
import {
  useGetAllClassifyInstancesQuery,
  useGetHealthQuery,
} from "~/features/plus/plus.slice";
import {
  selectSystemsToClassify,
  setSystemsToClassify,
  useGetAllSystemsQuery,
} from "~/features/system";
import ClassifySystemsTable from "~/features/system/ClassifySystemsTable";
import { ClassificationStatus, GenerateTypes } from "~/types/api";

const POLL_INTERVAL_SECONDS = 3;

const ClassifySystemsLayout = ({ children }: { children: ReactNode }) => (
  <Layout title="Classify Systems">
    <Stack spacing={4}>
      <Heading fontSize="2xl" fontWeight="semibold">
        Classified systems
      </Heading>
      {children}
    </Stack>
  </Layout>
);

const ClassifySystems: NextPage = () => {
  const router = useRouter();
  const dispatch = useDispatch();
  const { systemOrDatamapRoute } = useInterzoneNav();
  const { isSuccess: hasPlus, isLoading: isLoadingPlus } = useGetHealthQuery();
  /**
   * TODO: fides#1744
   * Because there is currently no way to associate a scan with its classification,
   * we attempt to get the classification results for only the systems in review.
   * However, because this is its own page that can be navigated to directly,
   * we can't necessarily rely on knowing which systems were put into review
   * Therefore, as a fallback, query all systems.
   */
  const systemsToClassify = useAppSelector(selectSystemsToClassify);
  const { isLoading: isLoadingSystems, data: allSystems } =
    useGetAllSystemsQuery(undefined, {
      skip: !hasPlus || (systemsToClassify && systemsToClassify.length > 0),
    });
  const systems = systemsToClassify || allSystems;
  useEffect(() => {
    if (allSystems && allSystems.length) {
      dispatch(setSystemsToClassify(allSystems));
    }
  }, [dispatch, allSystems]);

  // Poll for updates to classification until all classifications are finished
  const [shouldPoll, setShouldPoll] = useState(true);
  const { isLoading: isLoadingClassifications, data: classifications } =
    useGetAllClassifyInstancesQuery(
      {
        resource_type: GenerateTypes.SYSTEMS,
        fides_keys: systems?.map((s) => s.fides_key),
      },
      {
        skip: !hasPlus,
        pollingInterval: shouldPoll ? POLL_INTERVAL_SECONDS * 1000 : undefined,
      }
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

  useEffect(() => {
    if (isClassificationFinished) {
      setShouldPoll(false);
    }
  }, [isClassificationFinished]);

  if (isLoading) {
    return (
      <ClassifySystemsLayout>
        <Spinner />
      </ClassifySystemsLayout>
    );
  }

  if (!classifications || classifications.length === 0) {
    return (
      <ClassifySystemsLayout>
        <Text data-testid="no-classifications">
          No classifications found. Have you run a scan?
        </Text>
      </ClassifySystemsLayout>
    );
  }

  return (
    <ClassifySystemsLayout>
      <Text>
        {isClassificationFinished
          ? "All systems have been classifed by Fides."
          : "Systems are still being classified by Fides."}
      </Text>
      {systems && systems.length ? (
        <ClassifySystemsTable systems={systems} />
      ) : (
        "No systems with classifications found"
      )}
      <HStack>
        <NextLink href={systemOrDatamapRoute} passHref>
          <Button variant="primary" size="sm">
            Finish
          </Button>
        </NextLink>
      </HStack>
    </ClassifySystemsLayout>
  );
};

export default ClassifySystems;
