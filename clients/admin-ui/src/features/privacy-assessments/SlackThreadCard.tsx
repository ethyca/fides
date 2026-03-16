import { Collapse, Flex, List, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { formatDate } from "~/features/common/utils";

import styles from "./EvidenceCardGroup.module.scss";
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
      <Text
        strong
        style={{ fontSize: 13, color: "#1A1F36", display: "block" }}
        className={styles.cardTitle}
      >
        Stakeholder communication
      </Text>

      <Text
        style={{
          fontSize: 13,
          color: "#4B5563",
          display: "block",
          lineHeight: 1.5,
          marginBottom: 8,
        }}
      >
        {item.value}
      </Text>

      <Text type="secondary" style={{ fontSize: 12, display: "block" }}>
        {data.channel || "N/A"} &middot; {data.messages.length} messages
        &middot; {formatDate(item.created_at)}
      </Text>

      {data.messages.length > 0 && (
        <Collapse
          ghost
          className={styles.messageCollapse}
          items={[
            {
              key: "thread",
              label: `View ${data.messages.length} message${data.messages.length === 1 ? "" : "s"}`,
              children: (
                <List
                  size="small"
                  dataSource={data.messages}
                  renderItem={(msg: SlackMessage) => (
                    <List.Item
                      style={{
                        padding: "8px 0",
                        borderBottom: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
                      }}
                    >
                      <List.Item.Meta
                        title={
                          <Flex align="center" gap="small">
                            <Text strong style={{ fontSize: 12 }}>
                              {msg.sender}
                            </Text>
                            {msg.timestamp && (
                              <Text type="secondary" style={{ fontSize: 11 }}>
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
                          <Text style={{ fontSize: 13, marginTop: 4 }}>
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
