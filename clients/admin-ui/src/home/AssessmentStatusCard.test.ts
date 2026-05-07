import { describe, expect, it } from "@jest/globals";

import { AssessmentStatus, RiskLevel } from "~/features/privacy-assessments";
import type {
  AssessmentGroupResponse,
  PrivacyAssessmentResponse,
} from "~/features/privacy-assessments/types";

import { computeMetrics } from "./AssessmentStatusCard";

const NOW = Date.UTC(2026, 4, 1);
const DAY_MS = 24 * 60 * 60 * 1000;

function isoDaysAgo(days: number): string {
  return new Date(NOW - days * DAY_MS).toISOString();
}

function makeAssessment(
  overrides: Partial<PrivacyAssessmentResponse> = {},
): PrivacyAssessmentResponse {
  return {
    id: overrides.id ?? "pri-test",
    template_id: "tpl",
    name: "Test assessment",
    status: AssessmentStatus.IN_PROGRESS,
    risk_level: null,
    ...overrides,
  } as PrivacyAssessmentResponse;
}

function makeGroup(
  dataUse: string | null,
  dataUseName: string | null,
  assessments: PrivacyAssessmentResponse[],
): AssessmentGroupResponse {
  return {
    data_use: dataUse,
    data_use_name: dataUseName,
    system_count: assessments.length,
    assessments,
  };
}

