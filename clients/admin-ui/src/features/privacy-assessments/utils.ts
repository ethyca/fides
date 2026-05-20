import { FIELD_NAME_LABELS, SOURCE_TYPE_LABELS } from "./constants";
import type {
  AnswerSourceBreakdown,
  AssessmentFilterKey,
  AssessmentTaskResponse,
  EvidenceItem,
  PrivacyAssessmentResponse,
} from "./types";
import {
  AssessmentStatus,
  DerivedAssessmentStatus,
  EvidenceType,
  QuestionnaireSessionStatus,
  RiskLevel,
} from "./types";

export const getInitials = (name: string) =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();

export const formatSystems = (task: AssessmentTaskResponse | null): string => {
  if (!task) {
    return "—";
  }

  // Prefer systems array with name fallback to fides_key
  if (task.systems && task.systems.length > 0) {
    return task.systems
      .map((system) => system.name ?? system.fides_key)
      .join(", ");
  }

  // Fall back to system_fides_keys
  if (task.system_fides_keys && task.system_fides_keys.length > 0) {
    return task.system_fides_keys.join(", ");
  }

  return "All systems";
};

export const formatTypes = (
  assessmentTypes: string[],
  namesMap?: Record<string, string>,
): string => {
  if (assessmentTypes.length === 0) {
    return "—";
  }
  return assessmentTypes.map((t) => namesMap?.[t] ?? t).join(", ");
};

