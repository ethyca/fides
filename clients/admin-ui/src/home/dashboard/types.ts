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

export interface SummaryBreakdownItem {
  label: string;
  value: number;
  color?: string;
}

export interface SummaryData {
  privacyRequests: {
    total: number;
    totalLabel: string;
    breakdown: SummaryBreakdownItem[];
  };
  systemDetection: {
    total: number;
    totalLabel: string;
    breakdown: SummaryBreakdownItem[];
  };
  dataClassification: {
    total: number;
    totalLabel: string;
    breakdown: SummaryBreakdownItem[];
  };
}

export interface ConsentCategoryData {
  category: string;
  value: number;
  change: number;
  trendData: number[];
}

export interface ConsentCategoriesData {
  categories: ConsentCategoryData[];
  timeRange: string;
}

export interface SystemDataClassificationData {
  systemName: string;
  categories: DataCategoryData[];
}

export interface DataClassificationData {
  systems: SystemDataClassificationData[];
}

export interface DashboardData {
  summary: SummaryData;
  consentCategories: ConsentCategoriesData;
  dataClassification: DataClassificationData;
  helios: HeliosData;
  janus: JanusData;
  lethe: LetheData;
}

