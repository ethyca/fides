import { StackedBarChartProps } from "fidesui";
import type { ReactNode } from "react";

import { pluralize } from "~/features/common/utils";
import { ActionType } from "~/types/api/models/ActionType";
import { PrivacyRequestsResponse } from "~/types/api/models/PrivacyRequestsResponse";

import {
  ProgressCardBadge,
  ProgressCardProps,
} from "../../data-discovery-and-detection/action-center/ProgressCard/ProgressCard";

/**
 * The three SLA buckets the widget row renders — one widget per bucket.
 * Ordering is meaningful: left-to-right goes from lowest urgency
 * (On track) to highest urgency (Overdue), matching the compliance
 * lead's scanning order.
 */
export type SlaBucket = "on_track" | "approaching" | "overdue";

export const SLA_BUCKET_ORDER: SlaBucket[] = [
  "on_track",
  "approaching",
  "overdue",
];

/** Human-readable title for each bucket's widget. */
export const SLA_BUCKET_LABEL: Record<SlaBucket, string> = {
  on_track: "On track",
  approaching: "Approaching",
  overdue: "Overdue",
};

/**
 * Short inline description that appears on the card and in the hover
 * tooltip on the bucket title. Mirrors the Helios/Action Center pattern
 * of exposing what a number represents on hover rather than in persistent
 * chrome.
 */
export const SLA_BUCKET_DESCRIPTION: Record<SlaBucket, string> = {
  on_track:
    "Active requests whose SLA deadline is comfortably in the future — more than the approaching window away.",
  approaching:
    "Active requests close to their SLA deadline. The approaching window is derived per policy from execution_timeframe (a 30-day policy flags within 2 days; a 90-day policy flags within 6 days).",
  overdue:
    "Active requests already past their SLA deadline. Immediate action required — these expose the organization to regulatory risk under GDPR Article 12, CCPA, and most US state privacy laws.",
};

/**
 * The PrivacyRequestStatus values that can appear in any of the three
 * SLA buckets. All three buckets cover the same active statuses — they
 * differ only by how close each request's due_date is to now. Surfaced
 * in the widget title's hover tooltip so the compliance lead can see
 * the data model at a glance.
 */
export const SLA_BUCKET_ACTIVE_STATUSES: ReadonlyArray<{
  status: string;
  note?: string;
}> = [
  { status: "in_processing" },
  { status: "pending", note: "awaiting approval" },
  { status: "approved" },
  { status: "paused" },
  { status: "requires_input" },
  { status: "requires_manual_finalization" },
  { status: "pending_external", note: "e.g. Jira-backed review" },
] as const;

/**
 * Build the content of the Ant Tooltip that wraps each SLA bucket
 * widget's title. Explains the underlying data model — which statuses
 * roll up into this bucket and how the SLA bucketing rule works — so
 * the compliance lead doesn't have to dig through docs to interpret
 * the number.
 */
export const buildBucketTitleTooltip = (bucket: SlaBucket): ReactNode => {
  const ruleByBucket: Record<SlaBucket, string> = {
    on_track: "due_date ≥ now + approaching window",
    approaching:
      "due_date < now + approaching window (per-policy, derived from execution_timeframe)",
    overdue: "due_date < now",
  };

  return (
    <div className="space-y-2 text-xs">
      <div className="font-semibold">{SLA_BUCKET_LABEL[bucket]}</div>
      <div className="text-xs">{SLA_BUCKET_DESCRIPTION[bucket]}</div>
      <div className="pt-1">
        <div className="mb-1 font-semibold">
          PrivacyRequestStatus values included
        </div>
        <ul className="m-0 list-disc pl-4">
          {SLA_BUCKET_ACTIVE_STATUSES.map(({ status, note }) => (
            <li key={status}>
              <code className="font-mono">{status}</code>
              {note ? (
                <span className="text-[10px] opacity-80"> ({note})</span>
              ) : null}
            </li>
          ))}
        </ul>
      </div>
      <div className="pt-1">
        <div className="mb-1 font-semibold">SLA rule</div>
        <div className="font-mono text-[10px]">{ruleByBucket[bucket]}</div>
      </div>
      <div className="pt-1 text-[10px] opacity-80">
        Statuses <code className="font-mono">complete</code>,{" "}
        <code className="font-mono">error</code>,{" "}
        <code className="font-mono">canceled</code>, and pre-workflow states
        are excluded from all SLA buckets.
      </div>
    </div>
  );
};

