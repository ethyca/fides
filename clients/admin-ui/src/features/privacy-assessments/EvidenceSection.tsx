import { Badge, Collapse, Flex, Text } from "fidesui";

import { EvidenceCardGroup } from "./EvidenceCardGroup";
import styles from "./EvidenceSection.module.scss";
import { EvidenceItem, EvidenceType, QuestionGroup } from "./types";

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
        <Text strong className="mb-5 block">
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
      e.type === EvidenceType.TEAM_INPUT,
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
                    color="var(--ant-brand-minos)"
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
                    color="var(--ant-brand-minos)"
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
      <Text strong className="mb-5 block">
        {group.id}. {group.title}
      </Text>
      <div className={styles.collapseWrapper}>
        <Collapse items={collapseItems} ghost />
      </div>
    </div>
  );
};
