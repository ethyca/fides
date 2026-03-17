import { Collapse, Flex, List, Text } from "fidesui";

import { formatDate, pluralize } from "~/features/common/utils";

import styles from "./SlackThreadCard.module.scss";
import { EvidenceItem, SlackMessage } from "./types";

interface SlackThreadCardProps {
  item: EvidenceItem;
}

export const SlackThreadCard = ({ item }: SlackThreadCardProps) => {
  const { data } = item;
  if (!data) {
    return null;
  }
  return (
    <div className={styles.slackCard}>
      <Text strong size="sm" className="mb-2 block">
        Stakeholder communication
      </Text>

      <Text size="sm" className="mb-2 block">
        {item.value}
      </Text>

      <Text type="secondary" size="sm" className="block">
        {data.channel || "N/A"} &middot; {data.messages.length}{" "}
        {pluralize(data.messages.length, "message", "messages")} &middot;{" "}
        {formatDate(item.created_at)}
      </Text>

      {data.messages.length > 0 && (
        <Collapse
          ghost
          className="mt-2"
          items={[
            {
              key: "thread",
              label: `View ${data.messages.length} ${pluralize(data.messages.length, "message", "messages")}`,
              children: (
                <List
                  size="small"
                  dataSource={data.messages}
                  renderItem={(msg: SlackMessage) => (
                    <List.Item className={styles.messageItem}>
                      <List.Item.Meta
                        title={
                          <Flex align="center" gap="small">
                            <Text strong size="sm">
                              {msg.sender}
                            </Text>
                            {msg.timestamp && (
                              <Text type="secondary" size="sm">
                                {new Date(msg.timestamp).toLocaleString(
                                  "en-US",
                                  {
                                    month: "short",
                                    day: "numeric",
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  },
                                )}
                              </Text>
                            )}
                          </Flex>
                        }
                        description={
                          <Text size="sm" className="mt-1 block">
                            {msg.text}
                          </Text>
                        }
                      />
                    </List.Item>
                  )}
                />
              ),
            },
          ]}
        />
      )}
    </div>
  );
};
