/**
 * Drop-in GraphQL replacements for the dashboard RTK Query hooks (Apollo).
 *
 * The five static read-only cards share one combined `DashboardOverview`
 * query. Apollo deduplicates concurrent `useQuery(DashboardOverviewDocument)`
 * calls with identical variables into a single network request, so all five
 * hooks below issue exactly one POST.
 *
 * `agentBriefing` is a separate query because the LLM-backed briefing is
 * slow and should not block the rest of the dashboard from painting.
 *
 * `priorityActions` and `activityFeed` keep their own per-card queries --
 * their interactive variables (dimension filter, infinite-scroll pagination)
 * make them poor combined-query candidates.
 *
 * Each hook keeps the exact name, call signature, and return shape of its
 * counterpart in ~/features/dashboard/dashboard.slice and maps the
 * camelCase GraphQL response back onto the existing snake_case
 * ~/features/dashboard/types interfaces. Cards change by one import line.
 */
import { useQuery } from "@apollo/client";
import { useMemo } from "react";

import {
  DashboardActivityFeedDocument,
  DashboardAgentBriefingDocument,
  DashboardOverviewDocument,
  DashboardPriorityActionsDocument,
  TrendPeriod as GqlTrendPeriod,
} from "~/__generated__/graphql/graphql";
import type {
  ActivityFeedResponse,
  AgentBriefingResponse,
  AstralisResponse,
  PostureResponse,
  PriorityAction,
  PrivacyRequestsResponse,
  SystemCoverageResponse,
  TrendsResponse,
} from "~/features/dashboard/types";
import {
  ActionSeverity,
  ActionType,
  DiffDirection,
  PostureBand,
  TrendPeriod,
} from "~/features/dashboard/types";

const TREND_PERIOD_TO_GQL: Record<TrendPeriod, GqlTrendPeriod> = {
  [TrendPeriod.THIRTY_DAYS]: GqlTrendPeriod.ThirtyDays,
  [TrendPeriod.SIXTY_DAYS]: GqlTrendPeriod.SixtyDays,
  [TrendPeriod.NINETY_DAYS]: GqlTrendPeriod.NinetyDays,
};

const useDashboardOverview = (period: TrendPeriod = TrendPeriod.THIRTY_DAYS) =>
  useQuery(DashboardOverviewDocument, {
    variables: { trendPeriod: TREND_PERIOD_TO_GQL[period] },
  });

export const useGetAgentBriefingQuery = () => {
  const { data, loading } = useQuery(DashboardAgentBriefingDocument);
  const briefing = data?.agentBriefing;
  const mapped = useMemo<AgentBriefingResponse | undefined>(
    () =>
      briefing
        ? {
            briefing: briefing.briefing,
            quick_actions: briefing.quickActions.map((qa) => ({
              label: qa.label,
              action_type: qa.actionType as unknown as ActionType,
              action_data: qa.actionData,
              severity: qa.severity as unknown as ActionSeverity,
            })),
          }
        : undefined,
    [briefing],
  );
  return { data: mapped, isLoading: loading };
};

export const useGetDashboardPostureQuery = () => {
  const { data, loading } = useDashboardOverview();
  const p = data?.posture;
  const mapped = useMemo<PostureResponse | undefined>(
    () =>
      p
        ? {
            score: p.score,
            band: p.band as unknown as PostureBand,
            diff_percent: p.diffPercent,
            diff_direction: p.diffDirection as unknown as DiffDirection,
            agent_annotation: p.agentAnnotation,
            dimensions: p.dimensions.map((d) => ({
              dimension: d.dimension,
              label: d.label,
              weight: d.weight,
              score: d.score,
              band: d.band as unknown as PostureBand,
            })),
          }
        : undefined,
    [p],
  );
  return { data: mapped, isLoading: loading && !p };
};

export const useGetSystemCoverageQuery = () => {
  const { data, loading } = useDashboardOverview();
  const c = data?.systemCoverage;
  const mapped = useMemo<SystemCoverageResponse | undefined>(
    () =>
      c
        ? {
            total_systems: c.totalSystems,
            fully_classified: c.fullyClassified,
            partially_classified: c.partiallyClassified,
            unclassified: c.unclassified,
            without_steward: c.withoutSteward,
            coverage_percentage: c.coveragePercentage,
          }
        : undefined,
    [c],
  );
  return { data: mapped, isLoading: loading && !c };
};