export const deduplicateEvidence = (items: EvidenceItem[]): EvidenceItem[] => {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = `${item.source_type}|${item.source_key}|${item.field_name}|${item.value}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};

const matchesQuery = (item: EvidenceItem, lower: string): boolean => {
  if (item.type === EvidenceType.TEAM_INPUT) {
    return (
      !!item.value?.toLowerCase().includes(lower) ||
      !!item.data?.channel?.toLowerCase().includes(lower) ||
      !!item.data?.messages.some(
        (msg) =>
          msg.sender.toLowerCase().includes(lower) ||
          msg.text.toLowerCase().includes(lower),
      )
    );
  }
  return (
    !!item.value?.toLowerCase().includes(lower) ||
    !!(
      item.source_type &&
      (SOURCE_TYPE_LABELS[item.source_type] ?? item.source_type)
        .toLowerCase()
        .includes(lower)
    ) ||
    !!(
      item.field_name &&
      (FIELD_NAME_LABELS[item.field_name] ?? item.field_name.replace(/_/g, " "))
        .toLowerCase()
        .includes(lower)
    )
  );
};

export const filterEvidence = (
  items: EvidenceItem[],
  query: string,
): EvidenceItem[] => {
  if (!query.trim()) {
    return items;
  }
  const lower = query.toLowerCase();
  return items.filter((item) => matchesQuery(item, lower));
};

type DeriveStatusInput = Pick<
  PrivacyAssessmentResponse,
  "status" | "questionnaire_status"
>;

/**
 * Resolve the badge value shown on an assessment card from the orthogonal
 * signals the backend exposes. Priority:
 *
 * 1. ``GENERATING`` — initial agent draft pass is in flight.
 * 2. ``SLACK_GATHERING`` — a Slack questionnaire session is currently open.
 * 3. ``SLACK_STOPPED`` — a Slack session was abandoned and the assessment
 *    still needs answers (only overrides ``IN_PROGRESS``; completed / outdated
 *    assessments don't surface old questionnaire history).
 * 4. Otherwise mirror ``AssessmentStatus`` 1:1.
 *
 * Callers should store the result as ``derivedStatus`` and key off the
 * ``STATUS_BADGE_*`` records in ``constants.ts``.
 */
export const deriveAssessmentStatus = (
  assessment: DeriveStatusInput,
): DerivedAssessmentStatus => {
  if (assessment.status === AssessmentStatus.GENERATING) {
    return DerivedAssessmentStatus.GENERATING;
  }
  if (assessment.questionnaire_status === QuestionnaireSessionStatus.IN_PROGRESS) {
    return DerivedAssessmentStatus.SLACK_GATHERING;
  }
  if (
    assessment.status === AssessmentStatus.IN_PROGRESS &&
    assessment.questionnaire_status === QuestionnaireSessionStatus.STOPPED
  ) {
    return DerivedAssessmentStatus.SLACK_STOPPED;
  }
  switch (assessment.status) {
    case AssessmentStatus.COMPLETED:
      return DerivedAssessmentStatus.COMPLETED;
    case AssessmentStatus.OUTDATED:
      return DerivedAssessmentStatus.OUTDATED;
    case AssessmentStatus.IN_PROGRESS:
    default:
      return DerivedAssessmentStatus.IN_PROGRESS;
  }
};

/**
 * Single predicate used by both the filter chip counts and the actual
 * filtering pass on the assessments list. Routing both through here keeps
 * the visible badge, the chip totals, and the cards on screen consistent.
 *
 * Filter semantics:
 * - ``all`` — always true.
 * - ``needs_input`` — derived status is ``IN_PROGRESS`` (slack / drafting
 *   cards have their own chips).
 * - ``agent_drafting`` — derived status is ``GENERATING``.
 * - ``slack`` — any Slack-derived state (``SLACK_GATHERING`` or
 *   ``SLACK_STOPPED``).
 * - ``high_risk`` — risk level is ``HIGH``, regardless of status.
 * - ``signed`` — derived status is ``COMPLETED``.
 */
export const assessmentMatchesFilter = (
  assessment: PrivacyAssessmentResponse,
  filter: AssessmentFilterKey,
): boolean => {
  if (filter === "all") {
    return true;
  }
  if (filter === "high_risk") {
    return assessment.risk_level === RiskLevel.HIGH;
  }
  const derived = deriveAssessmentStatus(assessment);
  switch (filter) {
    case "needs_input":
      return derived === DerivedAssessmentStatus.IN_PROGRESS;
    case "agent_drafting":
      return derived === DerivedAssessmentStatus.GENERATING;
    case "slack":
      return (
        derived === DerivedAssessmentStatus.SLACK_GATHERING ||
        derived === DerivedAssessmentStatus.SLACK_STOPPED
      );
    case "signed":
      return derived === DerivedAssessmentStatus.COMPLETED;
    default:
      return false;
  }
};

/**
 * UI buckets used by the progress-bar segments and the legend. The backend
 * has four ``AnswerSource`` values; we fold them into three display buckets:
 *
 * - ``agent`` — ``system`` + ``ai_analysis`` (everything the agent produced
 *   on its own, whether deterministic or LLM-derived)
 * - ``slack`` — ``team_input`` (answers gathered from SMEs via Slack)
 * - ``manual`` — ``user_input`` (direct human edits in the UI)
 *
 * Use this single helper for both the segments array and the legend so the
 * two surfaces always show consistent counts.
 */
export type AnswerSourceBucket = "agent" | "slack" | "manual";

export interface GroupedAnswerCounts {
  agent: number;
  slack: number;
  manual: number;
}

export const groupAnswersBySource = (
  breakdown: AnswerSourceBreakdown | null | undefined,
): GroupedAnswerCounts => ({
  agent: (breakdown?.system ?? 0) + (breakdown?.ai_analysis ?? 0),
  slack: breakdown?.team_input ?? 0,
  manual: breakdown?.user_input ?? 0,
});

/**
 * Token colours for each bucket. Reuses existing fidesui tokens — terracotta
 * for the Slack channel (matches the brand accent), neutral-500 for the
 * agent's mid-gray (closest to the prototype's ``rgba(43,46,53,0.55)``), and
 * the canonical text colour for manual entries. Promote to dedicated
 * provenance tokens if these reappear outside the assessments page.
 */
export const ANSWER_SOURCE_BUCKET_COLORS: Record<AnswerSourceBucket, string> = {
  agent: "var(--fidesui-neutral-500)",
  slack: "var(--fidesui-brand-terracotta)",
  manual: "var(--fidesui-color-text)",
};

export const ANSWER_SOURCE_BUCKET_LABELS: Record<AnswerSourceBucket, string> = {
  agent: "Agent",
  slack: "Slack",
  manual: "Manual",
};
