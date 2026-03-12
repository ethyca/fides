export interface ViolationSummary {
  id: string;
  policyName: string;
  controlName: string;
  violationCount: number;
  lastViolation: string;
}

export interface DataConsumer {
  name: string;
  requests: number;
  violations: number;
}

export interface RequestLogEntry {
  id: string;
  timestamp: string;
  consumer: string;
  consumerEmail: string;
  policy: string;
  controlName: string;
  policyDescription: string;
  dataset: string;
  table: string;
  dataUse: string;
  system: string;
  violationReason: string;
  requestContext: string;
}

export interface DailyViolationData {
  day: string;
  violations: number;
}

export interface MonthlyViolationData {
  month: string;
  violations: number;
}

export interface HourlyViolationData {
  label: string;
  violations: number;
}
