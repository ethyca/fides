import { Collapse, Flex, List, Space, Tag, Text } from "fidesui";

import styles from "./EvidenceSection.module.scss";
import {
  EvidenceItem,
  EvidenceType,
  ManualEntryEvidenceItem,
  QuestionGroup,
  SlackCommunicationEvidenceItem,
  SystemEvidenceItem,
} from "./types";

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

export interface EvidenceSectionProps {
  groupId: string;
  group: QuestionGroup | undefined;
  evidence: EvidenceItem[];
}

export const EvidenceSection = ({
  groupId,
  group,
  evidence,
}: EvidenceSectionProps) => {
  if (!group) {
    return null;
  }

  const systemEvidence = evidence.filter(
    (e) => e.type === EvidenceType.SYSTEM,
  ) as SystemEvidenceItem[];
  const manualEvidence = evidence.filter(
    (e) => e.type === EvidenceType.MANUAL_ENTRY,
  ) as ManualEntryEvidenceItem[];
  const slackEvidence = evidence.filter(
    (e) => e.type === EvidenceType.SLACK_COMMUNICATION,
  ) as SlackCommunicationEvidenceItem[];

  return (
    <div data-group-id={groupId}>
      <Text strong className={styles.sectionTitle}>
        {group.id}. {group.title}
      </Text>

      {systemEvidence.length > 0 && (
        <div className={styles.evidenceGroup}>
          <Text strong className={styles.groupHeading}>
            System-derived data
          </Text>
          <Text type="secondary" className={styles.groupDescription}>
            Automated data points extracted from system inventory,
            classifications, and policies.
          </Text>
          <Space direction="vertical" size="small" className={styles.itemList}>
            {systemEvidence.map((item) => (
              <div key={item.id} className={styles.evidenceCard}>
                <Flex
                  justify="space-between"
                  align="flex-start"
                  className={styles.cardHeader}
                >
                  <Text strong size="sm">
                    {item.source.source_name}
                  </Text>
                  {item.citation_number && <Tag>#{item.citation_number}</Tag>}
                </Flex>
                <Text className={styles.cardValue}>
                  <Text type="secondary">{item.field.field_label}: </Text>
                  {item.value_display}
                </Text>
                <Text type="secondary" size="sm" className={styles.cardMeta}>
                  Last updated: {formatTimestamp(item.created_at)}
                </Text>
              </div>
            ))}
          </Space>
        </div>
      )}

      {manualEvidence.length > 0 && (
        <div className={styles.evidenceGroup}>
          <Text strong className={styles.groupHeading}>
            Manual entries
          </Text>
          <Space direction="vertical" size="small" className={styles.itemList}>
            {manualEvidence.map((item) => (
              <div key={item.id} className={styles.evidenceCard}>
                <Flex
                  justify="space-between"
                  align="flex-start"
                  className={styles.cardHeader}
                >
                  <Text strong size="sm">
                    Manual entry
                  </Text>
                  {item.citation_number && <Tag>#{item.citation_number}</Tag>}
                </Flex>
                <Text className={styles.cardValue}>{item.entry.new_value}</Text>
                <Text type="secondary" size="sm" className={styles.cardMeta}>
                  {item.author.user_name}
                  {item.author.role && `, ${item.author.role}`} •{" "}
                  {formatTimestamp(item.created_at)}
                </Text>
              </div>
            ))}
          </Space>
        </div>
      )}

      {slackEvidence.length > 0 && (
        <div className={styles.evidenceGroup}>
          <Text strong className={styles.groupHeading}>
            Stakeholder communications
          </Text>
          <Space direction="vertical" size="small" className={styles.itemList}>
            {slackEvidence.map((item) => (
              <div key={item.id} className={styles.evidenceCard}>
                <Flex
                  justify="space-between"
                  align="flex-start"
                  className={styles.cardHeader}
                >
                  <Text strong size="sm">
                    Slack thread
                  </Text>
                  {item.citation_number && <Tag>#{item.citation_number}</Tag>}
                </Flex>
                {item.summary && (
                  <Text className={styles.cardValue}>{item.summary}</Text>
                )}
                <Text type="secondary" size="sm" className={styles.cardMeta}>
                  {item.channel.channel_name} • {item.thread.message_count}{" "}
                  messages • {formatTimestamp(item.created_at)}
                </Text>
                {item.messages && item.messages.length > 0 && (
                  <Collapse
                    ghost
                    className={styles.threadCollapse}
                    items={[
                      {
                        key: "thread",
                        label: `View ${item.messages.length} message${item.messages.length === 1 ? "" : "s"}`,
                        children: (
                          <List
                            size="small"
                            dataSource={item.messages}
                            renderItem={(msg, index) => (
                              <List.Item
                                className={
                                  index === item.messages.length - 1
                                    ? styles.lastMessage
                                    : styles.message
                                }
                              >
                                <List.Item.Meta
                                  title={
                                    <Flex align="center" gap="small">
                                      <Text strong size="sm">
                                        {msg.sender.display_name}
                                      </Text>
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
                                    </Flex>
                                  }
                                  description={
                                    <Text className={styles.messageText}>
                                      {msg.content.text}
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
            ))}
          </Space>
        </div>
      )}

      {evidence.length === 0 && (
        <Text type="secondary" size="sm">
          No evidence collected yet for this section.
        </Text>
      )}
    </div>
  );
};
