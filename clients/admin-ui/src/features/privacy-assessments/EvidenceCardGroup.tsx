import { Collapse, Flex, Link, List, Space, Text } from "fidesui";

import { formatDate } from "~/features/common/utils";

import { FIELD_NAME_LABELS, SOURCE_TYPE_LABELS } from "./constants";
import styles from "./EvidenceCardGroup.module.scss";
import { EvidenceItem, EvidenceType, SlackMessage } from "./types";

export interface EvidenceCardGroupProps {
  items: EvidenceItem[];
}

const SlackThreadCard = ({ item }: { item: EvidenceItem }) => {
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

export const EvidenceCardGroup = ({ items }: EvidenceCardGroupProps) => (
  <Space direction="vertical" size="small" className={styles.itemList}>
    {items.map((item) =>
      item.type === EvidenceType.TEAM_INPUT ? (
        <SlackThreadCard key={item.id} item={item} />
      ) : (
        <div key={item.id} className={styles.evidenceCard}>
          <Text strong size="sm" className="mb-2 block">
            {SOURCE_TYPE_LABELS[item.source_type] ?? item.source_type}
          </Text>
          <Text className={`mb-2 block ${styles.cardValue}`}>
            <Text type="secondary">
              {FIELD_NAME_LABELS[item.field_name] ??
                item.field_name.replace(/_/g, " ")}
              :{" "}
            </Text>
            {item.value}
          </Text>
          <Text type="secondary" size="sm" className="block">
            {formatDate(item.created_at)}
          </Text>
        </div>
      ),
    )}
  </Space>
);
