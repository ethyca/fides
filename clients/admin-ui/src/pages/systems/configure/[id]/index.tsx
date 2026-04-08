import { Button, Icons, Spin } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ErrorPage from "~/features/common/errors/ErrorPage";
import { useFeatures } from "~/features/common/features";
import { extractVendorSource, VendorSources } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import {
  INTEGRATION_MANAGEMENT_ROUTE,
  SYSTEM_ROUTE,
} from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import { useGetAllDictionaryEntriesQuery } from "~/features/plus/plus.slice";
import { useGetSystemByFidesKeyQuery } from "~/features/system";
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

  const {
    data: system,
    isLoading,
    error,
  } = useGetSystemByFidesKeyQuery(systemId);

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
      <>
        <SidePanel>
          <SidePanel.Identity title="System inventory" />
        </SidePanel>
        <Layout title="Systems">
          <Spin />
        </Layout>
      </>
    );
  }

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage={`A problem occurred while fetching the system ${systemId}`}
        actions={[
          {
            label: "Return to systems",
            onClick: () => router.push(SYSTEM_ROUTE),
          },
        ]}
      />
    );
  }

  const navItems = tabData.map((tab) => ({
    key: tab.key as string,
    label: tab.label as string,
    disabled: tab.disabled ?? false,
  }));

  const activeContent = tabData.find((tab) => tab.key === activeKey)?.children;

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title={system?.name || "System"}
          breadcrumbItems={[
            { title: "All systems", href: SYSTEM_ROUTE },
            { title: system?.name || "" },
          ]}
        />
        <SidePanel.Navigation
          items={navItems}
          activeKey={activeKey}
          onSelect={onTabChange}
        />
        {isPlusEnabled && (
          <SidePanel.Actions>
            <Button
              data-testid="integration-page-btn"
              iconPlacement="end"
              icon={<Icons.Settings />}
              onClick={() => router.push(INTEGRATION_MANAGEMENT_ROUTE)}
            >
              Integrations
            </Button>
          </SidePanel.Actions>
        )}
      </SidePanel>
      <Layout title="System inventory">
        {lockedForGVL && <GVLNotice />}
        {activeContent}
      </Layout>
    </>
  );
};

export default ConfigureSystem;
