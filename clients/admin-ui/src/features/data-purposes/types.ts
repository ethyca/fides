export interface DataPurpose {
  id: string;
  name: string;
  key: string;
  description: string;
  data_use: string;
  data_categories: string[];
  data_subjects: string[];
  legal_basis: string;
  legal_basis_is_flexible: boolean;
  retention_period_days: number | null;
  special_category_legal_basis: string | null;
  features: string[];
  sub_types: string[];
  updated_at: string;
}

export interface PurposeSystemAssignment {
  system_id: string;
  system_name: string;
  system_type: string;
  assigned: boolean;
}

export interface PurposeCoverage {
  systems: { assigned: number; total: number };
  datasets: { assigned: number; total: number };
  tables: { assigned: number; total: number };
  fields: { assigned: number; total: number };
}

export interface PurposeDatasetAssignment {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
  collection_count: number;
}

export interface AvailableSystem {
  system_id: string;
  system_name: string;
  system_type: string;
}

export interface AvailableDataset {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
}

export interface PurposeSummary {
  id: string;
  name: string;
  system_count: number;
  dataset_count: number;
  badge_count: number;
}
