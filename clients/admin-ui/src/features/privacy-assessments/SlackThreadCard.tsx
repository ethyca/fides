import { Collapse, Flex, Link, List, Text } from "fidesui";

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
    <div className={styles.evidenceCard}>
      <Text strong className={styles.cardTitle}>
        Stakeholder communication
      </Text>
      <Text type="secondary" size="sm" className="block">
        {data.channel || "N/A"} &middot; {data.messages.length} messages
        &middot; {formatDate(item.created_at)}
      </Text>

      {data.thread_url && (
        <Link
          href={data.thread_url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.threadLink}
        >
          View thread in Slack
        </Link>
      )}

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
                        description={<Text size="sm">{msg.text}</Text>}
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
