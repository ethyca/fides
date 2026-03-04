import { Flex, Space, Tag, Text } from "fidesui";

import styles from "./EvidenceSection.module.scss";
import { EvidenceItem, QuestionGroup } from "./types";

const SOURCE_TYPE_LABELS: Record<string, string> = {
  system: "System",
  privacy_declaration: "Privacy declaration",
  data_category: "Data category",
  data_use: "Data use",
  data_subject: "Data subject",
  dataset: "Dataset",
  data_flow: "Data flow",
  connection: "Connection",
};

const FIELD_NAME_LABELS: Record<string, string> = {
  name: "Name",
  description: "Description",
  data_use: "Data use",
  data_categories: "Data categories",
  data_subjects: "Data subjects",
  retention_period: "Retention period",
  third_parties: "Third parties",
};

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

const getSourceTypeLabel = (sourceType: string) =>
  SOURCE_TYPE_LABELS[sourceType] ?? sourceType;

const getFieldNameLabel = (fieldName: string) =>
  FIELD_NAME_LABELS[fieldName] ?? fieldName.replace(/_/g, " ");

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

  if (evidence.length === 0) {
    return (
      <div data-group-id={groupId}>
        <Text strong className={styles.sectionTitle}>
          {group.id}. {group.title}
        </Text>
        <Text type="secondary" size="sm">
          No evidence collected yet for this section.
        </Text>
      </div>
    );
  }

  const bySourceType = evidence.reduce<Record<string, EvidenceItem[]>>(
    (acc, item) => {
      const key = item.source_type;
      return {
        ...acc,
        [key]: [...(acc[key] ?? []), item],
      };
    },
    {},
  );

  return (
    <div data-group-id={groupId}>
      <Text strong className={styles.sectionTitle}>
        {group.id}. {group.title}
      </Text>

      {Object.entries(bySourceType).map(([sourceType, items]) => (
        <div key={sourceType} className={styles.evidenceGroup}>
          <Text strong className={styles.groupHeading}>
            {getSourceTypeLabel(sourceType)}
          </Text>
          <Space direction="vertical" size="small" className={styles.itemList}>
            {items.map((item) => (
              <div key={item.id} className={styles.evidenceCard}>
                <Flex
                  justify="space-between"
                  align="flex-start"
                  className={styles.cardHeader}
                >
                  <Text strong size="sm">
                    {item.source_key}
                  </Text>
                  {item.citation_number && <Tag>#{item.citation_number}</Tag>}
                </Flex>
                <Text className={styles.cardValue}>
                  <Text type="secondary">
                    {getFieldNameLabel(item.field_name)}:{" "}
                  </Text>
                  {item.value}
                </Text>
                <Text type="secondary" size="sm" className={styles.cardMeta}>
                  {formatTimestamp(item.created_at)}
                </Text>
              </div>
            ))}
          </Space>
        </div>
      ))}
    </div>
  );
};
