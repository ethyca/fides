import { AntTabs as Tabs, AntTabsProps as TabsProps } from "fidesui";
import { useMemo, useState } from "react";

import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import { PrivacyRequestStatus } from "~/types/api";

import ActivityTimeline from "./events-and-logs/ActivityTimeline";
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

  const [activeTabKey, setActiveTabKey] = useState(
    isManualStepsRequired ? "manual-steps" : "activity",
  );
  const items: TabsProps["items"] = useMemo(
    () => [
      {
        key: "activity",
        label: "Activity",
        children: <ActivityTimeline subjectRequest={subjectRequest} />,
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
        disabled: !isManualStepsRequired,
      },
    ],
    [isManualStepsRequired, subjectRequest],
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
      <div className="w-[432px]" data-testid="privacy-request-details">
        <RequestDetails subjectRequest={subjectRequest} />
      </div>
    </div>
  );
};

export default PrivacyRequest;