describe("computeMetrics", () => {
  it("returns zeroed metrics for undefined or empty input", () => {
    expect(computeMetrics(undefined, NOW)).toEqual({
      total: 0,
      bySegment: { completed: 0, pending: 0, open: 0, risk: 0 },
      topBlocked: [],
      blockedGroupOverflow: 0,
      topOwners: [],
      ownerOverflow: 0,
    });
    expect(computeMetrics([], NOW).total).toBe(0);
  });

  it("partitions assessments into the four segment buckets", () => {
    const groups = [
      makeGroup("ads", "Ads", [
        makeAssessment({ id: "1", status: AssessmentStatus.COMPLETED }),
        makeAssessment({
          id: "2",
          status: AssessmentStatus.COMPLETED,
          risk_level: RiskLevel.HIGH,
        }),
        makeAssessment({ id: "3", status: AssessmentStatus.GENERATING }),
        makeAssessment({
          id: "4",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.HIGH,
        }),
        makeAssessment({
          id: "5",
          status: AssessmentStatus.OUTDATED,
          risk_level: RiskLevel.HIGH,
        }),
        makeAssessment({ id: "6", status: AssessmentStatus.IN_PROGRESS }),
        makeAssessment({
          id: "7",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.MEDIUM,
        }),
        makeAssessment({ id: "8", status: AssessmentStatus.OUTDATED }),
      ]),
    ];

    const { bySegment, total } = computeMetrics(groups, NOW);
    expect(total).toBe(8);
    expect(bySegment).toEqual({
      completed: 2,
      pending: 1,
      open: 3,
      risk: 2,
    });
  });

  it("treats GENERATING and missing-timestamp rows as not stale", () => {
    const groups = [
      makeGroup("ads", "Ads", [
        // Stale: open and updated long ago
        makeAssessment({
          id: "stale",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.HIGH,
          updated_at: isoDaysAgo(30),
        }),
        // GENERATING with old timestamp must not be stale
        makeAssessment({
          id: "gen-old",
          status: AssessmentStatus.GENERATING,
          updated_at: isoDaysAgo(60),
        }),
        // Open with no updated_at must not be stale
        makeAssessment({
          id: "no-ts",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.HIGH,
          updated_at: null,
        }),
        // Completed with old timestamp must not be stale
        makeAssessment({
          id: "done-old",
          status: AssessmentStatus.COMPLETED,
          updated_at: isoDaysAgo(60),
        }),
      ]),
    ];

    const metrics = computeMetrics(groups, NOW);
    expect(metrics.topBlocked).toHaveLength(1);
    expect(metrics.topBlocked[0].staleCount).toBe(1);
    // 3 total flagged for the group: 2 high-risk + 1 stale
    expect(metrics.topBlocked[0].highRiskCount).toBe(2);
  });

  it("aggregates groups by stable data_use key, not display name", () => {
    const groups = [
      // Two distinct data_use ids that happen to share a display name —
      // they must remain separate buckets.
      makeGroup("ads.first", "Advertising", [
        makeAssessment({
          id: "a1",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.HIGH,
        }),
      ]),
      makeGroup("ads.third", "Advertising", [
        makeAssessment({
          id: "a2",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.HIGH,
        }),
      ]),
      // Two null data_use groups — they should merge into one Uncategorized bucket.
      makeGroup(null, null, [
        makeAssessment({
          id: "u1",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.HIGH,
        }),
      ]),
      makeGroup(null, null, [
        makeAssessment({
          id: "u2",
          status: AssessmentStatus.IN_PROGRESS,
          risk_level: RiskLevel.HIGH,
        }),
      ]),
    ];

    const { topBlocked } = computeMetrics(groups, NOW);
    expect(topBlocked).toHaveLength(3);
    const names = topBlocked.map((g) => g.name).sort();
    expect(names).toEqual(["Advertising", "Advertising", "Uncategorized"]);
    const uncat = topBlocked.find((g) => g.name === "Uncategorized");
    expect(uncat?.totalCount).toBe(2);
  });

  it("ranks blocked groups by stale + high-risk and reports overflow", () => {
    const groups = Array.from({ length: 5 }, (_, i) =>
      makeGroup(`u${i}`, `Group ${i}`, [
        // Each subsequent group has fewer attention signals.
        ...Array.from({ length: 5 - i }, (__, j) =>
          makeAssessment({
            id: `g${i}-${j}`,
            status: AssessmentStatus.IN_PROGRESS,
            risk_level: RiskLevel.HIGH,
          }),
        ),
      ]),
    );

    const { topBlocked, blockedGroupOverflow } = computeMetrics(groups, NOW);
    expect(topBlocked).toHaveLength(3);
    expect(topBlocked.map((g) => g.name)).toEqual([
      "Group 0",
      "Group 1",
      "Group 2",
    ]);
    expect(blockedGroupOverflow).toBe(2);
  });

  it("aggregates owners only for open assessments and reports overflow", () => {
    const groups = [
      makeGroup("ads", "Ads", [
        // alice has 3 open: 2 IN_PROGRESS + 1 OUTDATED, 1 stale
        makeAssessment({
          id: "a1",
          created_by: "alice",
          status: AssessmentStatus.IN_PROGRESS,
        }),
        makeAssessment({
          id: "a2",
          created_by: "alice",
          status: AssessmentStatus.IN_PROGRESS,
          updated_at: isoDaysAgo(30),
        }),
        makeAssessment({
          id: "a3",
          created_by: "alice",
          status: AssessmentStatus.OUTDATED,
        }),
        // alice's completed assessment must not increase open count
        makeAssessment({
          id: "a4",
          created_by: "alice",
          status: AssessmentStatus.COMPLETED,
        }),
        // bob has 2 open
        makeAssessment({
          id: "b1",
          created_by: "bob",
          status: AssessmentStatus.IN_PROGRESS,
        }),
        makeAssessment({
          id: "b2",
          created_by: "bob",
          status: AssessmentStatus.IN_PROGRESS,
        }),
        // charlie has 1 open
        makeAssessment({
          id: "c1",
          created_by: "charlie",
          status: AssessmentStatus.IN_PROGRESS,
        }),
        // dave has 1 open
        makeAssessment({
          id: "d1",
          created_by: "dave",
          status: AssessmentStatus.IN_PROGRESS,
        }),
        // null created_by must be skipped
        makeAssessment({
          id: "n1",
          created_by: null,
          status: AssessmentStatus.IN_PROGRESS,
        }),
      ]),
    ];

    const { topOwners, ownerOverflow } = computeMetrics(groups, NOW);
    expect(topOwners.map((o) => o.owner)).toEqual(["alice", "bob", "charlie"]);
    expect(topOwners[0]).toEqual({
      owner: "alice",
      openCount: 3,
      staleCount: 1,
    });
    expect(ownerOverflow).toBe(1);
  });
});