export const useGetPrivacyRequestsQuery = () => {
  const { data, loading } = useDashboardOverview();
  const pr = data?.privacyRequests;
  const mapped = useMemo<PrivacyRequestsResponse | undefined>(
    () =>
      pr
        ? {
            active_count: pr.activeCount,
            overdue_count: pr.overdueCount,
            statuses: {
              in_progress: pr.statuses.inProgress,
              pending_action: pr.statuses.pendingAction,
              awaiting_approval: pr.statuses.awaitingApproval,
            },
            sla_health: Object.fromEntries(
              pr.slaHealth.map((b) => [
                b.label,
                {
                  on_track: b.onTrack,
                  approaching: b.approaching,
                  overdue: b.overdue,
                },
              ]),
            ),
          }
        : undefined,
    [pr],
  );
  return { data: mapped, isLoading: loading && !pr };
};

export const useGetAstralisQuery = () => {
  const { data, loading } = useDashboardOverview();
  const a = data?.astralis;
  const mapped = useMemo<AstralisResponse | undefined>(
    () =>
      a
        ? {
            active_conversations: a.activeConversations,
            completed_assessments: a.completedAssessments,
            awaiting_response: a.awaitingResponse,
            risks_identified: a.risksIdentified,
          }
        : undefined,
    [a],
  );
  return { data: mapped, isLoading: loading && !a };
};

export const useGetDashboardTrendsQuery = ({
  period,
}: {
  period: TrendPeriod;
}) => {
  const { data, loading } = useDashboardOverview(period);
  const t = data?.trends;
  const mapped = useMemo<TrendsResponse | undefined>(
    () =>
      t
        ? {
            metrics: Object.fromEntries(
              t.metrics.map((m) => [
                m.key,
                {
                  value: m.value,
                  history: m.history,
                  metadata: m.metadata,
                  diff: m.diff,
                },
              ]),
            ),
          }
        : undefined,
    [t],
  );
  return { data: mapped, isLoading: loading && !t };
};

interface PriorityActionsParams {
  page?: number;
  size?: number;
  dimension?: string | null;
}

interface PriorityActionsResponse {
  items: PriorityAction[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const useGetPriorityActionsQuery = (
  params?: PriorityActionsParams | void,
) => {
  const { dimension, page, size } = params ?? {};
  const { data, loading } = useQuery(DashboardPriorityActionsDocument, {
    variables: {
      page: page ?? 1,
      size: size ?? 25,
      dimension: dimension ?? null,
    },
  });
  const pa = data?.priorityActions;
  const mapped = useMemo<PriorityActionsResponse | undefined>(
    () =>
      pa
        ? {
            items: pa.items.map(
              (i): PriorityAction => ({
                id: i.id,
                type: i.type as unknown as ActionType,
                severity: i.severity as unknown as ActionSeverity,
                title: i.title,
                message: i.message,
                agent_summary: i.agentSummary,
                due_date: i.dueDate ?? null,
                action_data: i.actionData,
                status: i.status as unknown as PriorityAction["status"],
              }),
            ),
            total: pa.total,
            page: pa.page,
            size: pa.size,
            pages: pa.pages,
          }
        : undefined,
    [pa],
  );
  return { data: mapped, isLoading: loading };
};

interface ActivityFeedParams {
  page?: number;
  size?: number;
  actor_type?: "user" | "system";
}

interface ActivityFeedOptions {
  pollingInterval?: number;
  [key: string]: unknown;
}

export const useGetActivityFeedQuery = (
  params?: ActivityFeedParams | void,
  options?: ActivityFeedOptions,
) => {
  const { page, size } = params ?? {};
  const { data, loading } = useQuery(DashboardActivityFeedDocument, {
    variables: { page: page ?? 1, size: size ?? 20 },
    pollInterval: options?.pollingInterval,
    notifyOnNetworkStatusChange: true,
  });
  const af = data?.activityFeed;
  const mapped = useMemo<ActivityFeedResponse | undefined>(
    () =>
      af
        ? {
            items: af.items.map((i) => ({
              id: `${i.timestamp}__${i.message}`,
              actor_type: i.actorType as unknown as "user" | "system",
              message: i.message,
              timestamp: i.timestamp,
            })),
            total: af.total,
            page: af.page,
            size: af.size,
            pages: af.pages,
          }
        : undefined,
    [af],
  );
  return { data: mapped, isFetching: loading };
};
