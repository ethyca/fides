/* eslint-disable */
import type { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Date with time (isoformat) */
  DateTime: { input: string; output: string; }
  /** The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf). */
  JSON: { input: Record<string, unknown>; output: Record<string, unknown>; }
};

export enum ActionSeverity {
  Critical = 'critical',
  High = 'high',
  Low = 'low',
  Medium = 'medium'
}

export type ActivityFeedItem = {
  __typename?: 'ActivityFeedItem';
  actorType: ActorType;
  message: Scalars['String']['output'];
  timestamp: Scalars['DateTime']['output'];
};

export type ActivityFeedPage = {
  __typename?: 'ActivityFeedPage';
  items: Array<ActivityFeedItem>;
  page: Scalars['Int']['output'];
  pages: Scalars['Int']['output'];
  size: Scalars['Int']['output'];
  total: Scalars['Int']['output'];
};

export enum ActorType {
  Agent = 'agent',
  User = 'user'
}

export type AgentBriefing = {
  __typename?: 'AgentBriefing';
  briefing: Scalars['String']['output'];
  quickActions: Array<QuickAction>;
};

export type Astralis = {
  __typename?: 'Astralis';
  activeConversations: Scalars['Int']['output'];
  awaitingResponse: Scalars['Int']['output'];
  completedAssessments: Scalars['Int']['output'];
  risksIdentified: Scalars['Int']['output'];
};

export enum DashboardActionStatus {
  Completed = 'completed',
  InProgress = 'in_progress',
  Pending = 'pending'
}

export enum DashboardActionType {
  ClassificationReview = 'classification_review',
  ConsentAnomaly = 'consent_anomaly',
  DsrAction = 'dsr_action',
  PiaUpdate = 'pia_update',
  PolicyViolation = 'policy_violation',
  StewardAssignment = 'steward_assignment',
  SystemReview = 'system_review'
}

export enum DiffDirection {
  Down = 'down',
  Unchanged = 'unchanged',
  Up = 'up'
}

export type Posture = {
  __typename?: 'Posture';
  agentAnnotation: Scalars['String']['output'];
  band: PostureBand;
  diffDirection: DiffDirection;
  diffPercent: Scalars['Float']['output'];
  dimensions: Array<PostureDimension>;
  score: Scalars['Float']['output'];
};

export enum PostureBand {
  AtRisk = 'at_risk',
  Critical = 'critical',
  Excellent = 'excellent',
  Good = 'good'
}

export type PostureDimension = {
  __typename?: 'PostureDimension';
  band: PostureBand;
  dimension: Scalars['String']['output'];
  label: Scalars['String']['output'];
  score: Scalars['Float']['output'];
  weight: Scalars['Float']['output'];
};

export type PriorityAction = {
  __typename?: 'PriorityAction';
  actionData: Scalars['JSON']['output'];
  agentSummary: Scalars['String']['output'];
  dueDate?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  message: Scalars['String']['output'];
  severity: ActionSeverity;
  status: DashboardActionStatus;
  title: Scalars['String']['output'];
  type: DashboardActionType;
};

export type PriorityActionsPage = {
  __typename?: 'PriorityActionsPage';
  items: Array<PriorityAction>;
  page: Scalars['Int']['output'];
  pages: Scalars['Int']['output'];
  size: Scalars['Int']['output'];
  total: Scalars['Int']['output'];
};

export type PrivacyRequestStatuses = {
  __typename?: 'PrivacyRequestStatuses';
  awaitingApproval: Scalars['Int']['output'];
  inProgress: Scalars['Int']['output'];
  pendingAction: Scalars['Int']['output'];
};

export type PrivacyRequests = {
  __typename?: 'PrivacyRequests';
  activeCount: Scalars['Int']['output'];
  overdueCount: Scalars['Int']['output'];
  slaHealth: Array<SlaHealthBucket>;
  statuses: PrivacyRequestStatuses;
};

