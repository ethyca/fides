import {
  AntSpace as Space,
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
} from "fidesui";
import dynamic from "next/dynamic";
import * as React from "react";
import { useEffect, useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import Restrict from "~/features/common/Restrict";
import { ManualTasks } from "~/features/manual-tasks/ManualTasks";
import { RequestTable } from "~/features/privacy-requests/RequestTable";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ScopeRegistryEnum } from "~/types/api";

import PageHeader from "../common/PageHeader";
import { useDSRErrorAlert } from "./hooks/useDSRErrorAlert";
import {
  PRIVACY_REQUEST_TABS,
  usePrivacyRequestTabs,
} from "./hooks/usePrivacyRequestTabs";

const ActionButtons = dynamic(
  () => import("~/features/privacy-requests/buttons/ActionButtons"),
  { loading: () => <div>Loading...</div> },
);

const PrivacyRequestsContainer = () => {
  const { processing } = useDSRErrorAlert();
  const { plus: hasPlus } = useFeatures();
  const { activeTab, handleTabChange, availableTabs } = usePrivacyRequestTabs();

  useEffect(() => {
    processing();
  }, [processing]);

  const tabItems: TabsProps["items"] = useMemo(() => {
    const items: NonNullable<TabsProps["items"]> = [];

    if (availableTabs.request) {
      items.push({
        key: PRIVACY_REQUEST_TABS.REQUEST,
        label: "Request",
        children: <RequestTable />,
      });
    }

    if (availableTabs.manualTask) {
      items.push({
        key: PRIVACY_REQUEST_TABS.MANUAL_TASK,
        label: "Manual tasks",
        children: <ManualTasks />,
      });
    }

    return items;
  }, [availableTabs.manualTask, availableTabs.request]);

  return (
    <>
      <PageHeader
        heading="Privacy Requests"
        breadcrumbItems={[{ title: "All requests" }]}
        rightContent={
          <Space>
            {hasPlus && (
              <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_CREATE]}>
                <SubmitPrivacyRequest />
              </Restrict>
            )}
            <ActionButtons />
          </Space>
        }
        data-testid="privacy-requests"
      />

      <Tabs activeKey={activeTab} onChange={handleTabChange} items={tabItems} />
    </>
  );
};

export default PrivacyRequestsContainer;
