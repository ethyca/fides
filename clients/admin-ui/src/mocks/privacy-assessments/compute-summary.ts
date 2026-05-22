import type {
  AssessmentGroupResponse,
  AssessmentSummaryBlockedGroup,
  AssessmentSummaryOwner,
  AssessmentSummaryResponse,
  AssessmentSummarySegment,
  PrivacyAssessmentResponse,
} from "~/features/privacy-assessments/types";
import {
  AssessmentStatus,
  RiskLevel,
} from "~/features/privacy-assessments/types";

const UNCATEGORIZED_KEY = "__uncategorized__";

const EMPTY_SEGMENT_COUNTS: Record<AssessmentSummarySegment, number> = {
  completed: 0,
  pending: 0,
  open: 0,
  risk: 0,
};

function segmentForAssessment(
  assessment: PrivacyAssessmentResponse,
): AssessmentSummarySegment {
  switch (assessment.status) {
    case AssessmentStatus.COMPLETED:
      return "completed";
    case AssessmentStatus.GENERATING:
      return "pending";
    case AssessmentStatus.IN_PROGRESS:
    case AssessmentStatus.OUTDATED:
      return assessment.risk_level === RiskLevel.HIGH ? "risk" : "open";
    default: {
      const exhaustive: never = assessment.status;
      return exhaustive;
    }
  }
}

export function computeSummary(
  groups: AssessmentGroupResponse[],
): AssessmentSummaryResponse {
  const bySegment = { ...EMPTY_SEGMENT_COUNTS };
  const groupAgg = new Map<string, AssessmentSummaryBlockedGroup>();
  const ownerAgg = new Map<string, AssessmentSummaryOwner>();
  let total = 0;

  groups.forEach((group) => {
    const groupKey = group.data_use ?? UNCATEGORIZED_KEY;
    let aggregate = groupAgg.get(groupKey);
    if (!aggregate) {
      aggregate = {
        name: group.data_use_name ?? "Uncategorized",
        outdated_count: 0,
        high_risk_count: 0,
        total_count: 0,
      };
      groupAgg.set(groupKey, aggregate);
    }

    group.assessments?.forEach((assessment) => {
      total += 1;
      aggregate!.total_count += 1;
      bySegment[segmentForAssessment(assessment)] += 1;
      if (assessment.risk_level === RiskLevel.HIGH) {
        aggregate!.high_risk_count += 1;
      }
      const isOutdated = assessment.status === AssessmentStatus.OUTDATED;
      if (isOutdated) {
        aggregate!.outdated_count += 1;
      }

      const isOpen =
        assessment.status === AssessmentStatus.IN_PROGRESS ||
        assessment.status === AssessmentStatus.OUTDATED;
      if (isOpen && assessment.created_by) {
        let owner = ownerAgg.get(assessment.created_by);
        if (!owner) {
          owner = {
            owner: assessment.created_by,
            open_count: 0,
            outdated_count: 0,
          };
          ownerAgg.set(assessment.created_by, owner);
        }
        owner.open_count += 1;
        if (isOutdated) {
          owner.outdated_count += 1;
        }
      }
    });
  });

  const blockedGroups = Array.from(groupAgg.values())
    .filter((g) => g.outdated_count > 0 || g.high_risk_count > 0)
    .sort(
      (a, b) =>
        b.outdated_count +
        b.high_risk_count -
        (a.outdated_count + a.high_risk_count),
    );

  const owners = Array.from(ownerAgg.values()).sort(
    (a, b) => b.open_count - a.open_count,
  );

  return {
    total,
    by_segment: bySegment,
    blocked_groups: blockedGroups,
    owners,
  };
}
