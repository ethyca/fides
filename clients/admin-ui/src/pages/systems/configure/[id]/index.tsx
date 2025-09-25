import { AntButton as Button, AntTabs as Tabs, Text } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
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
import { useGetSystemByFidesKeyQuery } from "~/features/system";
import {
  selectLockedForGVL,
  setLockedForGVL,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import GVLNotice from "~/features/system/GVLNotice";
import useSystemFormTabs, {
  SYSTEM_TAB_KEYS,
} from "~/features/system/hooks/useSystemFormTabs";

const ConfigureSystem: NextPage = () => {
  const router = useRouter();

  const dispatch = useAppDispatch();

  const systemId =
    (Array.isArray(router.query.id) ? router.query.id[0] : router.query.id) ??
    "";

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId);

  const { error: dictionaryError, isLoading: isDictionaryLoading } =
    useGetAllDictionaryEntriesQuery();

  const { tcf: isTCFEnabled, plus: isPlusEnabled } = useFeatures();

  const lockedForGVL = useAppSelector(selectLockedForGVL);

  useEffect(() => {
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

  const { tabData, activeKey, onTabChange } = useSystemFormTabs({
    isCreate: false,
  });

  if ((isLoading || isDictionaryLoading) && !dictionaryError) {
    return (
      <Layout title="Systems">
        <FidesSpinner />
      </Layout>
    );
  }

  if (!system) {
    return (
      <Layout title="Systems">
        <Text data-testid="system-not-found">
          Could not find a system with id {systemId}
        </Text>
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
      />
      <Tabs
        activeKey={activeKey}
        onChange={(tabKey) => {
          const systemKey = SYSTEM_TAB_KEYS.find((st) => st === tabKey);

          if (systemKey) {
            onTabChange(systemKey);
          }
        }}
        items={tabData}
        className="w-full"
        tabBarExtraContent={
          isPlusEnabled && (
            <Button
              size="small"
              className="absolute right-2 top-2"
              data-testid="integration-page-btn"
              onClick={() => router.push(INTEGRATION_MANAGEMENT_ROUTE)}
            >
              <Text>Integrations</Text>
              <GearLightIcon marginLeft={2} />
            </Button>
          )
        }
        renderTabBar={(props, DefaultTabBar) => (
          <>
            <DefaultTabBar {...props} />
            {lockedForGVL && <GVLNotice />}
          </>
        )}
      />
    </Layout>
  );
};

export default ConfigureSystem;