export type Query = {
  __typename?: 'Query';
  activityFeed: ActivityFeedPage;
  agentBriefing: AgentBriefing;
  astralis: Astralis;
  posture: Posture;
  priorityActions: PriorityActionsPage;
  privacyRequests: PrivacyRequests;
  systemCoverage: SystemCoverage;
  trends: Trends;
};


export type QueryActivityFeedArgs = {
  page?: Scalars['Int']['input'];
  size?: Scalars['Int']['input'];
};


export type QueryPriorityActionsArgs = {
  action?: InputMaybe<DashboardActionType>;
  dimension?: InputMaybe<Scalars['String']['input']>;
  page?: Scalars['Int']['input'];
  size?: Scalars['Int']['input'];
  status?: InputMaybe<DashboardActionStatus>;
};


export type QueryTrendsArgs = {
  period?: TrendPeriod;
};

export type QuickAction = {
  __typename?: 'QuickAction';
  actionData: Scalars['JSON']['output'];
  actionType: DashboardActionType;
  label: Scalars['String']['output'];
  severity: ActionSeverity;
};

export type SlaHealthBucket = {
  __typename?: 'SLAHealthBucket';
  approaching: Scalars['Int']['output'];
  label: Scalars['String']['output'];
  onTrack: Scalars['Int']['output'];
  overdue: Scalars['Int']['output'];
};

export type SystemCoverage = {
  __typename?: 'SystemCoverage';
  coveragePercentage: Scalars['Float']['output'];
  fullyClassified: Scalars['Int']['output'];
  partiallyClassified: Scalars['Int']['output'];
  totalSystems: Scalars['Int']['output'];
  unclassified: Scalars['Int']['output'];
  withoutSteward: Scalars['Int']['output'];
};

export type TrendMetric = {
  __typename?: 'TrendMetric';
  diff: Scalars['Float']['output'];
  history: Array<Scalars['Float']['output']>;
  key: Scalars['String']['output'];
  metadata: Scalars['JSON']['output'];
  value: Scalars['Float']['output'];
};

export enum TrendPeriod {
  NinetyDays = 'ninety_days',
  SixtyDays = 'sixty_days',
  ThirtyDays = 'thirty_days'
}

export type Trends = {
  __typename?: 'Trends';
  metrics: Array<TrendMetric>;
  period: TrendPeriod;
};

export type DashboardPostureQueryVariables = Exact<{ [key: string]: never; }>;


export type DashboardPostureQuery = { __typename?: 'Query', posture: { __typename?: 'Posture', score: number, band: PostureBand, diffPercent: number, diffDirection: DiffDirection, agentAnnotation: string, dimensions: Array<{ __typename?: 'PostureDimension', dimension: string, label: string, weight: number, score: number, band: PostureBand }> } };

export type DashboardTrendsQueryVariables = Exact<{
  period?: TrendPeriod;
}>;


export type DashboardTrendsQuery = { __typename?: 'Query', trends: { __typename?: 'Trends', period: TrendPeriod, metrics: Array<{ __typename?: 'TrendMetric', key: string, value: number, history: Array<number>, metadata: Record<string, unknown>, diff: number }> } };

export type DashboardSystemCoverageQueryVariables = Exact<{ [key: string]: never; }>;


export type DashboardSystemCoverageQuery = { __typename?: 'Query', systemCoverage: { __typename?: 'SystemCoverage', totalSystems: number, fullyClassified: number, partiallyClassified: number, unclassified: number, withoutSteward: number, coveragePercentage: number } };

export type DashboardPrivacyRequestsQueryVariables = Exact<{ [key: string]: never; }>;


export type DashboardPrivacyRequestsQuery = { __typename?: 'Query', privacyRequests: { __typename?: 'PrivacyRequests', activeCount: number, overdueCount: number, statuses: { __typename?: 'PrivacyRequestStatuses', inProgress: number, pendingAction: number, awaitingApproval: number }, slaHealth: Array<{ __typename?: 'SLAHealthBucket', label: string, onTrack: number, approaching: number, overdue: number }> } };

