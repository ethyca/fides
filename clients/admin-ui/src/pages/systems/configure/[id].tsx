import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  Heading,
  Spinner,
  Text,
  useToast,
} from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { extractVendorSource, VendorSources } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useGetAllDictionaryEntriesQuery } from "~/features/plus/plus.slice";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";
import {
  selectLockedForGVL,
  setLockedForGVL,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import EditSystemFlow from "~/features/system/EditSystemFlow";
import GVLNotice from "~/features/system/GVLNotice";

const INTEGRATION_TAB_INDEX = 3; // this needs to be updated if the order of the tabs changes

const ConfigureSystem: NextPage = () => {
  const toast = useToast();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [initialTabIndex, setInitialTabIndex] = useState(0);
  let systemId = "";
  if (router.query.id) {
    systemId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  }

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId, {
    skip: !systemId,
  });
  const { isLoading: isDictionaryLoading } = useGetAllDictionaryEntriesQuery();
  const { tcf: isTCFEnabled } = useFeatures();

  const lockedForGVL = useAppSelector(selectLockedForGVL);

  useEffect(() => {
    dispatch(setActiveSystem(system));
    if (system) {
      const locked =
        isTCFEnabled &&
        !!system.vendor_id &&
        extractVendorSource(system.fides_key) === VendorSources.GVL;
      dispatch(setLockedForGVL(locked));
    }
  }, [system, dispatch, isTCFEnabled]);

  useEffect(() => {
    const { status } = router.query;

    if (status) {
      if (status === "succeeded") {
        toast(successToastParams(`Integration successfully authorized.`));
      } else {
        toast(errorToastParams(`Failed to authorize integration.`));
      }
      // create a new url without the status query param
      const newQuery = { ...router.query };
      delete newQuery.status;
      const newUrl = {
        pathname: router.pathname,
        query: newQuery,
      };

      // replace the current history entry
      router.replace(newUrl, undefined, { shallow: true });

      setInitialTabIndex(INTEGRATION_TAB_INDEX);
    }
  }, [router, toast]);

  if (isLoading && isDictionaryLoading) {
    return (
      <Layout title="Systems">
        <Spinner />
      </Layout>
    );
  }

  return (
    <Layout title="Systems">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Configure your system
      </Heading>

      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <NextLink href={SYSTEM_ROUTE}>System Integrations</NextLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <NextLink href="#">Configure your integration</NextLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>

      {lockedForGVL ? <GVLNotice /> : null}
      {!system && !isLoading && !isDictionaryLoading ? (
        <Text data-testid="system-not-found">
          Could not find a system with id {systemId}
        </Text>
      ) : (
        <EditSystemFlow initialTabIndex={initialTabIndex} />
      )}
    </Layout>
  );
};

export default ConfigureSystem;
