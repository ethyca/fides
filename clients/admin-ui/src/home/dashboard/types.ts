export type Severity = "error" | "warning" | "info";

export interface SummaryData {
  score: number;
  trend: number;
  dsrsPending: number;
  dsrsOverdue: number;
  systemsCount: number;
  violations: number;
}

export interface AlertAction {
  label: string;
  href: string;
}

export interface AlertData {
  message: string;
  count: number;
  actions: AlertAction[];
}

export interface GovernanceDimension {
  subject: string;
  value: number;
  previous?: number;
  status: "success" | "warning" | "error";
}

export interface GovernanceData {
  score: number;
  trend: number;
  dimensions: GovernanceDimension[];
}

export interface ActionItem {
  id: string;
  title: string;
  severity: Severity;
  category: string;
  subject?: string;
  requestType?: string;
  daysRemaining?: number;
  submitted?: string;
  status?: string;
}

export interface ActionTab {
  key: string;
  label: string;
  count: number;
  items: ActionItem[];
}

export interface SparklineCardData {
  title: string;
  value: number;
  unit: string;
  trend: string;
  trendDirection: "up" | "down";
  data: number[];
}

export interface CoverageBreakdownItem {
  label: string;
  value: number;
  color: string;
}

export interface InfraMonitor {
  name: string;
  systems: number;
  classified: number;
}

export interface SystemCoverageData {
  percent: number;
  total: number;
  breakdown: CoverageBreakdownItem[];
  monitors: InfraMonitor[];
  dataStores: { total: number; approved: number; pending: number };
}

export interface SlaBar {
  label: string;
  segments: CoverageBreakdownItem[];
}

export interface DsrStatusData {
  active: number;
  breakdown: CoverageBreakdownItem[];
  slaBars: SlaBar[];
  slaLegend: CoverageBreakdownItem[];
}
