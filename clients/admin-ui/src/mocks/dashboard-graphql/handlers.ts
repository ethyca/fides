/* eslint-disable import/no-extraneous-dependencies */
import { addMocksToSchema } from "@graphql-tools/mock";
import { makeExecutableSchema } from "@graphql-tools/schema";
import { graphql } from "graphql";
import { rest } from "msw";

import { dashboardSchemaSDL } from "~/features/dashboard-graphql/schema-string";

/**
 * Schema-driven GraphQL mock used by both PoC FE branches (Apollo + urql).
 *
 * The mock surface is identical across the two variants by design — the only
 * thing the user is comparing is the FE stack, so the data plane stays fixed.
 *
 * Enums and a handful of fields have explicit resolvers; everything else
 * falls back to graphql-tools default mocks (length-3 lists, type-shaped
 * scalars). Good enough to drive the dashboard end-to-end without the BE.
 */
const baseSchema = makeExecutableSchema({ typeDefs: dashboardSchemaSDL });

const mockedSchema = addMocksToSchema({
  schema: baseSchema,
  mocks: {
    DateTime: () => new Date().toISOString(),
    JSON: () => ({}),
    PostureBand: () => "good",
    DiffDirection: () => "up",
    ActionSeverity: () => "medium",
    DashboardActionStatus: () => "pending",
    DashboardActionType: () => "classification_review",
    ActorType: () => "agent",
    TrendPeriod: () => "thirty_days",
    Posture: () => ({
      score: 72,
      diffPercent: 4.1,
      agentAnnotation: "Coverage improved over the last 30 days.",
      dimensions: [
        { dimension: "coverage", label: "Coverage", weight: 0.3, score: 78 },
        {
          dimension: "classification_health",
          label: "Classification Health",
          weight: 0.25,
          score: 65,
        },
        {
          dimension: "dsr_compliance",
          label: "DSR Compliance",
          weight: 0.25,
          score: 80,
        },
        {
          dimension: "consent_alignment",
          label: "Consent Alignment",
          weight: 0.2,
          score: 71,
        },
      ],
    }),
    SystemCoverage: () => ({
      totalSystems: 64,
      fullyClassified: 31,
      partiallyClassified: 18,
      unclassified: 15,
      withoutSteward: 9,
      coveragePercentage: 76.5,
    }),
    PrivacyRequests: () => ({
      activeCount: 12,
      overdueCount: 2,
      statuses: { inProgress: 7, pendingAction: 3, awaitingApproval: 2 },
      slaHealth: [
        { label: "access", onTrack: 5, approaching: 1, overdue: 1 },
        { label: "erasure", onTrack: 3, approaching: 1, overdue: 1 },
      ],
    }),
    Astralis: () => ({
      activeConversations: 4,
      completedAssessments: 11,
      awaitingResponse: 2,
      risksIdentified: 6,
    }),
    AgentBriefing: () => ({
      briefing: "Two privacy requests are overdue and require attention.",
      quickActions: [
        { label: "Review DSRs", actionType: "dsr_action", severity: "high" },
      ],
    }),
    TrendMetric: () => ({
      value: 42,
      history: [30, 33, 35, 38, 40, 42],
      diff: 4,
    }),
    PriorityAction: () => ({
      title: "Review classification proposals",
      message: "3 systems have field-level classifications awaiting approval.",
      agentSummary: "Auto-classified by Helios. Confidence > 0.8.",
    }),
    ActivityFeedItem: () => ({
      message: "Steward assigned to system_42.",
    }),
  },
});

export const dashboardGraphqlHandlers = () => [
  rest.post(/\/graphql$/, async (req, res, ctx) => {
    const body = (await req.json()) as {
      query?: string;
      operationName?: string;
      variables?: Record<string, unknown>;
    };
    if (!body?.query) {
      return res(
        ctx.status(400),
        ctx.json({ errors: [{ message: "no query" }] }),
      );
    }
    const result = await graphql({
      schema: mockedSchema,
      source: body.query,
      operationName: body.operationName,
      variableValues: body.variables,
    });
    return res(ctx.json(result));
  }),
];
