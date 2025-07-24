import { AntTabs as Tabs, AntTabsProps as TabsProps } from "fidesui";
import { useMemo, useState } from "react";

import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import { PrivacyRequestStatus } from "~/types/api";

import ActivityTab from "./events-and-logs/ActivityTab";
import PrivacyRequestDetailsManualTaskTab from "./PrivacyRequestDetailsManualTaskTab";
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

  const isRequiringInputStatus =
    subjectRequest.status === PrivacyRequestStatus.REQUIRES_INPUT;
  const showManualTasks = isRequiringInputStatus;

  const [activeTabKey, setActiveTabKey] = useState("activity");

  const items: TabsProps["items"] = useMemo(
    () => [
      {
        key: "activity",
        label: "Activity",
        children: <ActivityTab subjectRequest={subjectRequest} />,
      },
      {
        key: "manual-tasks",
        label: "Manual tasks",
        children: (
          <PrivacyRequestDetailsManualTaskTab
            subjectRequest={subjectRequest}
            onComplete={() => setActiveTabKey("activity")}
          />
        ),
        disabled: !showManualTasks,
      },
    ],
    [showManualTasks, subjectRequest],
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
