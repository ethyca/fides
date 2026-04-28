import classNames from "classnames";
import { Divider, Flex } from "fidesui";

import { useFlags } from "~/features/common/features";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";

import MonitorDetailsWidget from "./MonitorDetailsWidget";
import MonitorProgressWidget from "./MonitorProgressWidget";
import MonitorStatsWidget from "./MonitorStatsWidget";

export interface MonitorStatsProps {
  monitorId?: string;
  monitorType?: APIMonitorType;
}

// Statistics widgets are not yet enabled for cloud infrastructure monitors
const STATS_EXCLUDED_TYPES: Set<string> = new Set([
  APIMonitorType.CLOUD_INFRASTRUCTURE,
]);

const MonitorStats = ({ monitorId, monitorType }: MonitorStatsProps) => {
  const {
    flags: { heliosInsights },
  } = useFlags();

  if (monitorType && STATS_EXCLUDED_TYPES.has(monitorType)) {
    return null;
  }

  return (
    heliosInsights && (
      <Flex className={classNames("w-full")} gap="middle">
        {Object.values(monitorType ? [monitorType] : APIMonitorType)
          .filter((mType) => !STATS_EXCLUDED_TYPES.has(mType))
          .toReversed()
          .map((mType) => (
            <MonitorProgressWidget
              monitorType={mType}
              monitorId={monitorId}
              key={mType}
            />
          ))
          .reduce(
            (prev, curr) => [
              prev,
              ...(prev[0]
                ? [
                    <Divider
                      vertical
                      className="h-full"
                      key={`${curr.key}--divider`}
                    />,
                  ]
                : []),
              curr,
            ],
            [] as React.ReactNode[],
          )}
        {monitorId && monitorType && (
          <>
            <Divider vertical className="h-full" />
            <MonitorStatsWidget
              monitorType={monitorType}
              monitorId={monitorId}
            />
            <Divider vertical className="h-full" />
            <MonitorDetailsWidget monitorId={monitorId} />
          </>
        )}
      </Flex>
    )
  );
};

export default MonitorStats;
