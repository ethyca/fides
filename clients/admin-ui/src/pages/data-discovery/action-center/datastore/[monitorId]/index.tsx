import { Icons } from "fidesui";
import { NextPage } from "next";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useDispatch } from "react-redux";

import {
  ACTION_CENTER_DATASTORE_MONITOR_ACTIVITY_ROUTE,
  ACTION_CENTER_DATASTORE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import { useCalcAggregateStatisticsMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { monitorFieldUtil } from "~/features/data-discovery-and-detection/action-center/fields/monitor-fields.slice";
import ActionCenterFields from "~/features/data-discovery-and-detection/action-center/fields/page";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

export const MONITOR_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]: ACTION_CENTER_DATASTORE_MONITOR_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]: ACTION_CENTER_DATASTORE_MONITOR_ROUTE,
} as const;

const DatastoreMonitorResultSystems: NextPage = () => {
  const dispatch = useDispatch();
  const params = useParams<{ monitorId: string }>();
  const [pageSettings, setPageSettings] = useState({
    showIgnored: false,
    showApproved: false,
  });
  const [trigger] = useCalcAggregateStatisticsMutation();

  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      monitorType={APIMonitorType.DATASTORE}
      routeConfig={MONITOR_ACTION_CENTER_CONFIG}
      pageSettings={{
        badgeProps: {
          count: Object.values(pageSettings).flatMap((s) => (s ? [s] : []))
            .length,
          size: "small",
        },
        dropdownProps: {
          trigger: ["click"],
          menu: {
            onDeselect: (info) => {
              setPageSettings({
                showApproved: info.selectedKeys.includes("showApproved")
                  ? false
                  : pageSettings.showApproved,
                showIgnored: info.selectedKeys.includes("showIgnored")
                  ? false
                  : pageSettings.showIgnored,
              });
            },
            onSelect: (info) => {
              setPageSettings({
                showApproved: info.selectedKeys.includes("showApproved")
                  ? true
                  : pageSettings.showApproved,
                showIgnored: info.selectedKeys.includes("showIgnored")
                  ? true
                  : pageSettings.showIgnored,
              });
            },
            selectedKeys: Object.entries(pageSettings).flatMap(
              ([key, value]) => (value ? [key] : []),
            ),
            selectable: true,
            items: [
              {
                key: "showIgnored",
                label: "Show ignored",
                icon: pageSettings.showIgnored && <Icons.Checkmark />,
              },
              {
                key: "showApproved",
                label: "Show approved",
                icon: pageSettings.showApproved && <Icons.Checkmark />,
              },
            ],
          },
        },
      }}
      refresh={async () => {
        dispatch(
          monitorFieldUtil.invalidateTags([
            "Monitor Field Results",
            "Monitor Field Details",
          ]),
        );
        await trigger({
          monitor_config_id: monitorId,
          monitor_type: APIMonitorType.DATASTORE,
        });
      }}
    >
      {loading ? null : (
        <ActionCenterFields monitorId={monitorId} {...pageSettings} />
      )}
    </ActionCenterLayout>
  );
};

export default DatastoreMonitorResultSystems;