export type DashboardPriorityActionsQueryVariables = Exact<{
  page?: Scalars['Int']['input'];
  size?: Scalars['Int']['input'];
  dimension?: InputMaybe<Scalars['String']['input']>;
}>;


export type DashboardPriorityActionsQuery = { __typename?: 'Query', priorityActions: { __typename?: 'PriorityActionsPage', total: number, page: number, size: number, pages: number, items: Array<{ __typename?: 'PriorityAction', id: string, type: DashboardActionType, severity: ActionSeverity, title: string, message: string, agentSummary: string, dueDate?: string | null, actionData: Record<string, unknown>, status: DashboardActionStatus }> } };

export type DashboardAstralisQueryVariables = Exact<{ [key: string]: never; }>;


export type DashboardAstralisQuery = { __typename?: 'Query', astralis: { __typename?: 'Astralis', activeConversations: number, completedAssessments: number, awaitingResponse: number, risksIdentified: number } };

export type DashboardAgentBriefingQueryVariables = Exact<{ [key: string]: never; }>;


export type DashboardAgentBriefingQuery = { __typename?: 'Query', agentBriefing: { __typename?: 'AgentBriefing', briefing: string, quickActions: Array<{ __typename?: 'QuickAction', label: string, actionType: DashboardActionType, severity: ActionSeverity, actionData: Record<string, unknown> }> } };

export type DashboardActivityFeedQueryVariables = Exact<{
  page?: Scalars['Int']['input'];
  size?: Scalars['Int']['input'];
}>;


export type DashboardActivityFeedQuery = { __typename?: 'Query', activityFeed: { __typename?: 'ActivityFeedPage', total: number, page: number, size: number, pages: number, items: Array<{ __typename?: 'ActivityFeedItem', actorType: ActorType, message: string, timestamp: string }> } };


