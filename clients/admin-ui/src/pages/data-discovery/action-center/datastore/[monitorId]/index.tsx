import { useState } from "react";
import { Icons } from "fidesui";
import { NextPage } from "next";
import { useParams } from "next/navigation";

import {
  ACTION_CENTER_DATASTORE_MONITOR_ACTIVITY_ROUTE,
  ACTION_CENTER_DATASTORE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import ActionCenterFields from "~/features/data-discovery-and-detection/action-center/fields/page";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";

export const MONITOR_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_DATASTORE_MONITOR_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]: ACTION_CENTER_DATASTORE_MONITOR_ROUTE,
} as const;

const DatastoreMonitorResultSystems: NextPage = () => {
  const params = useParams<{ monitorId: string }>();
  const [pageSettings, setPageSettings] = useState({
    showIgnored: false,
    showApproved: false
  })


  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      routeConfig={MONITOR_ACTION_CENTER_CONFIG}
      pageSettings={
        {
          menu: {
            onSelect: ((info) => setPageSettings({
              showApproved: !!info.selectedKeys.includes('showApproved'),
              showIgnored: !!info.selectedKeys.includes('showApproved')
            })),
            selectedKeys: Object.entries(pageSettings).flatMap(([key, value]) => value ? [key] : []),
            selectable: true,
            items: [{
              key: "showIgnored",
              label: "Show ignored",
              icon: pageSettings.showIgnored && <Icons.Checkmark />
            },
            {
              key: "showApproved",
              label: "Show approved",
              icon: pageSettings.showApproved && <Icons.Checkmark />
            }]
          }
        }
      }

    >
      {loading ? null : <ActionCenterFields monitorId={monitorId} />}
    </ActionCenterLayout>
  );
};

export default DatastoreMonitorResultSystems;
