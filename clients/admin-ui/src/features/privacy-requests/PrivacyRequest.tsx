import { useGetAllEnabledAccessManualHooksQuery as useGetManualIntegrationsQuery } from "datastore-connections/datastore-connection.slice";
import { AntTabs as Tabs, AntTabsProps as TabsProps } from "fidesui";
import { useMemo, useState } from "react";

import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import { PrivacyRequestStatus } from "~/types/api";

import ActivityTab from "./events-and-logs/ActivityTab";
import ManualProcessingList from "./manual-processing/ManualProcessingList";
import RequestDetails from "./RequestDetails";
import { PrivacyRequestEntity } from "./types";

type PrivacyRequestProps = {
  data: PrivacyRequestEntity;
};

const PrivacyRequest = ({ data: initialData }: PrivacyRequestProps) => {
  const queryOptions = useMemo(
    () => ({
      id: initialData.id,
      verbose: true,
    }),
    [initialData.id],
  );

  // Poll for the latest privacy request data while the status is approved or in processing
  const { data: latestData } = useGetAllPrivacyRequestsQuery(queryOptions, {
    pollingInterval:
      initialData.status === PrivacyRequestStatus.APPROVED ||
      initialData.status === PrivacyRequestStatus.IN_PROCESSING
        ? 2000
        : 0,
    skip: !initialData.id,
  });

  // Use latest data if available, otherwise use initial data
  const subjectRequest = latestData?.items[0] ?? initialData;

  const isManualStepsRequired =
    subjectRequest.status === PrivacyRequestStatus.REQUIRES_INPUT;

  // Check if any manual-process integrations exist
  const { data: manualIntegrations } = useGetManualIntegrationsQuery();
  const hasManualIntegrations = (manualIntegrations || []).length > 0;

  const showManualSteps = isManualStepsRequired && hasManualIntegrations;

  const [activeTabKey, setActiveTabKey] = useState(
    showManualSteps ? "manual-steps" : "activity",
  );
  const items: TabsProps["items"] = useMemo(
    () => [
      {
        key: "activity",
        label: "Activity",
        children: <ActivityTab subjectRequest={subjectRequest} />,
      },
      {
        key: "manual-steps",
        label: "Manual steps",
        children: (
          <ManualProcessingList
            subjectRequest={subjectRequest}
            onComplete={() => setActiveTabKey("activity")}
          />
        ),
        disabled: !showManualSteps,
      },
    ],
    [showManualSteps, subjectRequest],
  );

  return (
    <div className="flex gap-8">
      <div className="flex-1">
        <Tabs
          items={items}
          activeKey={activeTabKey}
          onChange={setActiveTabKey}
        />
      </div>
      <div
        className="w-1/3 2xl:w-[432px]"
        data-testid="privacy-request-details"
      >
        <RequestDetails subjectRequest={subjectRequest} />
      </div>
    </div>
  );
};

export default PrivacyRequest;
