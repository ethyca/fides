/**
 * Drop-in GraphQL replacements for the dashboard RTK Query hooks (Apollo).
 *
 * Each hook keeps the exact name, call signature, and return shape of its
 * counterpart in ~/features/dashboard/dashboard.slice, and maps the
 * camelCase GraphQL response back onto the existing snake_case
 * ~/features/dashboard/types interfaces. That keeps every card component
 * unchanged except for its import path.
 *
 * Per-card queries (not one combined query) on purpose: preserves
 * independent auth failure and progressive per-card loading, matching the
 * REST behaviour. dashboard.slice.ts is intentionally left in place
 * (mutations stay on RTK; other consumers/tests may import it).
 */
import { useQuery } from "@apollo/client";

import {
  DashboardActivityFeedDocument,
  DashboardAgentBriefingDocument,
  DashboardAstralisDocument,
  DashboardPostureDocument,
  DashboardPriorityActionsDocument,
  DashboardPrivacyRequestsDocument,
  DashboardSystemCoverageDocument,
  DashboardTrendsDocument,
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

// REST TrendPeriod values ("30d") differ from the GraphQL enum names
// ("thirty_days"); the rest of the enums share the same string values.
const TREND_PERIOD_TO_GQL: Record<TrendPeriod, GqlTrendPeriod> = {
  [TrendPeriod.THIRTY_DAYS]: GqlTrendPeriod.ThirtyDays,
  [TrendPeriod.SIXTY_DAYS]: GqlTrendPeriod.SixtyDays,
  [TrendPeriod.NINETY_DAYS]: GqlTrendPeriod.NinetyDays,
};

export const useGetAgentBriefingQuery = () => {
  const { data, loading } = useQuery(DashboardAgentBriefingDocument);
  const briefing = data?.agentBriefing;
  const mapped: AgentBriefingResponse | undefined = briefing
    ? {
        briefing: briefing.briefing,
        quick_actions: briefing.quickActions.map((qa) => ({
          label: qa.label,
          action_type: qa.actionType as unknown as ActionType,
          action_data: qa.actionData,
          severity: qa.severity as unknown as ActionSeverity,
        })),
      }
    : undefined;
  return { data: mapped, isLoading: loading };
};

export const useGetDashboardPostureQuery = () => {
  const { data, loading } = useQuery(DashboardPostureDocument);
  const p = data?.posture;
  const mapped: PostureResponse | undefined = p
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
    : undefined;
  return { data: mapped, isLoading: loading };
};

export const useGetSystemCoverageQuery = () => {
  const { data, loading } = useQuery(DashboardSystemCoverageDocument);
  const c = data?.systemCoverage;
  const mapped: SystemCoverageResponse | undefined = c
    ? {
        total_systems: c.totalSystems,
        fully_classified: c.fullyClassified,
        partially_classified: c.partiallyClassified,
        unclassified: c.unclassified,
        without_steward: c.withoutSteward,
        coverage_percentage: c.coveragePercentage,
      }
    : undefined;
  return { data: mapped, isLoading: loading };
};

export const useGetPrivacyRequestsQuery = () => {
  const { data, loading } = useQuery(DashboardPrivacyRequestsDocument);
  const pr = data?.privacyRequests;
  const mapped: PrivacyRequestsResponse | undefined = pr
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
    : undefined;
  return { data: mapped, isLoading: loading };
};

export const useGetAstralisQuery = () => {
  const { data, loading } = useQuery(DashboardAstralisDocument);
  const a = data?.astralis;
  const mapped: AstralisResponse | undefined = a
    ? {
        active_conversations: a.activeConversations,
        completed_assessments: a.completedAssessments,
        awaiting_response: a.awaitingResponse,
        risks_identified: a.risksIdentified,
      }
    : undefined;
  return { data: mapped, isLoading: loading };
};

export const useGetDashboardTrendsQuery = ({
  period,
}: {
  period: TrendPeriod;
}) => {
  const { data, loading } = useQuery(DashboardTrendsDocument, {
    variables: { period: TREND_PERIOD_TO_GQL[period] },
  });
  const t = data?.trends;
  const mapped: TrendsResponse | undefined = t
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
    : undefined;
  return { data: mapped, isLoading: loading };
};

interface PriorityActionsParams {
  page?: number;
  size?: number;
  dimension?: string | null;
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
  const mapped: PriorityActionsResponse | undefined = pa
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
    : undefined;
  return { data: mapped, isLoading: loading };
};

interface PriorityActionsResponse {
  items: PriorityAction[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface ActivityFeedParams {
  page?: number;
  size?: number;
  actor_type?: "user" | "system";
}

interface ActivityFeedOptions {
  pollingInterval?: number;
  // Accept (and ignore) the other RTK Query options the call site passes
  // (skipPollingIfUnfocused, refetchOnMountOrArgChange, ...).
  [key: string]: unknown;
}

export const useGetActivityFeedQuery = (
  params?: ActivityFeedParams | void,
  // RTK polling options are accepted for signature parity. Polling maps to
  // Apollo's pollInterval; the rest are no-ops for the PoC.
  options?: ActivityFeedOptions,
) => {
  const { page, size } = params ?? {};
  const { data, loading } = useQuery(DashboardActivityFeedDocument, {
    variables: { page: page ?? 1, size: size ?? 20 },
    pollInterval: options?.pollingInterval,
    notifyOnNetworkStatusChange: true,
  });
  const af = data?.activityFeed;
  const mapped: ActivityFeedResponse | undefined = af
    ? {
        items: af.items.map((i) => ({
          // The GraphQL ActivityFeedItem has no id; synthesise a stable one
          // so the infinite-scroll dedupe keeps working unchanged.
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
    : undefined;
  return { data: mapped, isFetching: loading };
};
