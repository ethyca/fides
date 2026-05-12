import { skipToken } from "@reduxjs/toolkit/query";
import { Descriptions, Flex, Paragraph, Text } from "fidesui";

import { useFlags } from "~/features/common/features";
import { RouterLink } from "~/features/common/nav/RouterLink";
import {
  EDIT_SYSTEM_ROUTE,
  INTEGRATION_DETAIL_ROUTE,
} from "~/features/common/nav/routes";

import {
  useGetConnectionQuery,
  useGetMonitorConfigQuery,
} from "./action-center.slice";

export interface MonitorDetailsWidgetProps {
  monitorId: string;
}

const MonitorDetailsWidget = ({ monitorId }: MonitorDetailsWidgetProps) => {
  const {
    flags: { heliosInsights },
  } = useFlags();
  const { data: configData } = useGetMonitorConfigQuery(
    {
      monitor_config_id: monitorId,
    },
    {
      refetchOnMountOrArgChange: true,
    },
  );
  const connectionKey = configData?.connection_config_key;
  const { data: connectionData } = useGetConnectionQuery(
    connectionKey ? { connection_key: connectionKey } : skipToken,
  );

  return (
    heliosInsights && (
      <Flex className="w-full" gap="middle" vertical>
        <Text strong>Details</Text>
        <Descriptions
          size="small"
          items={[
            {
              label: "System",
              children:
                connectionData?.linked_systems &&
                connectionData.linked_systems.length > 0 ? (
                  <Paragraph
                    ellipsis={{
                      rows: 1,
                      tooltip: { title: connectionData?.system_key },
                    }}
                  >
                    {connectionData?.linked_systems?.map((linkedSystem) => (
                      <RouterLink
                        key={linkedSystem.fides_key}
                        href={EDIT_SYSTEM_ROUTE.replace(
                          "[id]",
                          linkedSystem.fides_key,
                        )}
                      >
                        {" "}
                        {linkedSystem.name}
                      </RouterLink>
                    ))}
                  </Paragraph>
                ) : (
                  "None"
                ),
              span: "filled",
            },
            {
              label: "Integration",
              children: (
                <Paragraph
                  ellipsis={{
                    rows: 1,
                    tooltip: { title: connectionData?.key },
                  }}
                >
                  <RouterLink
                    href={INTEGRATION_DETAIL_ROUTE.replace(
                      "[id]",
                      connectionData?.key ?? "",
                    )}
                  >
                    {connectionData?.key}
                  </RouterLink>
                </Paragraph>
              ),
              span: "filled",
            },
          ]}
        />
      </Flex>
    )
  );
};

export default MonitorDetailsWidget;
