import { Badge, Collapse, Flex, Space, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { FIELD_NAME_LABELS, SOURCE_TYPE_LABELS } from "./constants";
import styles from "./EvidenceSection.module.scss";
import { EvidenceItem, EvidenceType, QuestionGroup } from "./types";

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

interface EvidenceCardGroupProps {
  items: EvidenceItem[];
}

const EvidenceCardGroup = ({ items }: EvidenceCardGroupProps) => (
  <Space direction="vertical" size="small" className={styles.itemList}>
    {items.map((item) => (
      <div key={item.id} className={styles.evidenceCard}>
        <Text strong size="sm" className={styles.cardHeader}>
          {getSourceTypeLabel(item.source_type)}
        </Text>
        <Text className={styles.cardValue}>
          <Text type="secondary">{getFieldNameLabel(item.field_name)}: </Text>
          {item.value}
        </Text>
        <Text type="secondary" size="sm" className={styles.cardMeta}>
          {formatTimestamp(item.created_at)}
        </Text>
      </div>
    ))}
  </Space>
);

export interface EvidenceSectionProps {
  groupId: string;
  group: QuestionGroup | undefined;
  evidence: EvidenceItem[];
  searchQuery?: string;
}

export const EvidenceSection = ({
  groupId,
  group,
  evidence,
  searchQuery,
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
          {searchQuery
            ? `No evidence matches "${searchQuery.length > 50 ? `${searchQuery.slice(0, 50)}…` : searchQuery}".`
            : "No evidence collected yet for this section."}
        </Text>
      </div>
    );
  }

  const systemItems = evidence.filter(
    (e) =>
      e.type === EvidenceType.SYSTEM || e.type === EvidenceType.AI_ANALYSIS,
  );
  const humanItems = evidence.filter(
    (e) =>
      e.type === EvidenceType.MANUAL_ENTRY ||
      e.type === EvidenceType.SLACK_COMMUNICATION,
  );

  const collapseItems = [
    ...(systemItems.length > 0
      ? [
          {
            key: "system",
            label: (
              <div>
                <Flex align="center" gap="small" className="mb-1">
                  <Text strong>System-derived data</Text>
                  <Badge
                    count={systemItems.length}
                    color={palette.FIDESUI_MINOS}
                  />
                </Flex>
                <Text type="secondary" size="sm">
                  Automated data points extracted from system inventory,
                  classifications, policies, and monitoring systems.
                </Text>
              </div>
            ),
            children: <EvidenceCardGroup items={systemItems} />,
          },
        ]
      : []),
    ...(humanItems.length > 0
      ? [
          {
            key: "human",
            label: (
              <div>
                <Flex align="center" gap="small" className="mb-1">
                  <Text strong>Human input</Text>
                  <Badge
                    count={humanItems.length}
                    color={palette.FIDESUI_MINOS}
                  />
                </Flex>
                <Text type="secondary" size="sm">
                  Manual entries and stakeholder communications that inform this
                  assessment.
                </Text>
              </div>
            ),
            children: <EvidenceCardGroup items={humanItems} />,
          },
        ]
      : []),
  ];

  return (
    <div data-group-id={groupId}>
      <Text strong className={styles.sectionTitle}>
        {group.id}. {group.title}
      </Text>
      <Collapse items={collapseItems} ghost />
    </div>
  );
};
