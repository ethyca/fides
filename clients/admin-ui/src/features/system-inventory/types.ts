export enum HealthStatus {
  HEALTHY = "healthy",
  ISSUES = "issues",
}

export enum SystemCapability {
  DSAR = "DSARs",
  MONITORING = "Monitoring",
  CONSENT = "Consent",
  INTEGRATIONS = "Integrations",
  CLASSIFICATION = "Classification",
}

export interface GovernanceDimension {
  label: string;
  score: number;
  color: string;
}

export interface GovernanceHealthData {
  score: number;
  dimensions: GovernanceDimension[];
  annotationAvg: number;
  systemsWithPurposes: number;
  systemsWithStewards: number;
  totalIssues: number;
  healthBreakdown: {
    healthy: number;
    issues: number;
  };
  annotationTrend: number[];
  stewardTrend: number[];
  purposeTrend: number[];
}

export interface SystemQuickAction {
  label: string;
  href: string;
}

export interface GovernanceIssue {
  title: string;
  severity: "error" | "warning";
  resolveHref: string;
}

export interface MockSteward {
  initials: string;
  name: string;
}

export interface MockPurpose {
  name: string;
  color: string;
}

export interface MockIntegration {
  name: string;
  type: string;
  accessLevel: string;
  status: "active" | "disabled" | "failed" | "untested";
  lastTested: string | null;
  enabledActions: string[];
}

export interface MockMonitor {
  name: string;
  frequency: string;
  status: "completed" | "processing" | "failed";
  lastRun: string;
  resourceCount: number;
}

export interface MockRelationship {
  systemName: string;
  systemKey: string;
  role: "producer" | "consumer";
  declaredUse: string;
  authorizedUses: string[];
  hasViolation: boolean;
  violationReason?: string;
}

export interface MockClassification {
  approved: number;
  pending: number;
  unreviewed: number;
  categories: MockClassificationCategory[];
}

export interface MockClassificationCategory {
  name: string;
  fieldCount: number;
  approvedPercent: number;
}

export interface MockDataset {
  name: string;
  key: string;
  collectionCount: number;
  fieldCount: number;
  createdAt: string;
}

export interface MockPrivacyRequests {
  open: number;
  closed: number;
  avgAccessDays: number;
  avgErasureDays: number;
  dsarEnabled: boolean;
}

export interface MockHistoryEntry {
  timestamp: string;
  action: string;
  user: string;
  detail: string;
}

export interface MockSystem {
  fides_key: string;
  name: string;
  system_type: string;
  description: string;
  department: string;
  responsibility: "Controller" | "Processor" | "Sub-Processor";
  roles: Array<"producer" | "consumer">;
  purposes: MockPurpose[];
  annotation_percent: number;
  health: HealthStatus;
  issues: GovernanceIssue[];
  issue_count: number;
  stewards: MockSteward[];
  group: string | null;
  logoDomain: string | null;
  agentBriefing?: string;
  // Detail page data
  integrations: MockIntegration[];
  monitors: MockMonitor[];
  relationships: MockRelationship[];
  classification: MockClassification;
  datasets: MockDataset[];
  privacyRequests: MockPrivacyRequests;
  history: MockHistoryEntry[];
}

export interface SystemInventoryStats {
  total: number;
  violations: number;
  issues: number;
  healthy: number;
}
