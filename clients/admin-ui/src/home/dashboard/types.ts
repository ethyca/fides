/**
 * Types for dashboard data structures
 */

export interface FieldStatusData {
  name: string;
  value: number;
  color: string;
}

export interface ClassificationActivityDataPoint {
  date: string;
  discovered: number;
  reviewed: number;
  approved: number;
}

export interface DataCategoryData {
  name: string;
  value: number;
  fill: string;
}

export interface ConsentRateDataPoint {
  date: string;
  optIn: number;
  optOut: number;
}

export interface HeliosData {
  discoveredFields: FieldStatusData[];
  classificationActivity: ClassificationActivityDataPoint[];
  dataCategories: DataCategoryData[];
}

export interface JanusData {
  consentRates: ConsentRateDataPoint[];
}

export interface LetheData {
  privacyRequestsNeedingApproval: number;
  pendingManualTasks: number;
}

export interface DashboardData {
  helios: HeliosData;
  janus: JanusData;
  lethe: LetheData;
}

