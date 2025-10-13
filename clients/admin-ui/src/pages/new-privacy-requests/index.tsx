import {
  AntSpace as Space,
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
} from "fidesui";
import type { NextPage } from "next";
import { useEffect, useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import { ManualTasks } from "~/features/manual-tasks/ManualTasks";
import ActionButtons from "~/features/privacy-requests/buttons/ActionButtons";
import { PrivacyRequestsDashboard } from "~/features/privacy-requests/dashboard/PrivacyRequestsDashboard";
import { useDSRErrorAlert } from "~/features/privacy-requests/hooks/useDSRErrorAlert";
import {
  PRIVACY_REQUEST_TABS,
  usePrivacyRequestTabs,
} from "~/features/privacy-requests/hooks/usePrivacyRequestTabs";
import SubmitPrivacyRequest from "~/features/privacy-requests/SubmitPrivacyRequest";
import { ScopeRegistryEnum } from "~/types/api";

const PrivacyRequests: NextPage = () => {
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
        children: <PrivacyRequestsDashboard />,
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
    <FixedLayout title="Privacy Requests">
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
    </FixedLayout>
  );
};
export default PrivacyRequests;
