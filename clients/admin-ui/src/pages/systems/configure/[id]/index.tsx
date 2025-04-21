import { AntButton as Button, Box, Text, VStack } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabsContent from "~/features/common/DataTabsContent";
import DataTabsHeader from "~/features/common/DataTabsHeader";
import { useFeatures } from "~/features/common/features";
import FidesSpinner from "~/features/common/FidesSpinner";
import { extractVendorSource, VendorSources } from "~/features/common/helpers";
import { GearLightIcon } from "~/features/common/Icon";
import Layout from "~/features/common/Layout";
import {
  INTEGRATION_MANAGEMENT_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
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

const ConfigureSystem: NextPage = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();

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

  const { tcf: isTCFEnabled, plus: isPlusEnabled } = useFeatures();

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

  const { tabData, tabIndex, onTabChange } = useSystemFormTabs({
    isCreate: false,
  });

  if ((isLoading || isDictionaryLoading) && !dictionaryError) {
    return (
      <Layout title="Systems">
        <FidesSpinner />
      </Layout>
    );
  }

  return (
    <Layout title="System inventory" mainProps={{ w: "calc(100vw - 240px)" }}>
      <PageHeader
        heading="System inventory"
        breadcrumbItems={[
          { title: "All systems", href: SYSTEM_ROUTE },
          { title: system?.name || "" },
        ]}
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
          {isPlusEnabled && (
            <Button
              size="small"
              className="absolute right-2 top-2"
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
        <VStack alignItems="stretch">
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
