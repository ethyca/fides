import { Divider, Flex, Text } from "fidesui";

import type { MockSystem } from "../../types";

interface HistoryTabProps {
  system: MockSystem;
}

const HistoryTab = ({ system }: HistoryTabProps) => {
  if (system.history.length === 0) {
    return <Text type="secondary">No activity recorded for this system.</Text>;
  }

  return (
    <Flex vertical style={{ maxWidth: 600 }}>
      {system.history.map((entry, i) => (
        <div key={entry.timestamp}>
          <Flex gap="middle" className="py-3">
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                backgroundColor: "#93969a",
                marginTop: 6,
                flexShrink: 0,
              }}
            />
            <div>
              <Text strong className="text-sm">
                {entry.action}
              </Text>
              <br />
              <Text type="secondary" className="text-xs">
                {entry.detail}
              </Text>
              <br />
              <Text type="secondary" className="text-xs">
                {entry.user} &middot;{" "}
                {new Date(entry.timestamp).toLocaleString()}
              </Text>
            </div>
          </Flex>
          {i < system.history.length - 1 && <Divider className="!my-0" />}
        </div>
      ))}
    </Flex>
  );
};

export default HistoryTab;