/**
 * Stable left-to-right display order for the four action types as stacked
 * bar segments and bottom badges. Access leads because it's the most
 * common request type in practice.
 */
export const ACTION_TYPE_ORDER: ActionType[] = [
  ActionType.ACCESS,
  ActionType.ERASURE,
  ActionType.CONSENT,
  ActionType.UPDATE,
];

/** Human-readable title for each action type. */
export const ACTION_TYPE_LABEL: Record<ActionType, string> = {
  [ActionType.ACCESS]: "Access",
  [ActionType.ERASURE]: "Erasure",
  [ActionType.CONSENT]: "Consent",
  [ActionType.UPDATE]: "Update",
};

/**
 * Stacked-bar colors for each action type. Values are either Ant theme
 * tokens (resolved through the global `token` object at render time) or
 * raw CSS color strings; `StackedBarChart` falls back to the raw value
 * when a token lookup returns undefined.
 *
 * Palette borrows from the Helios Action Center widgets so the Request
 * Manager insights feel like part of the same family:
 *   - Access  → colorSuccess (Helios "Approved" green)
 *   - Erasure → colorWarning (Helios "Classified" gold)
 *   - Update  → colorError (new; Action Center only has 3 semantic
 *                segments, so a 4th color is needed for Update)
 *
 * Consent uses the Fides palette's `bg-info` (`#a5d6f3`) — the designated
 * light blue — directly as a hex. There is no corresponding Ant token in
 * the Fides theme; `colorPrimary` and `colorInfo` are both overridden to
 * Minos (`#2b2e35`), which renders near-black, and `colorPrimaryBg` is a
 * pale neutral indistinguishable from the empty-bar segment. See
 * `clients/fidesui/src/palette/palette.module.scss` for the full palette.
 */
export const ACTION_TYPE_COLOR: Record<ActionType, string> = {
  [ActionType.ACCESS]: "colorSuccess",
  [ActionType.ERASURE]: "colorWarning",
  [ActionType.CONSENT]: "#a5d6f3",
  [ActionType.UPDATE]: "colorError",
};

/**
 * Ant Badge status color (success / warning / error / default) used as
 * the dot marker next to the bucket name and in certain secondary UI.
 * Aligns with the stacked-bar color for each SLA widget but complements
 * — not duplicates — the per-action-type colors inside the bar.
 */
export const SLA_BUCKET_BADGE_STATUS: Record<
  SlaBucket,
  "success" | "warning" | "error"
> = {
  on_track: "success",
  approaching: "warning",
  overdue: "error",
};

/**
 * Key the backend uses for an action type in the `sla_health` dict.
 * The API returns Title-cased keys ("Access", "Erasure", ...), so
 * normalize to that form.
 */
export const slaHealthKeyForActionType = (actionType: ActionType): string =>
  actionType.charAt(0).toUpperCase() + actionType.slice(1);

/**
 * Pivot the backend's action-type-keyed `sla_health` response into a
 * bucket-keyed structure the widgets render from.
 *
 *   input  : { Access: { on_track, approaching, overdue, total }, ... }
 *   output : { on_track: { Access: N, Erasure: N, ... }, ... }
 */
export const pivotSlaHealthByBucket = (
  data: PrivacyRequestsResponse | undefined,
): Record<SlaBucket, Record<ActionType, number>> => {
  const result: Record<SlaBucket, Record<ActionType, number>> = {
    on_track: {
      [ActionType.ACCESS]: 0,
      [ActionType.ERASURE]: 0,
      [ActionType.CONSENT]: 0,
      [ActionType.UPDATE]: 0,
    },
    approaching: {
      [ActionType.ACCESS]: 0,
      [ActionType.ERASURE]: 0,
      [ActionType.CONSENT]: 0,
      [ActionType.UPDATE]: 0,
    },
    overdue: {
      [ActionType.ACCESS]: 0,
      [ActionType.ERASURE]: 0,
      [ActionType.CONSENT]: 0,
      [ActionType.UPDATE]: 0,
    },
  };

  if (!data?.sla_health) {
    return result;
  }

  for (const actionType of ACTION_TYPE_ORDER) {
    const key = slaHealthKeyForActionType(actionType);
    const bucketData = data.sla_health[key];
    if (!bucketData) {
      continue;
    }
    result.on_track[actionType] = bucketData.on_track ?? 0;
    result.approaching[actionType] = bucketData.approaching ?? 0;
    result.overdue[actionType] = bucketData.overdue ?? 0;
  }

  return result;
};

