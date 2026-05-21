// PROTOTYPE — delete with TCF history
import { CUSTOM_TAG_COLOR, Flex, List, Tag, Text } from "fidesui";

import {
  EVENT_TYPE_COLOR,
  EVENT_TYPE_LABEL,
  HistoryEvent,
  HistorySource,
} from "./mockHistory";

const getSourceLabel = (source: HistorySource): string =>
  source.kind === "fides" ? "Fides" : source.name;

const formatTimestamp = (iso: string): string => {
  const date = new Date(iso);
  const datePart = date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const timePart = date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
  const tzPart =
    date
      .toLocaleTimeString("en-US", { timeZoneName: "short" })
      .split(" ")
      .pop() ?? "";
  return `${datePart}, ${timePart.toLowerCase()} ${tzPart}`;
};

export const VersionHistoryListItem = ({ event }: { event: HistoryEvent }) => {
  const hashChange = `${event.previousHash ?? "(none)"} → ${event.newHash}`;
  const sourceLabel = getSourceLabel(event.source);

  return (
    <List.Item data-testid={`history-event-${event.id}`}>
      <Flex
        justify="space-between"
        align="center"
        className="w-full"
        gap="middle"
      >
        <Flex vertical gap="small" className="grow">
          <Flex align="center" gap="small" wrap>
            <Tag color={EVENT_TYPE_COLOR[event.type]}>
              {EVENT_TYPE_LABEL[event.type]}
            </Tag>
            <Text type="secondary" style={{ fontSize: "13px" }}>
              {formatTimestamp(event.timestamp)}
            </Text>
          </Flex>
          <Flex align="center" gap="small" wrap>
            <Text type="secondary" style={{ fontSize: "12px" }}>
              Change:
            </Text>
            <Text
              style={{
                fontFamily: "var(--fidesui-font-family-monospace, monospace)",
                fontSize: "12px",
              }}
            >
              {hashChange}
            </Text>
          </Flex>
        </Flex>
        <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>{sourceLabel}</Tag>
      </Flex>
    </List.Item>
  );
};
