import { Tabs, TabsProps } from "fidesui";
import { useMemo, useState } from "react";

import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import { PrivacyRequestStatus } from "~/types/api";

import PrivacyRequestDetailsAccessPackageTab from "./access-package/PrivacyRequestDetailsAccessPackageTab";
import ActivityTab from "./events-and-logs/ActivityTab";
import PrivacyRequestDetailsManualTaskTab from "./PrivacyRequestDetailsManualTaskTab";
import RequestDetails from "./RequestDetails";
import { PrivacyRequestEntity } from "./types";

type PrivacyRequestProps = {
  data: PrivacyRequestEntity;
};

const TERMINAL_STATES = [
  PrivacyRequestStatus.COMPLETE,
  PrivacyRequestStatus.CANCELED,
  PrivacyRequestStatus.DENIED,
  PrivacyRequestStatus.ERROR,
];

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
    pollingInterval: !TERMINAL_STATES.includes(initialData.status) ? 2000 : 0,
    skip: !initialData.id,
  });

  // Use latest data if available, otherwise use initial data
  const subjectRequest = latestData?.items[0] ?? initialData;

  const isRequiringInputStatus =
    subjectRequest.status === PrivacyRequestStatus.REQUIRES_INPUT;
  const showManualTasks = isRequiringInputStatus;
  const isAwaitingAccessReview =
    subjectRequest.status === PrivacyRequestStatus.AWAITING_ACCESS_REVIEW;

  // Pick the initial tab based on the request's status at mount time.
  // After mount, never override the user's manual tab selection -- the
  // poll cycles through the same status and would otherwise yank them
  // back here mid-review.
  const [activeTabKey, setActiveTabKey] = useState(() =>
    initialData.status === PrivacyRequestStatus.AWAITING_ACCESS_REVIEW
      ? "access-package"
      : "activity",
  );

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
      {
        key: "access-package",
        label: "Access package",
        children: (
          <PrivacyRequestDetailsAccessPackageTab
            subjectRequest={subjectRequest}
          />
        ),
        disabled: !isAwaitingAccessReview,
      },
    ],
    [showManualTasks, isAwaitingAccessReview, subjectRequest],
  );

  return (
    <div className="flex gap-8">
      <div className="w-0 grow">
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
