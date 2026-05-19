/* eslint-disable */
import * as types from './graphql';
import type { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';

/**
 * Map of all GraphQL operations in the project.
 *
 * This map has several performance disadvantages:
 * 1. It is not tree-shakeable, so it will include all operations in the project.
 * 2. It is not minifiable, so the string of a GraphQL query will be multiple times inside the bundle.
 * 3. It does not support dead code elimination, so it will add unused operations.
 *
 * Therefore it is highly recommended to use the babel or swc plugin for production.
 * Learn more about it here: https://the-guild.dev/graphql/codegen/plugins/presets/preset-client#reducing-bundle-size
 */
type Documents = {
    "query DashboardOverview($trendPeriod: TrendPeriod! = thirty_days) {\n  posture {\n    score\n    band\n    diffPercent\n    diffDirection\n    agentAnnotation\n    dimensions {\n      dimension\n      label\n      weight\n      score\n      band\n    }\n  }\n  trends(period: $trendPeriod) {\n    period\n    metrics {\n      key\n      value\n      history\n      metadata\n      diff\n    }\n  }\n  systemCoverage {\n    totalSystems\n    fullyClassified\n    partiallyClassified\n    unclassified\n    withoutSteward\n    coveragePercentage\n  }\n  privacyRequests {\n    activeCount\n    overdueCount\n    statuses {\n      inProgress\n      pendingAction\n      awaitingApproval\n    }\n    slaHealth {\n      label\n      onTrack\n      approaching\n      overdue\n    }\n  }\n  astralis {\n    activeConversations\n    completedAssessments\n    awaitingResponse\n    risksIdentified\n  }\n  ... @defer(label: \"agentBriefing\") {\n    agentBriefing {\n      briefing\n      quickActions {\n        label\n        actionType\n        severity\n        actionData\n      }\n    }\n  }\n}\n\nquery DashboardPriorityActions($page: Int! = 1, $size: Int! = 25, $dimension: String) {\n  priorityActions(page: $page, size: $size, dimension: $dimension) {\n    items {\n      id\n      type\n      severity\n      title\n      message\n      agentSummary\n      dueDate\n      actionData\n      status\n    }\n    total\n    page\n    size\n    pages\n  }\n}\n\nquery DashboardActivityFeed($page: Int! = 1, $size: Int! = 20) {\n  activityFeed(page: $page, size: $size) {\n    items {\n      actorType\n      message\n      timestamp\n    }\n    total\n    page\n    size\n    pages\n  }\n}": typeof types.DashboardOverviewDocument,
};
const documents: Documents = {
    "query DashboardOverview($trendPeriod: TrendPeriod! = thirty_days) {\n  posture {\n    score\n    band\n    diffPercent\n    diffDirection\n    agentAnnotation\n    dimensions {\n      dimension\n      label\n      weight\n      score\n      band\n    }\n  }\n  trends(period: $trendPeriod) {\n    period\n    metrics {\n      key\n      value\n      history\n      metadata\n      diff\n    }\n  }\n  systemCoverage {\n    totalSystems\n    fullyClassified\n    partiallyClassified\n    unclassified\n    withoutSteward\n    coveragePercentage\n  }\n  privacyRequests {\n    activeCount\n    overdueCount\n    statuses {\n      inProgress\n      pendingAction\n      awaitingApproval\n    }\n    slaHealth {\n      label\n      onTrack\n      approaching\n      overdue\n    }\n  }\n  astralis {\n    activeConversations\n    completedAssessments\n    awaitingResponse\n    risksIdentified\n  }\n  ... @defer(label: \"agentBriefing\") {\n    agentBriefing {\n      briefing\n      quickActions {\n        label\n        actionType\n        severity\n        actionData\n      }\n    }\n  }\n}\n\nquery DashboardPriorityActions($page: Int! = 1, $size: Int! = 25, $dimension: String) {\n  priorityActions(page: $page, size: $size, dimension: $dimension) {\n    items {\n      id\n      type\n      severity\n      title\n      message\n      agentSummary\n      dueDate\n      actionData\n      status\n    }\n    total\n    page\n    size\n    pages\n  }\n}\n\nquery DashboardActivityFeed($page: Int! = 1, $size: Int! = 20) {\n  activityFeed(page: $page, size: $size) {\n    items {\n      actorType\n      message\n      timestamp\n    }\n    total\n    page\n    size\n    pages\n  }\n}": types.DashboardOverviewDocument,
};

/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 *
 *
 * @example
 * ```ts
 * const query = gql(`query GetUser($id: ID!) { user(id: $id) { name } }`);
 * ```
 *
 * The query argument is unknown!
 * Please regenerate the types.
 */
export function gql(source: string): unknown;

/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "query DashboardOverview($trendPeriod: TrendPeriod! = thirty_days) {\n  posture {\n    score\n    band\n    diffPercent\n    diffDirection\n    agentAnnotation\n    dimensions {\n      dimension\n      label\n      weight\n      score\n      band\n    }\n  }\n  trends(period: $trendPeriod) {\n    period\n    metrics {\n      key\n      value\n      history\n      metadata\n      diff\n    }\n  }\n  systemCoverage {\n    totalSystems\n    fullyClassified\n    partiallyClassified\n    unclassified\n    withoutSteward\n    coveragePercentage\n  }\n  privacyRequests {\n    activeCount\n    overdueCount\n    statuses {\n      inProgress\n      pendingAction\n      awaitingApproval\n    }\n    slaHealth {\n      label\n      onTrack\n      approaching\n      overdue\n    }\n  }\n  astralis {\n    activeConversations\n    completedAssessments\n    awaitingResponse\n    risksIdentified\n  }\n  ... @defer(label: \"agentBriefing\") {\n    agentBriefing {\n      briefing\n      quickActions {\n        label\n        actionType\n        severity\n        actionData\n      }\n    }\n  }\n}\n\nquery DashboardPriorityActions($page: Int! = 1, $size: Int! = 25, $dimension: String) {\n  priorityActions(page: $page, size: $size, dimension: $dimension) {\n    items {\n      id\n      type\n      severity\n      title\n      message\n      agentSummary\n      dueDate\n      actionData\n      status\n    }\n    total\n    page\n    size\n    pages\n  }\n}\n\nquery DashboardActivityFeed($page: Int! = 1, $size: Int! = 20) {\n  activityFeed(page: $page, size: $size) {\n    items {\n      actorType\n      message\n      timestamp\n    }\n    total\n    page\n    size\n    pages\n  }\n}"): (typeof documents)["query DashboardOverview($trendPeriod: TrendPeriod! = thirty_days) {\n  posture {\n    score\n    band\n    diffPercent\n    diffDirection\n    agentAnnotation\n    dimensions {\n      dimension\n      label\n      weight\n      score\n      band\n    }\n  }\n  trends(period: $trendPeriod) {\n    period\n    metrics {\n      key\n      value\n      history\n      metadata\n      diff\n    }\n  }\n  systemCoverage {\n    totalSystems\n    fullyClassified\n    partiallyClassified\n    unclassified\n    withoutSteward\n    coveragePercentage\n  }\n  privacyRequests {\n    activeCount\n    overdueCount\n    statuses {\n      inProgress\n      pendingAction\n      awaitingApproval\n    }\n    slaHealth {\n      label\n      onTrack\n      approaching\n      overdue\n    }\n  }\n  astralis {\n    activeConversations\n    completedAssessments\n    awaitingResponse\n    risksIdentified\n  }\n  ... @defer(label: \"agentBriefing\") {\n    agentBriefing {\n      briefing\n      quickActions {\n        label\n        actionType\n        severity\n        actionData\n      }\n    }\n  }\n}\n\nquery DashboardPriorityActions($page: Int! = 1, $size: Int! = 25, $dimension: String) {\n  priorityActions(page: $page, size: $size, dimension: $dimension) {\n    items {\n      id\n      type\n      severity\n      title\n      message\n      agentSummary\n      dueDate\n      actionData\n      status\n    }\n    total\n    page\n    size\n    pages\n  }\n}\n\nquery DashboardActivityFeed($page: Int! = 1, $size: Int! = 20) {\n  activityFeed(page: $page, size: $size) {\n    items {\n      actorType\n      message\n      timestamp\n    }\n    total\n    page\n    size\n    pages\n  }\n}"];

export function gql(source: string) {
  return (documents as any)[source] ?? {};
}

export type DocumentType<TDocumentNode extends DocumentNode<any, any>> = TDocumentNode extends DocumentNode<  infer TType,  any>  ? TType  : never;