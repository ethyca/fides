import {
  AntSpace as Space,
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
} from "fidesui";
import dynamic from "next/dynamic";
import * as React from "react";
import { useEffect } from "react";

import { useFeatures } from "~/features/common/features";
import Restrict from "~/features/common/Restrict";
import { RequestTable } from "~/features/privacy-requests/RequestTable";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ScopeRegistryEnum } from "~/types/api";

import PageHeader from "../common/PageHeader";
import { useDSRErrorAlert } from "./hooks/useDSRErrorAlert";
import {
  PRIVACY_REQUEST_TABS,
  usePrivacyRequestTabs,
} from "./hooks/usePrivacyRequestTabs";
import ManualTaskTab from "./ManualTaskTab";

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

  const tabItems: TabsProps["items"] = [
    {
      key: PRIVACY_REQUEST_TABS.REQUEST,
      label: "Request",
      children: <RequestTable />,
    },
    ...(availableTabs.manualTask
      ? [
          {
            key: PRIVACY_REQUEST_TABS.MANUAL_TASK,
            label: "Manual task",
            children: <ManualTaskTab />,
          },
        ]
      : []),
  ];

  const handleTabChangeWrapper = (activeKey: string) => {
    handleTabChange(activeKey as any); // Cast to PrivacyRequestTabKey since we control the tabs
  };

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

      <Tabs
        activeKey={activeTab}
        onChange={handleTabChangeWrapper}
        items={tabItems}
      />
    </>
  );
};

export default PrivacyRequestsContainer;
