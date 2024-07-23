import { Box, Button, Text, useToast, VStack } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabsContent from "~/features/common/DataTabsContent";
import DataTabsHeader from "~/features/common/DataTabsHeader";
import { useFeatures, useFlags } from "~/features/common/features";
import FidesSpinner from "~/features/common/FidesSpinner";
import { extractVendorSource, VendorSources } from "~/features/common/helpers";
import { GearLightIcon } from "~/features/common/Icon";
import Layout from "~/features/common/Layout";
import {
  INTEGRATION_MANAGEMENT_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
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
import GVLNotice from "~/features/system/GVLNotice";
import useSystemFormTabs from "~/features/system/hooks/useSystemFormTabs";

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

  const { error: dictionaryError, isLoading: isDictionaryLoading } =
    useGetAllDictionaryEntriesQuery();

  const { tcf: isTCFEnabled } = useFeatures();
  const { flags } = useFlags();
  const discoveryDetectionEnabled = flags.dataDiscoveryAndDetection;

  const lockedForGVL = useAppSelector(selectLockedForGVL);

  useEffect(() => {
    dispatch(setActiveSystem(system));
    if (system) {
      const locked =
        isTCFEnabled &&
        !!system.vendor_id &&
        extractVendorSource(system.vendor_id) === VendorSources.GVL;
      dispatch(setLockedForGVL(locked));
    } else {
      setLockedForGVL(false);
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

  const { tabData, tabIndex, onTabChange } = useSystemFormTabs({
    isCreate: false,
    initialTabIndex,
  });

  if ((isLoading || isDictionaryLoading) && !dictionaryError) {
    return (
      <Layout title="Systems">
        <FidesSpinner />
      </Layout>
    );
  }

  return (
    <Layout title="System inventory" mainProps={{ paddingTop: 0 }}>
      <PageHeader
        breadcrumbs={[
          { title: "System inventory", link: SYSTEM_ROUTE },
          { title: system?.name || "" },
        ]}
        isSticky
      >
        <Box position="relative">
          <DataTabsHeader
            data={tabData}
            data-testid="system-tabs"
            index={tabIndex}
            isLazy
            isManual
            onChange={onTabChange}
            width="full"
            border="full-width"
          />
          {discoveryDetectionEnabled && (
            <Button
              size="xs"
              variant="outline"
              position="absolute"
              right={0}
              top="50%"
              transform="auto"
              translateY="-50%"
              data-testid="integration-page-btn"
              onClick={() => router.push(INTEGRATION_MANAGEMENT_ROUTE)}
            >
              <Text>Integrations</Text>
              <GearLightIcon marginLeft={2} />
            </Button>
          )}
        </Box>
      </PageHeader>
      {lockedForGVL ? <GVLNotice /> : null}
      {!system && !isLoading && !isDictionaryLoading ? (
        <Text data-testid="system-not-found">
          Could not find a system with id {systemId}
        </Text>
      ) : (
        <VStack alignItems="stretch" flex="1" gap="18px" maxWidth="70vw">
          <DataTabsContent
            data={tabData}
            index={tabIndex}
            isLazy
            isManual
            onChange={onTabChange}
          />
        </VStack>
      )}
    </Layout>
  );
};

export default ConfigureSystem;
