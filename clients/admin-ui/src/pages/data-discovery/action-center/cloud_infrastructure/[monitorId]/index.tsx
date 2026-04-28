import { Icons } from "fidesui";
import { NextPage } from "next";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useDispatch } from "react-redux";

import {
  ACTION_CENTER_CLOUD_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  ACTION_CENTER_CLOUD_INFRASTRUCTURE_MONITOR_ROUTE,
} from "~/features/common/nav/routes";
import ActionCenterLayout from "~/features/data-discovery-and-detection/action-center/ActionCenterLayout";
import { ActionCenterRoute } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import { CloudInfraResourcesTable } from "~/features/data-discovery-and-detection/action-center/tables/CloudInfraResourcesTable";
import { discoveryDetectionUtil } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

export const MONITOR_CLOUD_INFRASTRUCTURE_ACTION_CENTER_CONFIG = {
  [ActionCenterRoute.ACTIVITY]:
    ACTION_CENTER_CLOUD_INFRASTRUCTURE_MONITOR_ACTIVITY_ROUTE,
  [ActionCenterRoute.ATTENTION_REQUIRED]:
    ACTION_CENTER_CLOUD_INFRASTRUCTURE_MONITOR_ROUTE,
} as const;

const CloudInfrastructureMonitorResults: NextPage = () => {
  const params = useParams<{ monitorId: string }>();
  const dispatch = useDispatch();

  const monitorId = params?.monitorId
    ? decodeURIComponent(params.monitorId)
    : undefined;
  const loading = !monitorId;
  const [pageSettings, setPageSettings] = useState({
    showIgnored: false,
    showApproved: false,
  });

  return (
    <ActionCenterLayout
      monitorId={monitorId}
      monitorType={APIMonitorType.CLOUD_INFRASTRUCTURE}
      routeConfig={MONITOR_CLOUD_INFRASTRUCTURE_ACTION_CENTER_CONFIG}
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
          discoveryDetectionUtil.invalidateTags([
            "Cloud Infra Monitor Results",
          ]),
        );
      }}
    >
      {loading ? null : (
        <CloudInfraResourcesTable monitorId={monitorId} {...pageSettings} />
      )}
    </ActionCenterLayout>
  );
};

export default CloudInfrastructureMonitorResults;
