import { Flex, Text } from "fidesui";

import styles from "./AssessmentProgressLegend.module.scss";
import {
  ANSWER_SOURCE_BUCKET_COLORS,
  ANSWER_SOURCE_BUCKET_LABELS,
  type AnswerSourceBucket,
  type GroupedAnswerCounts,
} from "./utils";

interface AssessmentProgressLegendProps {
  breakdown: GroupedAnswerCounts;
  /**
   * Compact spacing for the card; full spacing for larger surfaces.
   */
  compact?: boolean;
}

const BUCKET_ORDER: AnswerSourceBucket[] = ["agent", "slack", "manual"];

/**
 * Renders one chip per non-zero answer-source bucket: a coloured dot, the
 * bucket label, and the count. Renders nothing when every bucket is empty —
 * the 0% label on the progress bar already communicates that state.
 *
 * Keep the bucket colours and labels in sync with the ``segments`` array
 * built in ``AssessmentCard`` — both read from the same maps in ``utils.ts``.
 */
export const AssessmentProgressLegend = ({
  breakdown,
  compact = false,
}: AssessmentProgressLegendProps) => {
  const entries = BUCKET_ORDER.filter((bucket) => breakdown[bucket] > 0);

  if (entries.length === 0) {
    return null;
  }

  return (
    <Flex gap={compact ? 8 : 12} align="center" wrap="wrap">
      {entries.map((bucket) => (
        <Flex key={bucket} align="center" gap={4} className={styles.entry}>
          <span
            className={styles.dot}
            style={{ backgroundColor: ANSWER_SOURCE_BUCKET_COLORS[bucket] }}
          />
          <Text variant="monoLabel" type="secondary" size="sm">
            {ANSWER_SOURCE_BUCKET_LABELS[bucket]}
          </Text>
          <Text variant="monoLabel" size="sm" strong>
            {breakdown[bucket]}
          </Text>
        </Flex>
      ))}
    </Flex>
  );
};