export const DashboardPostureDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardPosture"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"posture"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"score"}},{"kind":"Field","name":{"kind":"Name","value":"band"}},{"kind":"Field","name":{"kind":"Name","value":"diffPercent"}},{"kind":"Field","name":{"kind":"Name","value":"diffDirection"}},{"kind":"Field","name":{"kind":"Name","value":"agentAnnotation"}},{"kind":"Field","name":{"kind":"Name","value":"dimensions"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"dimension"}},{"kind":"Field","name":{"kind":"Name","value":"label"}},{"kind":"Field","name":{"kind":"Name","value":"weight"}},{"kind":"Field","name":{"kind":"Name","value":"score"}},{"kind":"Field","name":{"kind":"Name","value":"band"}}]}}]}}]}}]} as unknown as DocumentNode<DashboardPostureQuery, DashboardPostureQueryVariables>;
export const DashboardTrendsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardTrends"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"period"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"TrendPeriod"}}},"defaultValue":{"kind":"EnumValue","value":"thirty_days"}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"trends"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"period"},"value":{"kind":"Variable","name":{"kind":"Name","value":"period"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"period"}},{"kind":"Field","name":{"kind":"Name","value":"metrics"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"key"}},{"kind":"Field","name":{"kind":"Name","value":"value"}},{"kind":"Field","name":{"kind":"Name","value":"history"}},{"kind":"Field","name":{"kind":"Name","value":"metadata"}},{"kind":"Field","name":{"kind":"Name","value":"diff"}}]}}]}}]}}]} as unknown as DocumentNode<DashboardTrendsQuery, DashboardTrendsQueryVariables>;
export const DashboardSystemCoverageDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardSystemCoverage"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"systemCoverage"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"totalSystems"}},{"kind":"Field","name":{"kind":"Name","value":"fullyClassified"}},{"kind":"Field","name":{"kind":"Name","value":"partiallyClassified"}},{"kind":"Field","name":{"kind":"Name","value":"unclassified"}},{"kind":"Field","name":{"kind":"Name","value":"withoutSteward"}},{"kind":"Field","name":{"kind":"Name","value":"coveragePercentage"}}]}}]}}]} as unknown as DocumentNode<DashboardSystemCoverageQuery, DashboardSystemCoverageQueryVariables>;
export const DashboardPrivacyRequestsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardPrivacyRequests"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"privacyRequests"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"activeCount"}},{"kind":"Field","name":{"kind":"Name","value":"overdueCount"}},{"kind":"Field","name":{"kind":"Name","value":"statuses"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"inProgress"}},{"kind":"Field","name":{"kind":"Name","value":"pendingAction"}},{"kind":"Field","name":{"kind":"Name","value":"awaitingApproval"}}]}},{"kind":"Field","name":{"kind":"Name","value":"slaHealth"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"label"}},{"kind":"Field","name":{"kind":"Name","value":"onTrack"}},{"kind":"Field","name":{"kind":"Name","value":"approaching"}},{"kind":"Field","name":{"kind":"Name","value":"overdue"}}]}}]}}]}}]} as unknown as DocumentNode<DashboardPrivacyRequestsQuery, DashboardPrivacyRequestsQueryVariables>;
export const DashboardPriorityActionsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardPriorityActions"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"page"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},"defaultValue":{"kind":"IntValue","value":"1"}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"size"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},"defaultValue":{"kind":"IntValue","value":"25"}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"dimension"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"priorityActions"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"page"},"value":{"kind":"Variable","name":{"kind":"Name","value":"page"}}},{"kind":"Argument","name":{"kind":"Name","value":"size"},"value":{"kind":"Variable","name":{"kind":"Name","value":"size"}}},{"kind":"Argument","name":{"kind":"Name","value":"dimension"},"value":{"kind":"Variable","name":{"kind":"Name","value":"dimension"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"type"}},{"kind":"Field","name":{"kind":"Name","value":"severity"}},{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"agentSummary"}},{"kind":"Field","name":{"kind":"Name","value":"dueDate"}},{"kind":"Field","name":{"kind":"Name","value":"actionData"}},{"kind":"Field","name":{"kind":"Name","value":"status"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"size"}},{"kind":"Field","name":{"kind":"Name","value":"pages"}}]}}]}}]} as unknown as DocumentNode<DashboardPriorityActionsQuery, DashboardPriorityActionsQueryVariables>;
export const DashboardAstralisDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardAstralis"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"astralis"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"activeConversations"}},{"kind":"Field","name":{"kind":"Name","value":"completedAssessments"}},{"kind":"Field","name":{"kind":"Name","value":"awaitingResponse"}},{"kind":"Field","name":{"kind":"Name","value":"risksIdentified"}}]}}]}}]} as unknown as DocumentNode<DashboardAstralisQuery, DashboardAstralisQueryVariables>;
export const DashboardAgentBriefingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardAgentBriefing"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"agentBriefing"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"briefing"}},{"kind":"Field","name":{"kind":"Name","value":"quickActions"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"label"}},{"kind":"Field","name":{"kind":"Name","value":"actionType"}},{"kind":"Field","name":{"kind":"Name","value":"severity"}},{"kind":"Field","name":{"kind":"Name","value":"actionData"}}]}}]}}]}}]} as unknown as DocumentNode<DashboardAgentBriefingQuery, DashboardAgentBriefingQueryVariables>;
export const DashboardActivityFeedDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"DashboardActivityFeed"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"page"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},"defaultValue":{"kind":"IntValue","value":"1"}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"size"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}},"defaultValue":{"kind":"IntValue","value":"20"}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"activityFeed"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"page"},"value":{"kind":"Variable","name":{"kind":"Name","value":"page"}}},{"kind":"Argument","name":{"kind":"Name","value":"size"},"value":{"kind":"Variable","name":{"kind":"Name","value":"size"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"actorType"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"timestamp"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"size"}},{"kind":"Field","name":{"kind":"Name","value":"pages"}}]}}]}}]} as unknown as DocumentNode<DashboardActivityFeedQuery, DashboardActivityFeedQueryVariables>;