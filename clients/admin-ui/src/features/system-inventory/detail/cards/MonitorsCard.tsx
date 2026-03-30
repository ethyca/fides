import { Card, Flex, Tag, Text } from "fidesui";

import { MONITOR_STATUS_COLORS } from "../../constants";
import type { MockMonitor } from "../../types";

interface MonitorsCardProps {
  monitors: MockMonitor[];
}

const MonitorsCard = ({ monitors }: MonitorsCardProps) => (
  <Card
    title="Monitors"
    size="small"
    extra={<Text type="secondary" className="cursor-pointer text-xs hover:underline">View all ›</Text>}
  >
    {monitors.length === 0 ? (
      <Text type="secondary">No monitors configured</Text>
    ) : (
      monitors.map((mon) => (
        <Flex
          key={mon.name}
          justify="space-between"
          align="center"
          className="py-2"
        >
          <div>
            <Text strong className="text-sm">
              {mon.name}
            </Text>
            <br />
            <Text type="secondary" className="text-xs">
              {mon.frequency} &middot; Last run{" "}
              {new Date(mon.lastRun).toLocaleDateString()} &middot;{" "}
              {mon.resourceCount} resources
            </Text>
          </div>
          <Tag
            color={MONITOR_STATUS_COLORS[mon.status] as never}
            bordered={false}
          >
            {mon.status.charAt(0).toUpperCase() + mon.status.slice(1)}
          </Tag>
        </Flex>
      ))
    )}
  </Card>
);

export default MonitorsCard;