/**
 * Bar-chart segments for one bucket widget. One segment per action type,
 * colored via `ACTION_TYPE_COLOR`, plus a trailing `empty` segment so the
 * bar keeps its full width when every action type is zero (matches
 * Action Center visual treatment).
 */
const ACTION_TYPE_BAR_CHART_SEGMENTS: StackedBarChartProps["segments"] = [
  { key: ActionType.ACCESS, color: ACTION_TYPE_COLOR[ActionType.ACCESS], label: ACTION_TYPE_LABEL[ActionType.ACCESS] },
  { key: ActionType.ERASURE, color: ACTION_TYPE_COLOR[ActionType.ERASURE], label: ACTION_TYPE_LABEL[ActionType.ERASURE] },
  { key: ActionType.CONSENT, color: ACTION_TYPE_COLOR[ActionType.CONSENT], label: ACTION_TYPE_LABEL[ActionType.CONSENT] },
  { key: ActionType.UPDATE, color: ACTION_TYPE_COLOR[ActionType.UPDATE], label: ACTION_TYPE_LABEL[ActionType.UPDATE] },
  { key: "empty", color: "colorPrimaryBg", label: "" },
] as const;

/**
 * Build ProgressCardProps for one SLA bucket widget (On track /
 * Approaching / Overdue). The stacked bar and bottom badges both
 * break the bucket's total down by DSR action type.
 */
export const buildBucketProgressProps = ({
  bucket,
  counts,
  lastUpdated,
}: {
  bucket: SlaBucket;
  counts: Record<ActionType, number>;
  lastUpdated?: string;
}): ProgressCardProps => {
  const total = ACTION_TYPE_ORDER.reduce((sum, at) => sum + (counts[at] ?? 0), 0);

  // Bar chart segment data — one per action type, plus `empty` when the
  // bucket has no requests so the bar still renders at full width.
  const progress: Record<string, number> = {
    empty: total === 0 ? 1 : 0,
  };
  for (const actionType of ACTION_TYPE_ORDER) {
    progress[actionType] = counts[actionType] ?? 0;
  }

  const badges: ProgressCardBadge[] = ACTION_TYPE_ORDER.map((actionType) => ({
    // No "error" badge here — the semantic urgency is conveyed by the
    // card's bucket framing (the Overdue card IS the urgent one), not by
    // repeating red on individual request-type counts.
    status: "default",
    label: ACTION_TYPE_LABEL[actionType].toLowerCase(),
    count: counts[actionType] ?? 0,
  }));

  return {
    title: SLA_BUCKET_LABEL[bucket],
    // Subtitle appears after "resources need review across …" — we've
    // overridden that line via `progressSummary`, so this is mostly used
    // in the ellipsis tooltip on the title.
    subtitle: `${total} ${pluralize(total, "request", "requests")}`,
    progress: {
      label: SLA_BUCKET_LABEL[bucket],
      numerator: total,
      denominator: total,
    },
    primaryStatValue: total,
    // Short sentence on the card itself. Longer explanation lives in the
    // hover tooltip (driven by `numericStats.label`).
    progressSummary:
      total === 0
        ? "No active requests"
        : `${pluralize(total, "request", "requests")} in this bucket`,
    barChartProps: {
      data: { progress },
      segments: ACTION_TYPE_BAR_CHART_SEGMENTS,
    },
    badges,
    // Hover tooltip on the primary statistic — shows the bucket's
    // description + per-action-type breakdown (Helios pattern).
    numericStats: {
      label: SLA_BUCKET_DESCRIPTION[bucket],
      data: ACTION_TYPE_ORDER.map((actionType) => ({
        label: ACTION_TYPE_LABEL[actionType],
        count: counts[actionType] ?? 0,
      })),
    },
    // Hover tooltip on the bottom badge row — same breakdown expressed
    // as percentage share so viewers can compare action-type mix across
    // buckets at a glance (e.g. "Overdue is 60% Access vs. On-track 40%").
    percentageStats: {
      label: `Share by DSR policy (${SLA_BUCKET_LABEL[bucket]})`,
      data:
        total > 0
          ? ACTION_TYPE_ORDER.map((actionType) => ({
              label: ACTION_TYPE_LABEL[actionType],
              value: Math.round(((counts[actionType] ?? 0) / total) * 100),
            }))
          : [],
    },
    // Hover tooltip on the widget title — surfaces the underlying data
    // model (status mapping + SLA bucketing rule) without taking up
    // persistent UI space.
    titleTooltip: buildBucketTitleTooltip(bucket),
    lastUpdated,
  };
};
